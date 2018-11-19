# Copyright (c) 2016-2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ipaddress
import logging
import six
from collections import defaultdict

from yardstick.common import utils
from yardstick.network_services.libs.ixia_libs.ixnet import ixnet_api
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import Rfc2544ResourceHelper


LOG = logging.getLogger(__name__)

WAIT_AFTER_CFG_LOAD = 10
WAIT_FOR_TRAFFIC = 30
WAIT_PROTOCOLS_STARTED = 420


class IxiaBasicScenario(object):
    def __init__(self, client, context_cfg, ixia_cfg):

        self.client = client
        self.context_cfg = context_cfg
        self.ixia_cfg = ixia_cfg

        self._uplink_vports = None
        self._downlink_vports = None

    def apply_config(self):
        pass

    def create_traffic_model(self, traffic_profile=None):
        # pylint: disable=unused-argument
        vports = self.client.get_vports()
        self._uplink_vports = vports[::2]
        self._downlink_vports = vports[1::2]
        self.client.create_traffic_model(self._uplink_vports,
                                         self._downlink_vports)

    def get_stats(self):
        return self.client.get_statistics()

    def generate_samples(self, resource_helper, ports, duration):
        stats = self.get_stats()

        samples = {}
        # this is not DPDK port num, but this is whatever number we gave
        # when we selected ports and programmed the profile
        for port_num in ports:
            try:
                # reverse lookup port name from port_num so the stats dict is descriptive
                intf = resource_helper.vnfd_helper.find_interface_by_port(port_num)
                port_name = intf['name']
                avg_latency = stats['Store-Forward_Avg_latency_ns'][port_num]
                min_latency = stats['Store-Forward_Min_latency_ns'][port_num]
                max_latency = stats['Store-Forward_Max_latency_ns'][port_num]
                samples[port_name] = {
                    'rx_throughput_kps': float(stats['Rx_Rate_Kbps'][port_num]),
                    'tx_throughput_kps': float(stats['Tx_Rate_Kbps'][port_num]),
                    'rx_throughput_mbps': float(stats['Rx_Rate_Mbps'][port_num]),
                    'tx_throughput_mbps': float(stats['Tx_Rate_Mbps'][port_num]),
                    'in_packets': int(stats['Valid_Frames_Rx'][port_num]),
                    'out_packets': int(stats['Frames_Tx'][port_num]),
                    'RxThroughput': float(stats['Valid_Frames_Rx'][port_num]) / duration,
                    'TxThroughput': float(stats['Frames_Tx'][port_num]) / duration,
                    'Store-Forward_Avg_latency_ns': utils.safe_cast(avg_latency, int, 0),
                    'Store-Forward_Min_latency_ns': utils.safe_cast(min_latency, int, 0),
                    'Store-Forward_Max_latency_ns': utils.safe_cast(max_latency, int, 0)
                }
            except IndexError:
                pass

        return samples

    def run_protocols(self):
        pass

    def stop_protocols(self):
        pass

    def update_tracking_options(self):
        pass

    def get_tc_rfc2544_options(self):
        pass


