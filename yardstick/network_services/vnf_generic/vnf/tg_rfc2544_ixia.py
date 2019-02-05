# Copyright (c) 2016-2019 Intel Corporation
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
import collections

from six import moves
from yardstick.common import utils
from yardstick.common import exceptions
from yardstick.network_services.libs.ixia_libs.ixnet import ixnet_api
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import Rfc2544ResourceHelper


LOG = logging.getLogger(__name__)

WAIT_AFTER_CFG_LOAD = 10
WAIT_FOR_TRAFFIC = 30
WAIT_PROTOCOLS_STARTED = 420


class IxiaBasicScenario(object):
    """Ixia Basic scenario for flow from port to port"""

    def __init__(self, client, context_cfg, ixia_cfg):

        self.client = client
        self.context_cfg = context_cfg
        self.ixia_cfg = ixia_cfg

        self._uplink_vports = None
        self._downlink_vports = None

    def apply_config(self):
        pass

    def run_protocols(self):
        pass

    def stop_protocols(self):
        pass

    def create_traffic_model(self, traffic_profile=None):
        # pylint: disable=unused-argument
        vports = self.client.get_vports()
        self._uplink_vports = vports[::2]
        self._downlink_vports = vports[1::2]
        self.client.create_traffic_model(self._uplink_vports,
                                         self._downlink_vports)

    def _get_stats(self):
        return self.client.get_statistics()

    def generate_samples(self, resource_helper, ports, duration):
        stats = self._get_stats()

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

    def update_tracking_options(self):
        pass

    def get_tc_rfc2544_options(self):
        pass


