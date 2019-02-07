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

import unittest
import mock
import os
import re
import copy

from yardstick.common import utils
from yardstick.common import exceptions
from yardstick.benchmark.contexts import base as ctx_base
from yardstick.network_services.vnf_generic.vnf import acl_vnf
from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper
from yardstick.network_services.nfvi.resource import ResourceProfile
from yardstick.network_services.vnf_generic.vnf.acl_vnf import AclApproxSetupEnvSetupEnvHelper
from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh


TEST_FILE_YAML = 'nsb_test_case.yaml'
SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'


name = 'vnf__1'


@mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Process")
class TestAclApproxVnf(unittest.TestCase):
    VNFD = {'vnfd:vnfd-catalog':
            {'vnfd':
             [{'short-name': 'VpeVnf',
               'vdu':
               [{'routing_table':
                 [{'network': '152.16.100.20',
                   'netmask': '255.255.255.0',
                   'gateway': '152.16.100.20',
                   'if': 'xe0'},
                  {'network': '152.16.40.20',
                   'netmask': '255.255.255.0',
                   'gateway': '152.16.40.20',
                   'if': 'xe1'}],
                 'description': 'VPE approximation using DPDK',
                 'name': 'vpevnf-baremetal',
                 'nd_route_tbl':
                 [{'network': '0064:ff9b:0:0:0:0:9810:6414',
                   'netmask': '112',
                   'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                   'if': 'xe0'},
                  {'network': '0064:ff9b:0:0:0:0:9810:2814',
                   'netmask': '112',
                   'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                   'if': 'xe1'}],
                 'id': 'vpevnf-baremetal',
                 'external-interface':
                 [{'virtual-interface':
                   {'dst_mac': '00:00:00:00:00:04',
                    'vpci': '0000:05:00.0',
                    'local_ip': '152.16.100.19',
                    'type': 'PCI-PASSTHROUGH',
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': 0,
                    'bandwidth': '10 Gbps',
                    'driver': "i40e",
                    'dst_ip': '152.16.100.20',
                    'local_iface_name': 'xe0',
                    'local_mac': '00:00:00:00:00:02'},
                   'vnfd-connection-point-ref': 'xe0',
                   'name': 'xe0'},
                  {'virtual-interface':
                   {'dst_mac': '00:00:00:00:00:03',
                    'vpci': '0000:05:00.1',
                    'local_ip': '152.16.40.19',
                    'type': 'PCI-PASSTHROUGH',
                    'driver': "i40e",
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': 1,
                    'bandwidth': '10 Gbps',
                    'dst_ip': '152.16.40.20',
                    'local_iface_name': 'xe1',
                    'local_mac': '00:00:00:00:00:01'},
                   'vnfd-connection-point-ref': 'xe1',
                   'name': 'xe1'}]}],
               'description': 'Vpe approximation using DPDK',
               'mgmt-interface':
                   {'vdu-id': 'vpevnf-baremetal',
                    'host': '1.2.1.1',
                    'password': 'r00t',
                    'user': 'root',
                    'ip': '1.2.1.1'},
               'benchmark':
                   {'kpi': ['packets_in', 'packets_fwd', 'packets_dropped']},
               'connection-point': [{'type': 'VPORT', 'name': 'xe0'},
                                    {'type': 'VPORT', 'name': 'xe1'}],
               'id': 'AclApproxVnf', 'name': 'VPEVnfSsh'}]}}

    scenario_cfg = {'options': {'packetsize': 64, 'traffic_type': 4,
                                'rfc2544': {'allowed_drop_rate': '0.8 - 1'},
                                'vnf__1': {'rules': 'acl_1rule.yaml',
                                           'vnf_config': {'lb_config': 'SW',
                                                          'lb_count': 1,
                                                          'worker_config':
                                                          '1C/1T',
                                                          'worker_threads': 1}}
                                },
                    'task_id': 'a70bdf4a-8e67-47a3-9dc1-273c14506eb7',
                    'task_path': '/tmp',
                    'tc': 'tc_ipv4_1Mflow_64B_packetsize',
                    'runner': {'object': 'NetworkServiceTestCase',
                               'interval': 35,
                               'output_filename': '/tmp/yardstick.out',
                               'runner_id': 74476, 'duration': 400,
                               'type': 'Duration'},
                    'traffic_profile': 'ipv4_throughput_acl.yaml',
                    'traffic_options': {'flow': 'ipv4_Packets_acl.yaml',
                                        'imix': 'imix_voice.yaml'},
                    'type': 'ISB',
                    'nodes': {'tg__2': 'trafficgen_2.yardstick',
                              'tg__1': 'trafficgen_1.yardstick',
                              'vnf__1': 'vnf.yardstick'},
                    'topology': 'vpe-tg-topology-baremetal.yaml'}

    context_cfg = {'nodes': {'tg__2':
                             {'member-vnf-index': '3',
                              'role': 'TrafficGen',
                              'name': 'trafficgen_2.yardstick',
                              'vnfd-id-ref': 'tg__2',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens513f0',
                                       'vld_id': acl_vnf.AclApproxVnf.DOWNLINK,
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.40.20',
                                       'dst_mac': '00:00:00:00:00:01',
                                       'local_mac': '00:00:00:00:00:03',
                                       'dst_ip': '152.16.40.19',
                                       'driver': 'ixgbe',
                                       'vpci': '0000:02:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens513f1',
                                       'netmask': '255.255.255.0',
                                       'network': '202.16.100.0',
                                       'local_ip': '202.16.100.20',
                                       'local_mac': '00:1e:67:d0:60:5d',
                                       'driver': 'ixgbe',
                                       'vpci': '0000:02:00.1',
                                       'dpdk_port_num': 1}},
                              'password': 'r00t',
                              'VNF model': 'l3fwd_vnf.yaml',
                              'user': 'root'},
                             'tg__1':
                             {'member-vnf-index': '1',
                              'role': 'TrafficGen',
                              'name': 'trafficgen_1.yardstick',
                              'vnfd-id-ref': 'tg__1',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens785f0',
                                       'vld_id': acl_vnf.AclApproxVnf.UPLINK,
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.20',
                                       'dst_mac': '00:00:00:00:00:02',
                                       'local_mac': '00:00:00:00:00:04',
                                       'dst_ip': '152.16.100.19',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens785f1',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.21',
                                       'local_mac': '00:00:00:00:00:01',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.1',
                                       'dpdk_port_num': 1}},
                              'password': 'r00t',
                              'VNF model': 'tg_rfc2544_tpl.yaml',
                              'user': 'root'},
                             'vnf__1':
                             {'name': 'vnf.yardstick',
                              'vnfd-id-ref': 'vnf__1',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens786f0',
                                       'vld_id': acl_vnf.AclApproxVnf.UPLINK,
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.19',
                                       'dst_mac': '00:00:00:00:00:04',
                                       'local_mac': '00:00:00:00:00:02',
                                       'dst_ip': '152.16.100.20',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens786f1',
                                       'vld_id': acl_vnf.AclApproxVnf.DOWNLINK,
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.40.19',
                                       'dst_mac': '00:00:00:00:00:03',
                                       'local_mac': '00:00:00:00:00:01',
                                       'dst_ip': '152.16.40.20',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.1',
                                       'dpdk_port_num': 1}},
                              'routing_table':
                              [{'netmask': '255.255.255.0',
                                'gateway': '152.16.100.20',
                                'network': '152.16.100.20',
                                'if': 'xe0'},
                               {'netmask': '255.255.255.0',
                                'gateway': '152.16.40.20',
                                'network': '152.16.40.20',
                                'if': 'xe1'}],
                              'member-vnf-index': '2',
                              'host': '1.2.1.1',
                              'role': 'vnf',
                              'user': 'root',
                              'nd_route_tbl':
                              [{'netmask': '112',
                                'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                                'network': '0064:ff9b:0:0:0:0:9810:6414',
                                'if': 'xe0'},
                               {'netmask': '112',
                                'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                                'network': '0064:ff9b:0:0:0:0:9810:2814',
                                'if': 'xe1'}],
                              'password': 'r00t',
                              'VNF model': 'acl_vnf.yaml'}}}

    def test___init__(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = acl_vnf.AclApproxVnf(name, vnfd)
        self.assertIsNone(acl_approx_vnf._vnf_process)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server', return_value='mock_node')
    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = acl_vnf.AclApproxVnf(name, vnfd)
        acl_approx_vnf.scenario_helper.scenario_cfg = {
            'nodes': {acl_approx_vnf.name: "mock"}
        }
        acl_approx_vnf.q_in = mock.MagicMock()
        acl_approx_vnf.q_out = mock.MagicMock()
        acl_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        acl_approx_vnf.resource = mock.Mock(autospec=ResourceProfile)
        acl_approx_vnf.vnf_execute = mock.Mock(return_value="")
        result = {
            'physical_node': 'mock_node',
            'packets_dropped': 0,
            'packets_fwd': 0,
            'packets_in': 0
        }
        self.assertEqual(result, acl_approx_vnf.collect_kpi())

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_vnf_execute_command(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = acl_vnf.AclApproxVnf(name, vnfd)
        acl_approx_vnf.q_in = mock.MagicMock()
        acl_approx_vnf.q_out = mock.MagicMock()
        acl_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        cmd = "quit"
        self.assertEqual("", acl_approx_vnf.vnf_execute(cmd))

    @mock.patch(SSH_HELPER)
    def test_get_stats(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = acl_vnf.AclApproxVnf(name, vnfd)
        acl_approx_vnf.q_in = mock.MagicMock()
        acl_approx_vnf.q_out = mock.MagicMock()
        acl_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        result = "ACL TOTAL: pkts_processed: 100, pkts_drop: 0, spkts_received: 100"
        acl_approx_vnf.vnf_execute = mock.Mock(return_value=result)
        self.assertEqual(result, acl_approx_vnf.get_stats())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @mock.patch("yardstick.network_services.vnf_generic.vnf.acl_vnf.hex")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.acl_vnf.eval")
    @mock.patch('yardstick.network_services.vnf_generic.vnf.acl_vnf.open')
    @mock.patch(SSH_HELPER)
    def test_run_acl(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = acl_vnf.AclApproxVnf(name, vnfd)
        acl_approx_vnf._build_config = mock.MagicMock()
        acl_approx_vnf.queue_wrapper = mock.MagicMock()
        acl_approx_vnf.scenario_helper.scenario_cfg = self.scenario_cfg
        acl_approx_vnf.vnf_cfg = {'lb_config': 'SW',
                                  'lb_count': 1,
                                  'worker_config': '1C/1T',
                                  'worker_threads': 1}
        acl_approx_vnf.all_options = {'traffic_type': '4',
                                      'topology': 'nsb_test_case.yaml'}
        acl_approx_vnf._run()
        acl_approx_vnf.ssh_helper.run.assert_called_once()

    @mock.patch.object(utils, 'find_relative_file')
    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = acl_vnf.AclApproxVnf(name, vnfd)
        acl_approx_vnf.deploy_helper = mock.MagicMock()
        acl_approx_vnf.resource_helper = mock.MagicMock()
        acl_approx_vnf._build_config = mock.MagicMock()
        self.scenario_cfg['vnf_options'] = {'acl': {'cfg': "",
                                                    'rules': ""}}
        acl_approx_vnf.q_out.put("pipeline>")
        acl_approx_vnf.WAIT_TIME = 0
        self.scenario_cfg.update({"nodes": {"vnf__1": ""}})
        self.assertIsNone(acl_approx_vnf.instantiate(self.scenario_cfg,
                                                     self.context_cfg))

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = acl_vnf.AclApproxVnf(name, vnfd)
        acl_approx_vnf._vnf_process = mock.MagicMock()
        acl_approx_vnf._vnf_process.terminate = mock.Mock()
        acl_approx_vnf.used_drivers = {"01:01.0": "i40e",
                                       "01:01.1": "i40e"}
        acl_approx_vnf.vnf_execute = mock.MagicMock()
        acl_approx_vnf.dpdk_devbind = "dpdk-devbind.py"
        acl_approx_vnf._resource_collect_stop = mock.Mock()
        self.assertIsNone(acl_approx_vnf.terminate())


class TestAclApproxSetupEnvSetupEnvHelper(unittest.TestCase):

    ACL_CONFIG = {"access-list-entries": [{
                     "actions": [
                       "count",
                       {"fwd": {
                           "port": 0
                         }
                       }
                     ],
                     "matches": {
                       "destination-ipv4-network": "152.16.0.0/24",
                       "destination-port-range": {
                         "lower-port": 0,
                         "upper-port": 65535
                       },
                       "source-ipv4-network": "0.0.0.0/0",
                       "source-port-range": {
                         "lower-port": 0,
                         "upper-port": 65535
                       },
                       "protocol-mask": 255,
                       "protocol": 127,
                       "priority": 1
                     },
                     "rule-name": "rule1588"
                   }
                 ]}

    def test_get_default_flows(self):
        """Check if default ACL SampleVNF CLI commands are
        generated correctly"""
        ssh_helper = mock.Mock()
        vnfd_helper = VnfdHelper({'vdu': [
            {'external-interface': [
                {
                    'virtual-interface': {
                        'local_ip': '152.16.100.19',
                        'netmask': '255.255.255.0',
                        'dpdk_port_num': 0,
                        'dst_ip': '152.16.100.20',
                        'vld_id': 'uplink_0',
                        'ifname': 'xe0',
                    },
                    'vnfd-connection-point-ref': 'xe0',
                    'name': 'xe0'
                },
                {
                    'virtual-interface': {
                        'local_ip': '152.16.40.19',
                        'netmask': '255.255.255.0',
                        'dpdk_port_num': 1,
                        'dst_ip': '152.16.40.20',
                        'vld_id': 'downlink_0',
                        'ifname': 'xe1',
                    },
                    'vnfd-connection-point-ref': 'xe1',
                    'name': 'xe1'
                }
            ]}
        ]})
        setup_helper = AclApproxSetupEnvSetupEnvHelper(vnfd_helper, ssh_helper, None)
        self.check_acl_commands(setup_helper.get_flows_config(), [
            # format: (<cli pattern>, <number of expected matches>)
            ("^p action add [0-9]+ accept$", 2),
            ("^p action add [0-9]+ count$", 2),
            ("^p action add [0-9]+ fwd 1$", 1),
            ("^p action add [0-9]+ fwd 0$", 1),
            ("^p acl add 1 152.16.100.0 24 152.16.40.0 24 0 65535 0 65535 0 0 [0-9]+$", 1),
            ("^p acl add 1 152.16.40.0 24 152.16.100.0 24 0 65535 0 65535 0 0 [0-9]+$", 1),
            ("^p acl applyruleset$", 1)
        ])

    @mock.patch.object(AclApproxSetupEnvSetupEnvHelper, 'get_default_flows')
    def test_get_flows_config(self, get_default_flows):
        """Check if provided ACL config can be converted to
        ACL SampleVNF CLI commands correctly"""
        ssh_helper = mock.Mock()
        setup_helper = AclApproxSetupEnvSetupEnvHelper(None, ssh_helper, None)
        get_default_flows.return_value = ({}, [])
        self.check_acl_commands(setup_helper.get_flows_config(self.ACL_CONFIG), [
            # format: (<cli pattern>, <number of expected matches>)
            ("^p action add [0-9]+ count$", 1),
            ("^p action add [0-9]+ fwd 0$", 1),
            ("^p acl add 1 0.0.0.0 0 152.16.0.0 24 0 65535 0 65535 127 0 [0-9]+$", 1),
            ("^p acl applyruleset$", 1)
        ])

    @mock.patch.object(AclApproxSetupEnvSetupEnvHelper, 'get_default_flows')
    def test_get_flows_config_invalid_action(self, get_default_flows):
        """Check if incorrect ACL config fails to convert
        to ACL SampleVNF CLI commands"""
        ssh_helper = mock.Mock()
        setup_helper = AclApproxSetupEnvSetupEnvHelper(None, ssh_helper, None)
        get_default_flows.return_value = ({}, [])
        # duplicate config and add invald action
        acl_config = copy.deepcopy(self.ACL_CONFIG)
        acl_config['access-list-entries'][0]["actions"].append({"xnat": {}})
        self.assertRaises(exceptions.AclUnknownActionTemplate,
                          setup_helper.get_flows_config, acl_config)

    @mock.patch.object(AclApproxSetupEnvSetupEnvHelper, 'get_default_flows')
    def test_get_flows_config_invalid_action_param(self, get_default_flows):
        """Check if ACL config with invalid action parameter fails to convert
        to ACL SampleVNF CLI commands"""
        ssh_helper = mock.Mock()
        setup_helper = AclApproxSetupEnvSetupEnvHelper(None, ssh_helper, None)
        get_default_flows.return_value = ({}, [])
        # duplicate config and add action with invalid parameter
        acl_config = copy.deepcopy(self.ACL_CONFIG)
        acl_config['access-list-entries'][0]["actions"].append(
            {"nat": {"xport": 0}})
        self.assertRaises(exceptions.AclMissingActionArguments,
            setup_helper.get_flows_config, acl_config)

    def check_acl_commands(self, config, expected_cli_patterns):
        """Check if expected ACL CLI commands (given as a list of patterns,
        `expected_cli_patterns` parameter) present in SampleVNF ACL
        configuration (given as a multiline string, `config` parameter)"""
        # Example of expected config:
        # ---------------------------
        # p action add 1 accept
        # p action add 1 fwd 1
        # p action add 2 accept
        # p action add 2 count
        # p action add 2 fwd 0
        # p acl add 1 152.16.100.0 24 152.16.40.0 24 0 65535 0 65535 0 0 1
        # p acl add 1 152.16.40.0 24 152.16.100.0 24 0 65535 0 65535 0 0 2
        # p acl applyruleset
        # ---------------------------
        # NOTE: The config above consists of actions ids, which are actually
        # unknown (generated at runtime), thus it's incorrect just to compare
        # the example ACL config above with the configuration returned by
        # get_flows_config() function. It's more correct to use CLI patterns
        # (RE) to find the required SampleVNF CLI commands in the multiline
        # string (SampleVNF ACL configuration).
        for pattern, num_of_match in expected_cli_patterns:
            # format: (<cli pattern>, <number of expected matches>)
            result = re.findall(pattern, config, re.MULTILINE)
            self.assertEqual(len(result), num_of_match)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.open')
    @mock.patch.object(utils, 'find_relative_file')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.MultiPortConfig')
    @mock.patch.object(utils, 'open_relative_file')
    def test_build_config(self, *args):
        vnfd_helper = mock.Mock()
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.vnf_cfg = {'lb_config': 'HW'}
        scenario_helper.options = {}
        scenario_helper.all_options = {}

        acl_approx_setup_helper = AclApproxSetupEnvSetupEnvHelper(vnfd_helper,
                                                                  ssh_helper,
                                                                  scenario_helper)

        acl_approx_setup_helper.get_flows_config = mock.Mock()
        acl_approx_setup_helper.ssh_helper.provision_tool = mock.Mock(return_value='tool_path')
        acl_approx_setup_helper.ssh_helper.all_ports = mock.Mock()
        acl_approx_setup_helper.vnfd_helper.port_nums = mock.Mock(return_value=[0, 1])
        expected = 'sudo tool_path -p 0x3 -f /tmp/acl_config -s /tmp/acl_script  --hwlb 3'
        self.assertEqual(acl_approx_setup_helper.build_config(), expected)
        acl_approx_setup_helper.get_flows_config.assert_called_once()