class IxiaPppoeClientScenario(object):
    def __init__(self, client, context_cfg, ixia_cfg):

        self.client = client

        self._uplink_vports = None
        self._downlink_vports = None

        self._access_topologies = []
        self._core_topologies = []

        self._context_cfg = context_cfg
        self._ixia_cfg = ixia_cfg
        self.protocols = []
        self.device_groups = []

    def apply_config(self):
        vports = self.client.get_vports()
        self._uplink_vports = vports[::2]
        self._downlink_vports = vports[1::2]
        self._fill_ixia_config()
        self._apply_access_network_config()
        self._apply_core_network_config()

    def create_traffic_model(self, traffic_profile):
        endpoints_id_pairs = self._get_endpoints_src_dst_id_pairs(
            traffic_profile.full_profile)
        endpoints_obj_pairs = \
            self._get_endpoints_src_dst_obj_pairs(endpoints_id_pairs)
        uplink_endpoints = endpoints_obj_pairs[::2]
        downlink_endpoints = endpoints_obj_pairs[1::2]
        self.client.create_ipv4_traffic_model(uplink_endpoints,
                                              downlink_endpoints)

    def run_protocols(self):
        LOG.info('PPPoE Scenario - Start Protocols')
        self.client.start_protocols()
        utils.wait_until_true(
            lambda: self.client.is_protocols_running(self.protocols),
            timeout=WAIT_PROTOCOLS_STARTED, sleep=2)

    def stop_protocols(self):
        LOG.info('PPPoE Scenario - Stop Protocols')
        self.client.stop_protocols()

    def _get_intf_addr(self, intf):
        """Retrieve interface IP address and mask

        :param intf: could be the string which represents IP address
        with mask (e.g 192.168.10.2/24) or a dictionary with the host
        name and the port (e.g. {'tg__0': 'xe1'})
        :return: (tuple) pair of ip address and mask
        """
        if isinstance(intf, six.string_types):
            ip, mask = tuple(intf.split('/'))
            return ip, int(mask)

        node_name, intf_name = next(iter(intf.items()))
        node = self._context_cfg["nodes"].get(node_name, {})
        interface = node.get("interfaces", {})[intf_name]
        ip = interface["local_ip"]
        mask = interface["netmask"]
        ipaddr = ipaddress.ip_network(six.text_type('{}/{}'.format(ip, mask)),
                                      strict=False)
        return ip, ipaddr.prefixlen

    @staticmethod
    def _get_endpoints_src_dst_id_pairs(flows_params):
        """Get list of flows src/dst port pairs

        Create list of flows src/dst port pairs based on traffic profile
        flows data. Each uplink/downlink pair in traffic profile represents
        specific flows between the pair of ports.

        Example ('port' key represents port on which flow will be created):

        Input flows data:
        uplink_0:
          ipv4:
            id: 1
            port: xe0
        downlink_0:
          ipv4:
            id: 2
            port: xe1
        uplink_1:
          ipv4:
            id: 3
            port: xe2
        downlink_1:
          ipv4:
            id: 4
            port: xe3

        Result list: ['xe0', 'xe1', 'xe2', 'xe3']

        Result list means that the following flows pairs will be created:
        - uplink 0: port xe0 <-> port xe1
        - downlink 0: port xe1 <-> port xe0
        - uplink 1: port xe2 <-> port xe3
        - downlink 1: port xe3 <-> port xe2

        :param flows_params: ordered dict of traffic profile flows params
        :return: (list) list of flows src/dst ports
        """
        if len(flows_params) % 2:
            raise RuntimeError('Number of uplink/downlink pairs'
                               ' in traffic profile is not equal')
        endpoint_pairs = []
        for flow in flows_params:
            port = flows_params[flow]['ipv4'].get('port')
            if port is None:
                continue
            endpoint_pairs.append(port)
        return endpoint_pairs

    def _get_endpoints_src_dst_obj_pairs(self, endpoints_id_pairs):
        """Create list of uplink/downlink device groups pairs

        Based on traffic profile options, create list of uplink/downlink
        device groups pairs between which flow groups will be created:

        1. In case uplink/downlink flows in traffic profile doesn't have
           specified 'port' key, flows will be created between each device
           group on access port and device group on corresponding core port.
           E.g.:
           Device groups created on access port xe0: dg1, dg2, dg3
           Device groups created on core port xe1: dg4
           Flows will be created between:
           dg1 -> dg4
           dg4 -> dg1
           dg2 -> dg4
           dg4 -> dg2
           dg3 -> dg4
           dg4 -> dg3

        2. In case uplink/downlink flows in traffic profile have specified
           'port' key, flows will be created between device groups on this
           port.
           E.g., for the following traffic profile
           uplink_0:
             port: xe0
           downlink_0:
             port: xe1
           uplink_1:
             port: xe0
           downlink_0:
             port: xe3
           Flows will be created between:
           Port xe0 (dg1) -> Port xe1 (dg1)
           Port xe1 (dg1) -> Port xe0 (dg1)
           Port xe0 (dg2) -> Port xe3 (dg1)
           Port xe3 (dg3) -> Port xe0 (dg1)

        :param endpoints_id_pairs: (list) List of uplink/downlink flows ports
         pairs
        :return: (list) list of uplink/downlink device groups descriptors pairs
        """
        pppoe = self._ixia_cfg['pppoe_client']
        sessions_per_port = pppoe['sessions_per_port']
        sessions_per_svlan = pppoe['sessions_per_svlan']
        svlan_count = int(sessions_per_port / sessions_per_svlan)

        uplink_ports = [p['tg__0'] for p in self._ixia_cfg['flow']['src_ip']]
        downlink_ports = [p['tg__0'] for p in self._ixia_cfg['flow']['dst_ip']]
        uplink_port_topology_map = zip(uplink_ports, self._access_topologies)
        downlink_port_topology_map = zip(downlink_ports, self._core_topologies)

        port_to_dev_group_mapping = {}
        for port, topology in uplink_port_topology_map:
            topology_dgs = self.client.get_topology_device_groups(topology)
            port_to_dev_group_mapping[port] = topology_dgs
        for port, topology in downlink_port_topology_map:
            topology_dgs = self.client.get_topology_device_groups(topology)
            port_to_dev_group_mapping[port] = topology_dgs

        uplink_endpoints = endpoints_id_pairs[::2]
        downlink_endpoints = endpoints_id_pairs[1::2]

        uplink_dev_groups = []
        group_up = [uplink_endpoints[i:i + svlan_count]
                    for i in range(0, len(uplink_endpoints), svlan_count)]

        for group in group_up:
            for i, port in enumerate(group):
                uplink_dev_groups.append(port_to_dev_group_mapping[port][i])

        downlink_dev_groups = []
        for port in downlink_endpoints:
            downlink_dev_groups.append(port_to_dev_group_mapping[port][0])

        endpoint_obj_pairs = []
        [endpoint_obj_pairs.extend([up, down])
         for up, down in zip(uplink_dev_groups, downlink_dev_groups)]

        if not endpoint_obj_pairs:
            for up, down in zip(uplink_ports, downlink_ports):
                uplink_dev_groups = port_to_dev_group_mapping[up]
                downlink_dev_groups = \
                    port_to_dev_group_mapping[down] * len(uplink_dev_groups)
                [endpoint_obj_pairs.extend(list(i))
                 for i in zip(uplink_dev_groups, downlink_dev_groups)]
        return endpoint_obj_pairs

    def _fill_ixia_config(self):
        pppoe = self._ixia_cfg["pppoe_client"]
        ipv4 = self._ixia_cfg["ipv4_client"]

        _ip = [self._get_intf_addr(intf)[0] for intf in pppoe["ip"]]
        self._ixia_cfg["pppoe_client"]["ip"] = _ip

        _ip = [self._get_intf_addr(intf)[0] for intf in ipv4["gateway_ip"]]
        self._ixia_cfg["ipv4_client"]["gateway_ip"] = _ip

        addrs = [self._get_intf_addr(intf) for intf in ipv4["ip"]]
        _ip = [addr[0] for addr in addrs]
        _prefix = [addr[1] for addr in addrs]

        self._ixia_cfg["ipv4_client"]["ip"] = _ip
        self._ixia_cfg["ipv4_client"]["prefix"] = _prefix

    def _apply_access_network_config(self):
        pppoe = self._ixia_cfg["pppoe_client"]
        sessions_per_port = pppoe['sessions_per_port']
        sessions_per_svlan = pppoe['sessions_per_svlan']
        svlan_count = int(sessions_per_port / sessions_per_svlan)

        # add topology per uplink port (access network)
        for access_tp_id, vport in enumerate(self._uplink_vports):
            name = 'Topology access {}'.format(access_tp_id)
            tp = self.client.add_topology(name, vport)
            self._access_topologies.append(tp)
            # add device group per svlan
            for dg_id in range(svlan_count):
                s_vlan_id = int(pppoe['s_vlan']) + dg_id + access_tp_id * svlan_count
                s_vlan = ixnet_api.Vlan(vlan_id=s_vlan_id)
                c_vlan = ixnet_api.Vlan(vlan_id=pppoe['c_vlan'], vlan_id_step=1)
                name = 'SVLAN {}'.format(s_vlan_id)
                dg = self.client.add_device_group(tp, name, sessions_per_svlan)
                self.device_groups.append(dg)
                # add ethernet layer to device group
                ethernet = self.client.add_ethernet(dg, 'Ethernet')
                self.protocols.append(ethernet)
                self.client.add_vlans(ethernet, [s_vlan, c_vlan])
                # add ppp over ethernet
                if 'pap_user' in pppoe:
                    ppp = self.client.add_pppox_client(ethernet, 'pap',
                                                       pppoe['pap_user'],
                                                       pppoe['pap_password'])
                else:
                    ppp = self.client.add_pppox_client(ethernet, 'chap',
                                                       pppoe['chap_user'],
                                                       pppoe['chap_password'])
                self.protocols.append(ppp)

    def _apply_core_network_config(self):
        ipv4 = self._ixia_cfg["ipv4_client"]
        sessions_per_port = ipv4['sessions_per_port']
        sessions_per_vlan = ipv4['sessions_per_vlan']
        vlan_count = int(sessions_per_port / sessions_per_vlan)

        # add topology per downlink port (core network)
        for core_tp_id, vport in enumerate(self._downlink_vports):
            name = 'Topology core {}'.format(core_tp_id)
            tp = self.client.add_topology(name, vport)
            self._core_topologies.append(tp)
            # add device group per vlan
            for dg_id in range(vlan_count):
                name = 'Core port {}'.format(core_tp_id)
                dg = self.client.add_device_group(tp, name, sessions_per_vlan)
                self.device_groups.append(dg)
                # add ethernet layer to device group
                ethernet = self.client.add_ethernet(dg, 'Ethernet')
                self.protocols.append(ethernet)
                if 'vlan' in ipv4:
                    vlan_id = int(ipv4['vlan']) + dg_id + core_tp_id * vlan_count
                    vlan = ixnet_api.Vlan(vlan_id=vlan_id)
                    self.client.add_vlans(ethernet, [vlan])
                # add ipv4 layer
                gw_ip = ipv4['gateway_ip'][core_tp_id]
                # use gw addr to generate ip addr from the same network
                ip_addr = ipaddress.IPv4Address(gw_ip) + 1
                ipv4_obj = self.client.add_ipv4(ethernet, name='ipv4',
                                                addr=ip_addr,
                                                addr_step='0.0.0.1',
                                                prefix=ipv4['prefix'][core_tp_id],
                                                gateway=gw_ip)
                self.protocols.append(ipv4_obj)
                if ipv4.get("bgp"):
                    bgp_peer_obj = self.client.add_bgp(ipv4_obj,
                                                       dut_ip=ipv4["bgp"]["dut_ip"],
                                                       local_as=ipv4["bgp"]["as_number"],
                                                       bgp_type=ipv4["bgp"].get("bgp_type"))
                    self.protocols.append(bgp_peer_obj)

    def update_tracking_options(self):
        priority_map = {
            'raw': 'ipv4Raw0',
            'tos': {'precedence': 'ipv4Precedence0'},
            'dscp': {'defaultPHB': 'ipv4DefaultPhb0',
                     'selectorPHB': 'ipv4ClassSelectorPhb0',
                     'assuredPHB': 'ipv4AssuredForwardingPhb0',
                     'expeditedPHB': 'ipv4ExpeditedForwardingPhb0'}
        }

        prio_trackby_key = 'ipv4Precedence0'

        try:
            priority = list(self._ixia_cfg['priority'])[0]
            if priority == 'raw':
                prio_trackby_key = priority_map[priority]
            elif priority in ['tos', 'dscp']:
                priority_type = list(self._ixia_cfg['priority'][priority])[0]
                prio_trackby_key = priority_map[priority][priority_type]
        except KeyError:
            pass

        tracking_options = ['flowGroup0', 'vlanVlanId0', prio_trackby_key]
        self.client.set_flow_tracking(tracking_options)

    def get_tc_rfc2544_options(self):
        return self._ixia_cfg.get('rfc2544')

    def get_stats(self):
        return self.client.get_pppoe_scenario_statistics()

    @staticmethod
    def _get_flow_vlan_data(stats, flow_id, key):
        if stats.get(flow_id):
            for vlan in stats[flow_id]:
                return stats[flow_id][vlan][key]

    def _get_port_ip_priority_stats(self, stats, flows_id_list, duration):
        result = {}
        prio_flows = [self._get_flow_vlan_data(stats, _flow_id, 'priority')
                      for _flow_id in flows_id_list]
        port_priority_id = []
        [port_priority_id.extend(list(data)) for data in prio_flows]

        for prio_id in set(port_priority_id):
            prio_flows_on_port = \
                len([_flow.get(prio_id) for _flow in prio_flows
                     if _flow.get(prio_id) is not None])
            result[prio_id] = {
                'in_packets': sum([int(i[prio_id]['in_packets'])
                                   for i in prio_flows]),
                'out_packets': sum([int(i[prio_id]['out_packets'])
                                    for i in prio_flows]),
                'tx_throughput_kbps': sum([float(i[prio_id]['tx_throughput_kbps'])
                                           for i in prio_flows]),
                'rx_throughput_kbps': sum([float(i[prio_id]['rx_throughput_kbps'])
                                           for i in prio_flows]),
                'tx_throughput_mbps': sum([float(i[prio_id]['tx_throughput_mbps'])
                                           for i in prio_flows]),
                'rx_throughput_mbps': sum([float(i[prio_id]['rx_throughput_mbps'])
                                           for i in prio_flows]),
                'RxThroughput': sum([int(i[prio_id]['in_packets'])
                                     for i in prio_flows]) / duration,
                'TxThroughput': sum([int(i[prio_id]['out_packets'])
                                     for i in prio_flows]) / duration,
                'Store-Forward_Avg_latency_ns': sum(
                    [int(i[prio_id]['Store-Forward_Avg_latency_ns'])
                     for i in prio_flows]) / prio_flows_on_port,
                'Store-Forward_Max_latency_ns': sum(
                    [int(i[prio_id]['Store-Forward_Max_latency_ns'])
                     for i in prio_flows]) / prio_flows_on_port,
                'Store-Forward_Min_latency_ns': sum(
                    [int(i[prio_id]['Store-Forward_Min_latency_ns'])
                     for i in prio_flows]) / prio_flows_on_port
            }
        return result

    def _update_flow_statistics(self, flow_stats):
        uplink_flows = list(flow_stats)[::2]
        vlan_subs_num = self._ixia_cfg["pppoe_client"]['sessions_per_svlan']
        for _flow in flow_stats:
            _priority = {}
            _vlan = {}
            # Get VLAN data from flow data
            vlan_key = list(flow_stats[_flow])[0]
            vlan_data = flow_stats[_flow].pop(vlan_key)

            for prior_flow_id in vlan_data:
                prio_flow_data = vlan_data[prior_flow_id]
                prio_flow = {
                    'in_packets': int(prio_flow_data['Rx_Frames']),
                    'out_packets': int(prio_flow_data['Tx_Frames']),
                    'tx_throughput_kbps': float(prio_flow_data['Tx_Rate_Kbps']),
                    'rx_throughput_kbps': float(prio_flow_data['Rx_Rate_Kbps']),
                    'tx_throughput_mbps': float(prio_flow_data['Tx_Rate_Mbps']),
                    'rx_throughput_mbps': float(prio_flow_data['Rx_Rate_Mbps']),
                    'Store-Forward_Avg_latency_ns': int(
                        prio_flow_data['Store-Forward_Avg_latency_ns']),
                    'Store-Forward_Max_latency_ns': int(
                        prio_flow_data['Store-Forward_Max_latency_ns']),
                    'Store-Forward_Min_latency_ns': int(
                        prio_flow_data['Store-Forward_Min_latency_ns'])
                }
                if _flow in uplink_flows:
                    prio_flow['avg_sub_tx_throughput_kbps'] = \
                        float(prio_flow_data['Tx_Rate_Kbps']) / vlan_subs_num
                    prio_flow['avg_sub_rx_throughput_kbps'] = \
                        float(prio_flow_data['Rx_Rate_Kbps']) / vlan_subs_num
                    prio_flow['avg_sub_tx_throughput_mbps'] = \
                        float(prio_flow_data['Tx_Rate_Mbps']) / vlan_subs_num
                    prio_flow['avg_sub_rx_throughput_mbps'] = \
                        float(prio_flow_data['Rx_Rate_Mbps']) / vlan_subs_num
                # Update flow statistics with updated flow data
                _priority[prior_flow_id] = prio_flow

            tx_frames = [int(vlan_data[_prio_id]['Tx_Frames'])
                         for _prio_id in vlan_data]
            rx_frames = [int(vlan_data[_prio_id]['Rx_Frames'])
                         for _prio_id in vlan_data]
            tx_rate_kbps = [float(vlan_data[_prio_id]['Tx_Rate_Kbps'])
                            for _prio_id in vlan_data]
            rx_rate_kbps = [float(vlan_data[_prio_id]['Rx_Rate_Kbps'])
                            for _prio_id in vlan_data]
            tx_rate_mbps = [float(vlan_data[_prio_id]['Tx_Rate_Mbps'])
                            for _prio_id in vlan_data]
            rx_rate_mbps = [float(vlan_data[_prio_id]['Rx_Rate_Mbps'])
                            for _prio_id in vlan_data]
            avg_latency = [
                int(vlan_data[_prio_id]['Store-Forward_Avg_latency_ns'])
                for _prio_id in vlan_data]
            max_latency = [
                int(vlan_data[_prio_id]['Store-Forward_Max_latency_ns'])
                for _prio_id in vlan_data]
            min_latency = [
                int(vlan_data[_prio_id]['Store-Forward_Min_latency_ns'])
                for _prio_id in vlan_data]

            _vlan['out_packets'] = sum(tx_frames)
            _vlan['in_packets'] = sum(rx_frames)
            _vlan['tx_throughput_kbps'] = sum(tx_rate_kbps)
            _vlan['rx_throughput_kbps'] = sum(rx_rate_kbps)
            _vlan['tx_throughput_mbps'] = sum(tx_rate_mbps)
            _vlan['rx_throughput_mbps'] = sum(rx_rate_mbps)
            _vlan['Store-Forward_Avg_latency_ns'] = \
                sum(avg_latency) / len(avg_latency)
            _vlan['Store-Forward_Max_latency_ns'] = \
                sum(max_latency) / len(max_latency)
            _vlan['Store-Forward_Min_latency_ns'] = \
                sum(min_latency) / len(min_latency)
            _vlan['priority'] = _priority
            vlan_name = 'VLAN{}'.format(vlan_key)
            flow_stats[_flow].update({vlan_name: _vlan})
        return flow_stats

    def generate_samples(self, resource_helper, ports, duration):

        stats = self.get_stats()
        samples = {}
        ports_stats = stats['port_statistics']
        flows_stats = stats['flow_statistic']
        pppoe_subs_per_port = stats['pppox_client_per_port']

        # Get sorted list of ixia ports names
        ixia_port_names = sorted([data['port_name'] for data in ports_stats])

        # Set 'port_id' key for ports stats items
        for item in ports_stats:
            port_id = item.pop('port_name').split('-')[-1].strip()
            item['port_id'] = int(port_id)

        # Set 'id' key for flows stats items
        for item in flows_stats:
            flow_id = item.pop('Flow_Group').split('-')[1].strip()
            item['id'] = int(flow_id)

        # Set 'port_id' key for pppoe subs per port stats
        for item in pppoe_subs_per_port:
            port_id = item.pop('subs_port').split('-')[-1].strip()
            item['port_id'] = int(port_id)

        # Map traffic flows to ports
        port_flow_map = defaultdict(set)
        for item in flows_stats:
            tx_port = item.pop('Tx_Port')
            tx_port_index = ixia_port_names.index(tx_port)
            port_flow_map[tx_port_index].update([item['id']])

        # Sort ports stats
        ports_stats = sorted(ports_stats, key=lambda k: k['port_id'])

        # Sort flows stats
        flows_stats = sorted(flows_stats, key=lambda k: k['id'])
        flows_id = list(set([flow['id'] for flow in flows_stats]))

        # Collect ip precedence flows under one flow vlan id
        flow_stats = defaultdict(dict)
        for flow in flows_stats:
            flow_id = flow.pop('id')
            vlan_id = flow.pop('VLAN-ID')
            ip_precedence = flow.pop('IP_Priority')
            if flow_stats[flow_id].get(vlan_id):
                flow_stats[flow_id][vlan_id].update({ip_precedence: flow})
            else:
                flow_stats[flow_id].update({vlan_id: {ip_precedence: flow}})

        # Update Flow Statistics
        flow_stats = self._update_flow_statistics(flow_stats)

        uplink_flows = flows_id[::2]
        downlink_flows = flows_id[1::2]
        up_down_flows_pairs = zip(uplink_flows, downlink_flows)

        # this is not DPDK port num, but this is whatever number we gave
        # when we selected ports and programmed the profile
        for port_num in ports:
            try:
                # reverse lookup port name from port_num so the stats dict is descriptive
                intf = resource_helper.vnfd_helper.find_interface_by_port(port_num)
                port_name = intf['name']
                port_id = ports_stats[port_num]['port_id']
                port_subs_stats = \
                    [port_data for port_data in pppoe_subs_per_port
                     if port_data.get('port_id') == port_id]

                _avg_latency = \
                    sum([self._get_flow_vlan_data(
                        flow_stats, flow, 'Store-Forward_Avg_latency_ns')
                        for flow in port_flow_map[port_num]]) / len(port_flow_map[port_num])
                _min_latency = \
                    sum([self._get_flow_vlan_data(
                        flow_stats, flow, 'Store-Forward_Min_latency_ns')
                        for flow in port_flow_map[port_num]]) / len(port_flow_map[port_num])
                _max_latency = \
                    sum([self._get_flow_vlan_data(
                        flow_stats, flow, 'Store-Forward_Max_latency_ns')
                        for flow in port_flow_map[port_num]]) / len(port_flow_map[port_num])

                _port_ip_priority = self._get_port_ip_priority_stats(
                    flow_stats, port_flow_map[port_num], duration)

                # Collect port VLANs data
                _vlans = {}
                for flow in port_flow_map[port_num]:
                    if flow in downlink_flows:
                        # Get uplink port pair for downlink port
                        uplink_flow_id = \
                            [up for (up, down) in up_down_flows_pairs
                             if down == flow][0]
                        # Form VLAN key name
                        _key_name = 'to'.join([
                            list(flow_stats[flow])[0],
                            list(flow_stats[uplink_flow_id])[0]])
                        _vlan_id = list(flow_stats[flow])[0]
                    else:
                        # Form VLAN key name
                        _key_name = list(flow_stats[flow])[0]
                        _vlan_id = list(flow_stats[flow])[0]
                    _vlans.update({_key_name: flow_stats[flow][_vlan_id]})

                samples[port_name] = {
                    'rx_throughput_kps': float(ports_stats[port_num]['Rx_Rate_Kbps']),
                    'tx_throughput_kps': float(ports_stats[port_num]['Tx_Rate_Kbps']),
                    'rx_throughput_mbps': float(ports_stats[port_num]['Rx_Rate_Mbps']),
                    'tx_throughput_mbps': float(ports_stats[port_num]['Tx_Rate_Mbps']),
                    'in_packets': int(ports_stats[port_num]['Valid_Frames_Rx']),
                    'out_packets': int(ports_stats[port_num]['Frames_Tx']),
                    'RxThroughput': float(ports_stats[port_num]['Valid_Frames_Rx']) / duration,
                    'TxThroughput': float(ports_stats[port_num]['Frames_Tx']) / duration,
                    'Store-Forward_Avg_latency_ns': utils.safe_cast(_avg_latency, int, 0),
                    'Store-Forward_Min_latency_ns': utils.safe_cast(_min_latency, int, 0),
                    'Store-Forward_Max_latency_ns': utils.safe_cast(_max_latency, int, 0),
                    'priority': _port_ip_priority,
                    'vlan': _vlans
                }

                if port_subs_stats:
                    samples[port_name].update(
                        {'sessions_up': int(port_subs_stats[0]['Sessions_Up']),
                         'sessions_down': int(port_subs_stats[0]['Sessions_Down']),
                         'sessions_not_started': int(port_subs_stats[0]['Sessions_Not_Started']),
                         'sessions_total': int(port_subs_stats[0]['Sessions_Total'])}
                    )

            except IndexError:
                pass

        return samples