class IxiaL3Scenario(IxiaBasicScenario):
    """Ixia scenario for L3 flow between static ip's"""

    def _add_static_ips(self):
        vports = self.client.get_vports()
        uplink_intf_vport = [(self.client.get_static_interface(vport), vport)
                             for vport in vports[::2]]
        downlink_intf_vport = [(self.client.get_static_interface(vport), vport)
                               for vport in vports[1::2]]

        for index in range(len(uplink_intf_vport)):
            intf, vport = uplink_intf_vport[index]
            try:
                iprange = self.ixia_cfg['flow'].get('src_ip')[index]
                start_ip = utils.get_ip_range_start(iprange)
                count = utils.get_ip_range_count(iprange)
                self.client.add_static_ipv4(intf, vport, start_ip, count, '32')
            except IndexError:
                raise exceptions.IncorrectFlowOption(
                    option="src_ip", link="uplink_{}".format(index))

            intf, vport = downlink_intf_vport[index]
            try:
                iprange = self.ixia_cfg['flow'].get('dst_ip')[index]
                start_ip = utils.get_ip_range_start(iprange)
                count = utils.get_ip_range_count(iprange)
                self.client.add_static_ipv4(intf, vport, start_ip, count, '32')
            except IndexError:
                raise exceptions.IncorrectFlowOption(
                    option="dst_ip", link="downlink_{}".format(index))

    def _add_interfaces(self):
        vports = self.client.get_vports()
        uplink_vports = (vport for vport in vports[::2])
        downlink_vports = (vport for vport in vports[1::2])

        ix_node = next(node for _, node in self.context_cfg['nodes'].items()
                       if node['role'] == 'IxNet')

        for intf in ix_node['interfaces'].values():
            ip = intf.get('local_ip')
            mac = intf.get('local_mac')
            gateway = None
            try:
                gateway = next(route.get('gateway')
                               for route in ix_node.get('routing_table')
                               if route.get('if') == intf.get('ifname'))
            except StopIteration:
                LOG.debug("Gateway not provided")

            if 'uplink' in intf.get('vld_id'):
                self.client.add_interface(next(uplink_vports),
                                          ip, mac, gateway)
            else:
                self.client.add_interface(next(downlink_vports),
                                          ip, mac, gateway)

    def apply_config(self):
        self._add_interfaces()
        self._add_static_ips()

    def create_traffic_model(self, traffic_profile=None):
        # pylint: disable=unused-argument
        vports = self.client.get_vports()
        self._uplink_vports = vports[::2]
        self._downlink_vports = vports[1::2]

        uplink_endpoints = [port + '/protocols/static'
                            for port in self._uplink_vports]
        downlink_endpoints = [port + '/protocols/static'
                              for port in self._downlink_vports]

        self.client.create_ipv4_traffic_model(uplink_endpoints,
                                              downlink_endpoints)


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
        if endpoints_obj_pairs:
            uplink_endpoints = endpoints_obj_pairs[::2]
            downlink_endpoints = endpoints_obj_pairs[1::2]
        else:
            uplink_endpoints = self._access_topologies
            downlink_endpoints = self._core_topologies
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
           specified 'port' key, flows will be created between topologies
           on corresponding access and core port.
           E.g.:
           Access topology on xe0: topology1
           Core topology on xe1: topology2
           Flows will be created between:
           topology1 -> topology2
           topology2 -> topology1

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

    def _get_stats(self):
        return self.client.get_pppoe_scenario_statistics()

    @staticmethod
    def get_flow_id_data(stats, flow_id, key):
        result = [float(flow.get(key)) for flow in stats if flow['id'] == flow_id]
        return sum(result) / len(result)

    def get_priority_flows_stats(self, samples, duration):
        results = {}
        priorities = set([flow['IP_Priority'] for flow in samples])
        for priority in priorities:
            tx_frames = sum(
                [int(flow['Tx_Frames']) for flow in samples
                 if flow['IP_Priority'] == priority])
            rx_frames = sum(
                [int(flow['Rx_Frames']) for flow in samples
                 if flow['IP_Priority'] == priority])
            prio_flows_num = len([flow for flow in samples
                                  if flow['IP_Priority'] == priority])
            avg_latency_ns = sum(
                [int(flow['Store-Forward_Avg_latency_ns']) for flow in samples
                 if flow['IP_Priority'] == priority]) / prio_flows_num
            min_latency_ns = sum(
                [int(flow['Store-Forward_Min_latency_ns']) for flow in samples
                 if flow['IP_Priority'] == priority]) / prio_flows_num
            max_latency_ns = sum(
                [int(flow['Store-Forward_Max_latency_ns']) for flow in samples
                 if flow['IP_Priority'] == priority]) / prio_flows_num
            tx_throughput = float(tx_frames) / duration
            rx_throughput = float(rx_frames) / duration
            results[priority] = {
                'in_packets': rx_frames,
                'out_packets': tx_frames,
                'RxThroughput': round(rx_throughput, 3),
                'TxThroughput': round(tx_throughput, 3),
                'avg_latency_ns': utils.safe_cast(avg_latency_ns, int, 0),
                'min_latency_ns': utils.safe_cast(min_latency_ns, int, 0),
                'max_latency_ns': utils.safe_cast(max_latency_ns, int, 0)
            }
        return results

    def generate_samples(self, resource_helper, ports, duration):

        stats = self._get_stats()
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
        port_flow_map = collections.defaultdict(set)
        for item in flows_stats:
            tx_port = item.pop('Tx_Port')
            tx_port_index = ixia_port_names.index(tx_port)
            port_flow_map[tx_port_index].update([item['id']])

        # Sort ports stats
        ports_stats = sorted(ports_stats, key=lambda k: k['port_id'])

        # Get priority flows stats
        prio_flows_stats = self.get_priority_flows_stats(flows_stats, duration)
        samples['priority_stats'] = prio_flows_stats

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

                avg_latency = \
                    sum([float(self.get_flow_id_data(
                        flows_stats, flow, 'Store-Forward_Avg_latency_ns'))
                        for flow in port_flow_map[port_num]]) / len(port_flow_map[port_num])
                min_latency = \
                    sum([float(self.get_flow_id_data(
                        flows_stats, flow, 'Store-Forward_Min_latency_ns'))
                        for flow in port_flow_map[port_num]]) / len(port_flow_map[port_num])
                max_latency = \
                    sum([float(self.get_flow_id_data(
                        flows_stats, flow, 'Store-Forward_Max_latency_ns'))
                        for flow in port_flow_map[port_num]]) / len(port_flow_map[port_num])

                samples[port_name] = {
                    'rx_throughput_kps': float(ports_stats[port_num]['Rx_Rate_Kbps']),
                    'tx_throughput_kps': float(ports_stats[port_num]['Tx_Rate_Kbps']),
                    'rx_throughput_mbps': float(ports_stats[port_num]['Rx_Rate_Mbps']),
                    'tx_throughput_mbps': float(ports_stats[port_num]['Tx_Rate_Mbps']),
                    'in_packets': int(ports_stats[port_num]['Valid_Frames_Rx']),
                    'out_packets': int(ports_stats[port_num]['Frames_Tx']),
                    'RxThroughput': float(ports_stats[port_num]['Valid_Frames_Rx']) / duration,
                    'TxThroughput': float(ports_stats[port_num]['Frames_Tx']) / duration,
                    'Store-Forward_Avg_latency_ns': utils.safe_cast(avg_latency, int, 0),
                    'Store-Forward_Min_latency_ns': utils.safe_cast(min_latency, int, 0),
                    'Store-Forward_Max_latency_ns': utils.safe_cast(max_latency, int, 0)
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
            "IxiaL3": IxiaL3Scenario,
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

    def run_traffic(self, traffic_profile):
        if self._terminated.value:
            return

        min_tol = self.rfc_helper.tolerance_low
        max_tol = self.rfc_helper.tolerance_high
        precision = self.rfc_helper.tolerance_precision
        resolution = self.rfc_helper.resolution
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
                first_run = traffic_profile.execute_traffic(self, self.client,
                                                            mac)
                self.client_started.value = 1
                # pylint: disable=unnecessary-lambda
                utils.wait_until_true(lambda: self.client.is_traffic_stopped(),
                                      timeout=traffic_profile.config.duration * 2)
                rfc2544_opts = self._ix_scenario.get_tc_rfc2544_options()
                samples = self.generate_samples(traffic_profile.ports,
                                                traffic_profile.config.duration)

                completed, samples = traffic_profile.get_drop_percentage(
                    samples, min_tol, max_tol, precision, resolution,
                    first_run=first_run, tc_rfc2544_opts=rfc2544_opts)
                self._queue.put(samples)

                if completed:
                    self._terminated.value = 1

        except Exception:  # pylint: disable=broad-except
            LOG.exception('Run Traffic terminated')

        self._ix_scenario.stop_protocols()
        self.client_started.value = 0
        self._terminated.value = 1

    def run_test(self, traffic_profile, tasks_queue, results_queue, *args): # pragma: no cover
        LOG.info("Ixia resource_helper run_test")
        if self._terminated.value:
            return

        min_tol = self.rfc_helper.tolerance_low
        max_tol = self.rfc_helper.tolerance_high
        precision = self.rfc_helper.tolerance_precision
        resolution = self.rfc_helper.resolution
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
            completed = False
            self.rfc_helper.iteration.value = 0
            self.client_started.value = 1
            while completed is False and not self._terminated.value:
                LOG.info("Wait for task ...")

                try:
                    task = tasks_queue.get(True, 5)
                except moves.queue.Empty:
                    continue
                else:
                    if task != 'RUN_TRAFFIC':
                        continue

                self.rfc_helper.iteration.value += 1
                LOG.info("Got %s task, start iteration %d", task,
                         self.rfc_helper.iteration.value)
                first_run = traffic_profile.execute_traffic(self, self.client,
                                                            mac)
                # pylint: disable=unnecessary-lambda
                utils.wait_until_true(lambda: self.client.is_traffic_stopped(),
                                      timeout=traffic_profile.config.duration * 2)
                samples = self.generate_samples(traffic_profile.ports,
                                                traffic_profile.config.duration)

                completed, samples = traffic_profile.get_drop_percentage(
                    samples, min_tol, max_tol, precision, resolution,
                    first_run=first_run)
                samples['Iteration'] = self.rfc_helper.iteration.value
                self._queue.put(samples)

                if completed:
                    LOG.debug("IxiaResourceHelper::run_test - test completed")
                    results_queue.put('COMPLETE')
                else:
                    results_queue.put('CONTINUE')
                tasks_queue.task_done()

        except Exception:  # pylint: disable=broad-except
            LOG.exception('Run Traffic terminated')

        self._ix_scenario.stop_protocols()
        self.client_started.value = 0
        LOG.debug("IxiaResourceHelper::run_test done")


class IxiaTrafficGen(SampleVNFTrafficGen):

    APP_NAME = 'Ixia'

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = IxiaResourceHelper

        super(IxiaTrafficGen, self).__init__(name, vnfd, setup_env_helper_type,
                                             resource_helper_type)
        self._ixia_traffic_gen = None
        self.ixia_file_name = ''
        self.vnf_port_pairs = []

    def _check_status(self):
        pass

    def terminate(self):
        self.resource_helper.stop_collect()
        super(IxiaTrafficGen, self).terminate()
