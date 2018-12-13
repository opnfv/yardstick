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

from yardstick.common import utils
from yardstick.network_services.libs.ixia_libs.ixnet import ixnet_api
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import Rfc2544ResourceHelper


LOG = logging.getLogger(__name__)

WAIT_AFTER_CFG_LOAD = 10
WAIT_FOR_TRAFFIC = 30
WAIT_PROTOCOLS_STARTED = 360


class BaseIxiaScenario(object):
    def __init__(self, client, context_cfg, ixia_cfg):

        self.client = client
        self.context_cfg = context_cfg
        self.ixia_cfg = ixia_cfg

        self._uplink_vports = None
        self._downlink_vports = None

    def apply_config(self):
        pass

    def create_traffic_model(self):
        pass

    def run_protocols(self):
        pass

    def stop_protocols(self):
        pass


class IxiaBasicScenario(BaseIxiaScenario):
    def create_traffic_model(self, traffic_profile=None):
        # pylint: disable=unused-argument
        vports = self.client.get_vports()
        self._uplink_vports = vports[::2]
        self._downlink_vports = vports[1::2]
        self.client.create_traffic_model(self._uplink_vports,
                                         self._downlink_vports)


class IxiaL3Scenario(BaseIxiaScenario):
    def _add_static(self):
        vports = self.client.get_vports()
        uplink_intf_vport = [(self.client.get_list(vport, 'interface'), vport)
                       for vport in vports[::2]]
        downlink_intf_vport = [(self.client.get_list(vport, 'interface'), vport)
                         for vport in vports[1::2]]

        for index in range(len(uplink_intf_vport)):
            intf, vport = uplink_intf_vport[index]
            try:
                iprange = self.ixia_cfg['flow'].get('src_ip')[index]
                start_ip, count = self._parse_IP_range(iprange)
                self.client.add_static_ipv4(intf, vport, start_ip, count)
            except IndexError:
                pass

            intf, vport = downlink_intf_vport[index]
            try:
                iprange = self.ixia_cfg['flow'].get('dst_ip')[index]
                start_ip, count = self._parse_IP_range(iprange)
                self.client.add_static_ipv4(intf, vport, start_ip, count)
            except IndexError:
                pass

    def _parse_IP_range(self, iprange):
        start_range, end_range = iprange.split("-")
        ip1 = int(ipaddress.IPv4Address(start_range))
        ip2 = int(ipaddress.IPv4Address(end_range))
        return start_range, ip2 - ip1

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
        self._add_static()

    def create_traffic_model(self):
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

    def get_stats(self, *args, **kwargs):
        return self.client.get_statistics()

    def setup(self):
        super(IxiaResourceHelper, self).setup()
        self._init_ix_scenario()

    def stop_collect(self):
        self._ix_scenario.stop_protocols()
        self._terminated.value = 1

    def generate_samples(self, ports, duration):
        stats = self.get_stats()

        samples = {}
        # this is not DPDK port num, but this is whatever number we gave
        # when we selected ports and programmed the profile
        for port_num in ports:
            try:
                # reverse lookup port name from port_num so the stats dict is descriptive
                intf = self.vnfd_helper.find_interface_by_port(port_num)
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
                samples = self.generate_samples(traffic_profile.ports,
                                                traffic_profile.config.duration)

                completed, samples = traffic_profile.get_drop_percentage(
                    samples, min_tol, max_tol, precision, first_run=first_run)
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