class IxiaRfc2544Helper(Rfc2544ResourceHelper):

    def is_done(self):
        return self.latency and self.iteration.value > 10


class IxiaResourceHelper(ClientResourceHelper):

    LATENCY_TIME_SLEEP = 120

    def __init__(self, setup_helper, rfc_helper_type=None):
        super(IxiaResourceHelper, self).__init__(setup_helper)
        self.scenario_helper = setup_helper.scenario_helper

        self._ixia_scenarios = {
            "IxiaBasic": IxiaBasicScenario,
            "IxiaPppoeClient": IxiaPppoeClientScenario,
        }

        self.client = ixnet_api.IxNextgen()

        if rfc_helper_type is None:
            rfc_helper_type = IxiaRfc2544Helper

        self.rfc_helper = rfc_helper_type(self.scenario_helper)
        self.uplink_ports = None
        self.downlink_ports = None
        self.context_cfg = None
        self._ix_scenario = None
        self._connect()

    def _connect(self, client=None):
        self.client.connect(self.vnfd_helper)

    def get_stats(self, *args, **kwargs):
        return self._ix_scenario.get_statistics()

    def setup(self):
        super(IxiaResourceHelper, self).setup()
        self._init_ix_scenario()

    def stop_collect(self):
        self._ix_scenario.stop_protocols()
        self._terminated.value = 1

    def generate_samples(self, ports, duration):
        return self._ix_scenario.generate_samples(self, ports, duration)

    def _init_ix_scenario(self):
        ixia_config = self.scenario_helper.scenario_cfg.get('ixia_config', 'IxiaBasic')

        if ixia_config in self._ixia_scenarios:
            scenario_type = self._ixia_scenarios[ixia_config]

            self._ix_scenario = scenario_type(self.client, self.context_cfg,
                                              self.scenario_helper.scenario_cfg['options'])
        else:
            raise RuntimeError(
                "IXIA config type '{}' not supported".format(ixia_config))

    def _initialize_client(self, traffic_profile):
        """Initialize the IXIA IxNetwork client and configure the server"""
        self.client.clear_config()
        self.client.assign_ports()
        self._ix_scenario.apply_config()
        self._ix_scenario.create_traffic_model(traffic_profile)

    def update_tracking_options(self):
        self._ix_scenario.update_tracking_options()

    def run_traffic(self, traffic_profile, *args):
        if self._terminated.value:
            return

        min_tol = self.rfc_helper.tolerance_low
        max_tol = self.rfc_helper.tolerance_high
        precision = self.rfc_helper.tolerance_precision
        default = "00:00:00:00:00:00"

        self._build_ports()
        traffic_profile.update_traffic_profile(self)
        self._initialize_client(traffic_profile)

        mac = {}
        for port_name in self.vnfd_helper.port_pairs.all_ports:
            intf = self.vnfd_helper.find_interface(name=port_name)
            virt_intf = intf["virtual-interface"]
            # we only know static traffic id by reading the json
            # this is used by _get_ixia_trafficrofile
            port_num = self.vnfd_helper.port_num(intf)
            mac["src_mac_{}".format(port_num)] = virt_intf.get("local_mac", default)
            mac["dst_mac_{}".format(port_num)] = virt_intf.get("dst_mac", default)

        self._ix_scenario.run_protocols()

        try:
            while not self._terminated.value:
                first_run = traffic_profile.execute_traffic(
                    self, self.client, mac)
                self.client_started.value = 1
                # pylint: disable=unnecessary-lambda
                utils.wait_until_true(lambda: self.client.is_traffic_stopped(),
                                      timeout=traffic_profile.config.duration * 2)
                rfc2544_opts = self._ix_scenario.get_tc_rfc2544_options()
                samples = self.generate_samples(traffic_profile.ports,
                                                traffic_profile.config.duration)

                completed, samples = traffic_profile.get_drop_percentage(
                    samples, min_tol, max_tol, precision, first_run=first_run,
                    tc_rfc2544_opts=rfc2544_opts)
                self._queue.put(samples)

                if completed:
                    self._terminated.value = 1

        except Exception:  # pylint: disable=broad-except
            LOG.exception('Run Traffic terminated')

        self._ix_scenario.stop_protocols()
        self._terminated.value = 1

    def collect_kpi(self):
        self.rfc_helper.iteration.value += 1
        return super(IxiaResourceHelper, self).collect_kpi()


class IxiaTrafficGen(SampleVNFTrafficGen):

    APP_NAME = 'Ixia'

    def __init__(self, name, vnfd, task_id, setup_env_helper_type=None,
                 resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = IxiaResourceHelper
        super(IxiaTrafficGen, self).__init__(
            name, vnfd, task_id, setup_env_helper_type, resource_helper_type)
        self._ixia_traffic_gen = None
        self.ixia_file_name = ''
        self.vnf_port_pairs = []

    def _check_status(self):
        pass

    def terminate(self):
        self.resource_helper.stop_collect()
        super(IxiaTrafficGen, self).terminate()
