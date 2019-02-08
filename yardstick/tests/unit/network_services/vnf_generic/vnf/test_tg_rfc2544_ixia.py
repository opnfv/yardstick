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

import os

import mock
import six
import unittest
import ipaddress
import time
from collections import OrderedDict

from yardstick.common import utils
from yardstick.common import exceptions
from yardstick.benchmark import contexts
from yardstick.benchmark.contexts import base as ctx_base
from yardstick.network_services.libs.ixia_libs.ixnet import ixnet_api
from yardstick.network_services.traffic_profile import base as tp_base
from yardstick.network_services.vnf_generic.vnf import tg_rfc2544_ixia


TEST_FILE_YAML = 'nsb_test_case.yaml'

NAME = "tg__1"


class TestIxiaResourceHelper(unittest.TestCase):

    def setUp(self):
        self._mock_IxNextgen = mock.patch.object(ixnet_api, 'IxNextgen')
        self.mock_IxNextgen = self._mock_IxNextgen.start()
        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_IxNextgen.stop()

    def test___init___with_custom_rfc_helper(self):
        class MyRfcHelper(tg_rfc2544_ixia.IxiaRfc2544Helper):
            pass

        ixia_resource_helper = tg_rfc2544_ixia.IxiaResourceHelper(
            mock.Mock(), MyRfcHelper)
        self.assertIsInstance(ixia_resource_helper.rfc_helper, MyRfcHelper)

    def test__init_ix_scenario(self):
        mock_scenario = mock.Mock()
        mock_scenario_helper = mock.Mock()
        mock_scenario_helper.scenario_cfg = {'ixia_config': 'TestScenario',
                                             'options': 'scenario_options'}
        mock_setup_helper = mock.Mock(scenario_helper=mock_scenario_helper)
        ixia_resource_helper = tg_rfc2544_ixia.IxiaResourceHelper(mock_setup_helper)
        ixia_resource_helper._ixia_scenarios = {'TestScenario': mock_scenario}
        ixia_resource_helper.client = 'client'
        ixia_resource_helper.context_cfg = 'context'
        ixia_resource_helper._init_ix_scenario()
        mock_scenario.assert_called_once_with('client', 'context', 'scenario_options')

    def test__init_ix_scenario_not_supported_cfg_type(self):
        mock_scenario_helper = mock.Mock()
        mock_scenario_helper.scenario_cfg = {'ixia_config': 'FakeScenario',
                                             'options': 'scenario_options'}
        mock_setup_helper = mock.Mock(scenario_helper=mock_scenario_helper)
        ixia_resource_helper = tg_rfc2544_ixia.IxiaResourceHelper(mock_setup_helper)
        ixia_resource_helper._ixia_scenarios = {'TestScenario': mock.Mock()}
        with self.assertRaises(RuntimeError):
            ixia_resource_helper._init_ix_scenario()

    @mock.patch.object(tg_rfc2544_ixia.IxiaResourceHelper, '_init_ix_scenario')
    def test_setup(self, mock__init_ix_scenario):
        ixia_resource_helper = tg_rfc2544_ixia.IxiaResourceHelper(mock.Mock())
        ixia_resource_helper.setup()
        mock__init_ix_scenario.assert_called_once()

    def test_stop_collect_with_client(self):
        mock_client = mock.Mock()
        ixia_resource_helper = tg_rfc2544_ixia.IxiaResourceHelper(mock.Mock())
        ixia_resource_helper.client = mock_client
        ixia_resource_helper._ix_scenario = mock.Mock()
        ixia_resource_helper.stop_collect()
        self.assertEqual(1, ixia_resource_helper._terminated.value)
        ixia_resource_helper._ix_scenario.stop_protocols.assert_called_once()

    def test_run_traffic(self):
        mock_tprofile = mock.Mock()
        mock_tprofile.config.duration = 10
        mock_tprofile.get_drop_percentage.return_value = True, 'fake_samples'
        ixia_rhelper = tg_rfc2544_ixia.IxiaResourceHelper(mock.Mock())
        ixia_rhelper.rfc_helper = mock.Mock()
        ixia_rhelper.vnfd_helper = mock.Mock()
        ixia_rhelper._ix_scenario = mock.Mock()
        ixia_rhelper.vnfd_helper.port_pairs.all_ports = []
        with mock.patch.object(ixia_rhelper, 'generate_samples'), \
                mock.patch.object(ixia_rhelper, '_build_ports'), \
                mock.patch.object(ixia_rhelper, '_initialize_client'), \
                mock.patch.object(utils, 'wait_until_true'):
            ixia_rhelper.run_traffic(mock_tprofile)

        self.assertEqual('fake_samples', ixia_rhelper._queue.get())
        mock_tprofile.update_traffic_profile.assert_called_once()

    def test_run_test(self):
        expected_result = {'test': 'fake_samples', 'Iteration': 1}
        mock_tprofile = mock.Mock()
        mock_tprofile.config.duration = 10
        mock_tprofile.get_drop_percentage.return_value = \
            True, {'test': 'fake_samples'}
        ixia_rhelper = tg_rfc2544_ixia.IxiaResourceHelper(mock.Mock())
        tasks_queue = mock.Mock()
        tasks_queue.get.return_value = 'RUN_TRAFFIC'
        results_queue = mock.Mock()
        ixia_rhelper.rfc_helper = mock.Mock()
        ixia_rhelper.vnfd_helper = mock.Mock()
        ixia_rhelper._ix_scenario = mock.Mock()
        ixia_rhelper.vnfd_helper.port_pairs.all_ports = []
        with mock.patch.object(ixia_rhelper, 'generate_samples'), \
                mock.patch.object(ixia_rhelper, '_build_ports'), \
                mock.patch.object(ixia_rhelper, '_initialize_client'), \
                mock.patch.object(utils, 'wait_until_true'):
            ixia_rhelper.run_test(mock_tprofile, tasks_queue, results_queue)

        self.assertEqual(expected_result, ixia_rhelper._queue.get())
        mock_tprofile.update_traffic_profile.assert_called_once()
        tasks_queue.task_done.assert_called_once()
        results_queue.put.assert_called_once_with('COMPLETE')


@mock.patch.object(tg_rfc2544_ixia, 'ixnet_api')
class TestIXIATrafficGen(unittest.TestCase):
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
                'host': '1.1.1.1',
                'password': 'r00t',
                            'user': 'root',
                            'ip': '1.1.1.1'},
               'benchmark':
               {'kpi': ['packets_in', 'packets_fwd',
                        'packets_dropped']},
               'connection-point': [{'type': 'VPORT', 'name': 'xe0'},
                                    {'type': 'VPORT', 'name': 'xe1'}],
               'id': 'VpeApproxVnf', 'name': 'VPEVnfSsh'}]}}

    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,  # pps
            "flow_number": 10,
            "frame_size": 64}}

    TC_YAML = {'scenarios': [{'tc_options':
                              {'rfc2544': {'allowed_drop_rate': '0.8 - 1'}},
                              'runner': {'duration': 400,
                                         'interval': 35, 'type': 'Duration'},
                              'traffic_options':
                                  {'flow': 'ipv4_1flow_Packets_vpe.yaml',
                                   'imix': 'imix_voice.yaml'},
                              'vnf_options': {'vpe': {'cfg': 'vpe_config'}},
                              'traffic_profile': 'ipv4_throughput_vpe.yaml',
                              'type': 'NSPerf',
                              'nodes': {'tg__1': 'trafficgen_1.yardstick',
                                        'vnf__1': 'vnf.yardstick'},
                              'topology': 'vpe_vnf_topology.yaml'}],
               'context': {'nfvi_type': 'baremetal',
                           'type': contexts.CONTEXT_NODE,
                           'name': 'yardstick',
                           'file': '/etc/yardstick/nodes/pod.yaml'},
               'schema': 'yardstick:task:0.1'}

    def test___init__(self, *args):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            # NOTE(ralonsoh): check the object returned.
            tg_rfc2544_ixia.IxiaTrafficGen(NAME, vnfd)

    def test_listen_traffic(self, *args):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ixnet_traffic_gen = tg_rfc2544_ixia.IxiaTrafficGen(NAME, vnfd)
            self.assertIsNone(ixnet_traffic_gen.listen_traffic({}))

    @mock.patch.object(ctx_base.Context, 'get_context_from_server', return_value='fake_context')
    def test_instantiate(self, *args):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh_mock.run = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ixnet_traffic_gen = tg_rfc2544_ixia.IxiaTrafficGen(NAME, vnfd)
            scenario_cfg = {'tc': "nsb_test_case",
                            "topology": ""}
            scenario_cfg.update(
                {
                    'options': {
                        'packetsize': 64,
                        'traffic_type': 4,
                        'rfc2544': {
                            'allowed_drop_rate': '0.8 - 1'},
                        'vnf__1': {
                            'rules': 'acl_1rule.yaml',
                            'vnf_config': {
                                'lb_config': 'SW',
                                'lb_count': 1,
                                'worker_config': '1C/1T',
                                'worker_threads': 1}}}})
            scenario_cfg.update({
                'nodes': {ixnet_traffic_gen.name: "mock"}
            })
            ixnet_traffic_gen.topology = ""
            ixnet_traffic_gen.get_ixobj = mock.MagicMock()
            ixnet_traffic_gen._ixia_traffic_gen = mock.MagicMock()
            ixnet_traffic_gen._ixia_traffic_gen._connect = mock.Mock()
            self.assertRaises(
                IOError,
                ixnet_traffic_gen.instantiate(scenario_cfg, {}))

    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server', return_value='mock_node')
    def test_collect_kpi(self, *args):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock

            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ixnet_traffic_gen = tg_rfc2544_ixia.IxiaTrafficGen(NAME, vnfd)
            ixnet_traffic_gen.scenario_helper.scenario_cfg = {
                'nodes': {ixnet_traffic_gen.name: "mock"}
            }
            ixnet_traffic_gen.data = {}
            restult = ixnet_traffic_gen.collect_kpi()

            expected = {'collect_stats': {},
                        'physical_node': 'mock_node'}

            self.assertEqual(expected, restult)

    def test_terminate(self, *args):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            ixnet_traffic_gen = tg_rfc2544_ixia.IxiaTrafficGen(
                NAME, vnfd, resource_helper_type=mock.Mock())
            ixnet_traffic_gen._terminated = mock.MagicMock()
            ixnet_traffic_gen._terminated.value = 0
            ixnet_traffic_gen._ixia_traffic_gen = mock.MagicMock()
            ixnet_traffic_gen._ixia_traffic_gen.ix_stop_traffic = mock.Mock()
            ixnet_traffic_gen._traffic_process = mock.MagicMock()
            ixnet_traffic_gen._traffic_process.terminate = mock.Mock()
            self.assertIsNone(ixnet_traffic_gen.terminate())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test__check_status(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sut = tg_rfc2544_ixia.IxiaTrafficGen('vnf1', vnfd)
        sut._check_status()

    @mock.patch("yardstick.ssh.SSH")
    def test_traffic_runner(self, mock_ssh, *args):
        mock_traffic_profile = mock.Mock(autospec=tp_base.TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE
        # traffic_profile.ports is standardized on port_num
        mock_traffic_profile.ports = [0, 1]

        mock_ssh_instance = mock.Mock(autospec=mock_ssh.SSH)
        mock_ssh_instance.execute.return_value = 0, "", ""
        mock_ssh_instance.run.return_value = 0, "", ""

        mock_ssh.from_node.return_value = mock_ssh_instance

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vnfd["mgmt-interface"].update({
            'tg-config': {
                "ixchassis": "1.1.1.1",
                "py_bin_path": "/root",
            }
        })

        samples = {}
        name = ''
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {
                "Rx_Rate_Kbps": 20,
                "Tx_Rate_Kbps": 20,
                "Rx_Rate_Mbps": 10,
                "Tx_Rate_Mbps": 10,
                "RxThroughput": 10,
                "TxThroughput": 10,
                "Valid_Frames_Rx": 1000,
                "Frames_Tx": 1000,
                "in_packets": 1000,
                "out_packets": 1000,
            }

        samples.update({"CurrentDropPercentage": 0.0})

        last_res = [
            0,
            {
                "Rx_Rate_Kbps": [20, 20],
                "Tx_Rate_Kbps": [20, 20],
                "Rx_Rate_Mbps": [10, 10],
                "Tx_Rate_Mbps": [10, 10],
                "CurrentDropPercentage": [0, 0],
                "RxThroughput": [10, 10],
                "TxThroughput": [10, 10],
                "Frames_Tx": [1000, 1000],
                "in_packets": [1000, 1000],
                "Valid_Frames_Rx": [1000, 1000],
                "out_packets": [1000, 1000],
            },
        ]

        mock_traffic_profile.execute_traffic.return_value = [
            'Completed', samples]
        mock_traffic_profile.get_drop_percentage.return_value = [
            'Completed', samples]

        sut = tg_rfc2544_ixia.IxiaTrafficGen(name, vnfd)
        sut.vnf_port_pairs = [[[0], [1]]]
        sut.tc_file_name = self._get_file_abspath(TEST_FILE_YAML)
        sut.topology = ""

        sut.ssh_helper = mock.Mock()
        sut._traffic_process = mock.MagicMock()
        sut.generate_port_pairs = mock.Mock()

        sut._ixia_traffic_gen = mock.MagicMock()
        sut._ixia_traffic_gen.ix_get_statistics.return_value = last_res

        sut.resource_helper.client = mock.MagicMock()
        sut.resource_helper.client_started = mock.MagicMock()
        sut.resource_helper.client_started.value = 1
        sut.resource_helper.rfc_helper.iteration.value = 11
        sut.resource_helper._ix_scenario = mock.Mock()

        sut.scenario_helper.scenario_cfg = {
            'options': {
                'packetsize': 64,
                'traffic_type': 4,
                'rfc2544': {
                    'allowed_drop_rate': '0.8 - 1',
                    'latency': True
                },
                'vnf__1': {
                    'rules': 'acl_1rule.yaml',
                    'vnf_config': {
                        'lb_config': 'SW',
                        'lb_count': 1,
                        'worker_config': '1C/1T',
                        'worker_threads': 1,
                    },
                },
            },
            'task_path': '/path/to/task'
        }

        @mock.patch.object(six.moves.builtins, 'open', create=True)
        @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_rfc2544_ixia.open',
                    mock.mock_open(), create=True)
        @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_rfc2544_ixia.LOG.exception')
        def _traffic_runner(*args):
            result = sut._traffic_runner(mock_traffic_profile)
            self.assertIsNone(result)

        _traffic_runner()

    def test_run_traffic_once(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sut = tg_rfc2544_ixia.IxiaTrafficGen('vnf1', vnfd)
        sut._init_traffic_process = mock.Mock()
        sut._tasks_queue.put = mock.Mock()
        sut.resource_helper.client_started.value = 0
        sut.run_traffic_once(self.TRAFFIC_PROFILE)
        sut._tasks_queue.put.assert_called_once_with("RUN_TRAFFIC")
        sut._init_traffic_process.assert_called_once_with(self.TRAFFIC_PROFILE)

    def test__test_runner(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sut = tg_rfc2544_ixia.IxiaTrafficGen('vnf1', vnfd)
        tasks = 'tasks'
        results = 'results'
        sut.resource_helper = mock.Mock()
        sut._test_runner(self.TRAFFIC_PROFILE, tasks, results)
        sut.resource_helper.run_test.assert_called_once_with(self.TRAFFIC_PROFILE,
                                                             tasks, results)

    @mock.patch.object(time, 'sleep', return_value=0)
    def test__init_traffic_process(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sut = tg_rfc2544_ixia.IxiaTrafficGen('vnf1', vnfd)
        sut._test_runner = mock.Mock(return_value=0)
        sut.resource_helper = mock.Mock()
        sut.resource_helper.client_started.value = 0
        sut._init_traffic_process(self.TRAFFIC_PROFILE)

    def test_wait_on_traffic(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sut = tg_rfc2544_ixia.IxiaTrafficGen('vnf1', vnfd)
        sut._tasks_queue.join = mock.Mock(return_value=0)
        sut._result_queue.get = mock.Mock(return_value='COMPLETE')
        result = sut.wait_on_traffic()
        sut._tasks_queue.join.assert_called_once()
        sut._result_queue.get.assert_called_once()
        self.assertEqual(result, 'COMPLETE')


class TestIxiaBasicScenario(unittest.TestCase):

    STATS = {'stat_name': ['Card01/Port01',
                           'Card02/Port02'],
             'port_name': ['Ethernet - 001', 'Ethernet - 002'],
             'Frames_Tx': ['150', '150'],
             'Valid_Frames_Rx': ['150', '150'],
             'Frames_Tx_Rate': ['0.0', '0.0'],
             'Valid_Frames_Rx_Rate': ['0.0', '0.0'],
             'Bytes_Rx': ['9600', '9600'],
             'Bytes_Tx': ['9600', '9600'],
             'Tx_Rate_Kbps': ['0.0', '0.0'],
             'Rx_Rate_Mbps': ['0.0', '0.0'],
             'Tx_Rate_Mbps': ['0.0', '0.0'],
             'Rx_Rate_Kbps': ['0.0', '0.0'],
             'Store-Forward_Max_latency_ns': ['100', '200'],
             'Store-Forward_Min_latency_ns': ['100', '200'],
             'Store-Forward_Avg_latency_ns': ['100', '200']}

    def setUp(self):
        self._mock_IxNextgen = mock.patch.object(ixnet_api, 'IxNextgen')
        self.mock_IxNextgen = self._mock_IxNextgen.start()
        self.context_cfg = mock.Mock()
        self.ixia_cfg = mock.Mock()
        self.scenario = tg_rfc2544_ixia.IxiaBasicScenario(self.mock_IxNextgen,
                                                          self.context_cfg,
                                                          self.ixia_cfg)
        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_IxNextgen.stop()

    def test___init___(self):
        self.assertIsInstance(self.scenario, tg_rfc2544_ixia.IxiaBasicScenario)
        self.assertEqual(self.scenario.client, self.mock_IxNextgen)

    def test_create_traffic_model(self):
        self.mock_IxNextgen.get_vports.return_value = [1, 2, 3, 4]
        self.scenario.create_traffic_model()
        self.scenario.client.get_vports.assert_called_once()
        self.scenario.client.create_traffic_model.assert_called_once_with([1, 3], [2, 4])

    def test_apply_config(self):
        self.assertIsNone(self.scenario.apply_config())

    def test_run_protocols(self):
        self.assertIsNone(self.scenario.run_protocols())

    def test_stop_protocols(self):
        self.assertIsNone(self.scenario.stop_protocols())

    def test__get_stats(self):
        self.scenario._get_stats()
        self.scenario.client.get_statistics.assert_called_once()

    @mock.patch.object(tg_rfc2544_ixia.IxiaBasicScenario, '_get_stats')
    def test_generate_samples(self, mock_get_stats):

        expected_samples = {'xe0': {
                                'in_packets': 150,
                                'out_packets': 150,
                                'in_bytes': 9600,
                                'out_bytes': 9600,
                                'rx_throughput_mbps': 0.0,
                                'rx_throughput_kps': 0.0,
                                'RxThroughput': 5.0,
                                'TxThroughput': 5.0,
                                'RxThroughputBps': 320.0,
                                'TxThroughputBps': 320.0,
                                'tx_throughput_mbps': 0.0,
                                'tx_throughput_kps': 0.0,
                                'Store-Forward_Max_latency_ns': 100,
                                'Store-Forward_Min_latency_ns': 100,
                                'Store-Forward_Avg_latency_ns': 100},
                            'xe1': {
                                'in_packets': 150,
                                'out_packets': 150,
                                'in_bytes': 9600,
                                'out_bytes': 9600,
                                'rx_throughput_mbps': 0.0,
                                'rx_throughput_kps': 0.0,
                                'RxThroughput': 5.0,
                                'TxThroughput': 5.0,
                                'RxThroughputBps': 320.0,
                                'TxThroughputBps': 320.0,
                                'tx_throughput_mbps': 0.0,
                                'tx_throughput_kps': 0.0,
                                'Store-Forward_Max_latency_ns': 200,
                                'Store-Forward_Min_latency_ns': 200,
                                'Store-Forward_Avg_latency_ns': 200}}

        res_helper = mock.Mock()
        res_helper.vnfd_helper.find_interface_by_port.side_effect = \
            [{'name': 'xe0'}, {'name': 'xe1'}]
        ports = [0, 1]
        duration = 30
        mock_get_stats.return_value = self.STATS
        samples = self.scenario.generate_samples(res_helper, ports, duration)
        mock_get_stats.assert_called_once()
        self.assertEqual(samples, expected_samples)


class TestIxiaL3Scenario(TestIxiaBasicScenario):
    IXIA_CFG = {
        'flow': {
            'src_ip': ['192.168.0.1-192.168.0.50'],
            'dst_ip': ['192.168.1.1-192.168.1.150']
        }
    }

    CONTEXT_CFG = {
        'nodes': {
            'tg__0': {
                'role': 'IxNet',
                'interfaces': {
                    'xe0': {
                        'vld_id': 'uplink_0',
                        'local_ip': '10.1.1.1',
                        'local_mac': 'aa:bb:cc:dd:ee:ff',
                        'ifname': 'xe0'
                    },
                    'xe1': {
                        'vld_id': 'downlink_0',
                        'local_ip': '20.2.2.2',
                        'local_mac': 'bb:bb:cc:dd:ee:ee',
                        'ifname': 'xe1'
                    }
                },
                'routing_table': [{
                    'network': "152.16.100.20",
                    'netmask': '255.255.0.0',
                    'gateway': '152.16.100.21',
                    'if': 'xe0'
                }]
            }
        }
    }

    def setUp(self):
        super(TestIxiaL3Scenario, self).setUp()
        self.ixia_cfg = self.IXIA_CFG
        self.context_cfg = self.CONTEXT_CFG
        self.scenario = tg_rfc2544_ixia.IxiaL3Scenario(self.mock_IxNextgen,
                                                       self.context_cfg,
                                                       self.ixia_cfg)

    def test___init___(self):
        self.assertIsInstance(self.scenario, tg_rfc2544_ixia.IxiaL3Scenario)
        self.assertEqual(self.scenario.client, self.mock_IxNextgen)

    def test_create_traffic_model(self):
        self.mock_IxNextgen.get_vports.return_value = ['1', '2']
        self.scenario.create_traffic_model()
        self.scenario.client.get_vports.assert_called_once()
        self.scenario.client.create_ipv4_traffic_model.\
            assert_called_once_with(['1/protocols/static'],
                                    ['2/protocols/static'])

    def test_apply_config(self):
        self.scenario._add_interfaces = mock.Mock()
        self.scenario._add_static_ips = mock.Mock()
        self.assertIsNone(self.scenario.apply_config())

    def test__add_static(self):
        self.mock_IxNextgen.get_vports.return_value = ['1', '2']
        self.mock_IxNextgen.get_static_interface.side_effect = ['intf1',
                                                                'intf2']

        self.scenario._add_static_ips()

        self.mock_IxNextgen.get_static_interface.assert_any_call('1')
        self.mock_IxNextgen.get_static_interface.assert_any_call('2')

        self.scenario.client.add_static_ipv4.assert_any_call(
            'intf1', '1', '192.168.0.1', 49, '32')
        self.scenario.client.add_static_ipv4.assert_any_call(
            'intf2', '2', '192.168.1.1', 149, '32')

    def test__add_interfaces(self):
        self.mock_IxNextgen.get_vports.return_value = ['1', '2']

        self.scenario._add_interfaces()

        self.mock_IxNextgen.add_interface.assert_any_call('1',
                                                          '10.1.1.1',
                                                          'aa:bb:cc:dd:ee:ff',
                                                          '152.16.100.21')
        self.mock_IxNextgen.add_interface.assert_any_call('2',
                                                          '20.2.2.2',
                                                          'bb:bb:cc:dd:ee:ee',
                                                          None)


class TestIxiaPppoeClientScenario(unittest.TestCase):

    IXIA_CFG = {
        'pppoe_client': {
            'sessions_per_port': 4,
            'sessions_per_svlan': 1,
            's_vlan': 10,
            'c_vlan': 20,
            'ip': ['10.3.3.1', '10.4.4.1']
        },
        'ipv4_client': {
            'sessions_per_port': 1,
            'sessions_per_vlan': 1,
            'vlan': 101,
            'gateway_ip': ['10.1.1.1', '10.2.2.1'],
            'ip': ['10.1.1.1', '10.2.2.1'],
            'prefix': ['24', '24']
        },
        'priority': {
            'tos': {'precedence': [0, 4]}
        }
    }

    CONTEXT_CFG = {
        'nodes': {'tg__0': {
            'interfaces': {'xe0': {
                'local_ip': '10.1.1.1',
                'netmask': '255.255.255.0'
                }}}}}

    def setUp(self):
        self._mock_IxNextgen = mock.patch.object(ixnet_api, 'IxNextgen')
        self.mock_IxNextgen = self._mock_IxNextgen.start()
        self.scenario = tg_rfc2544_ixia.IxiaPppoeClientScenario(
            self.mock_IxNextgen, self.CONTEXT_CFG, self.IXIA_CFG)
        tg_rfc2544_ixia.WAIT_PROTOCOLS_STARTED = 2
        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_IxNextgen.stop()

    def test___init___(self):
        self.assertIsInstance(self.scenario, tg_rfc2544_ixia.IxiaPppoeClientScenario)
        self.assertEqual(self.scenario.client, self.mock_IxNextgen)

    @mock.patch.object(tg_rfc2544_ixia.IxiaPppoeClientScenario,
                       '_fill_ixia_config')
    @mock.patch.object(tg_rfc2544_ixia.IxiaPppoeClientScenario,
                       '_apply_access_network_config')
    @mock.patch.object(tg_rfc2544_ixia.IxiaPppoeClientScenario,
                       '_apply_core_network_config')
    def test_apply_config(self, mock_apply_core_net_cfg,
                          mock_apply_access_net_cfg,
                          mock_fill_ixia_config):
        self.mock_IxNextgen.get_vports.return_value = [1, 2, 3, 4]
        self.scenario.apply_config()
        self.scenario.client.get_vports.assert_called_once()
        self.assertEqual(self.scenario._uplink_vports, [1, 3])
        self.assertEqual(self.scenario._downlink_vports, [2, 4])
        mock_fill_ixia_config.assert_called_once()
        mock_apply_core_net_cfg.assert_called_once()
        mock_apply_access_net_cfg.assert_called_once()

    @mock.patch.object(tg_rfc2544_ixia.IxiaPppoeClientScenario,
                       '_get_endpoints_src_dst_id_pairs')
    @mock.patch.object(tg_rfc2544_ixia.IxiaPppoeClientScenario,
                       '_get_endpoints_src_dst_obj_pairs')
    def test_create_traffic_model(self, mock_obj_pairs, mock_id_pairs):
        uplink_endpoints = ['group1', 'group2']
        downlink_endpoints = ['group3', 'group3']
        mock_id_pairs.return_value = ['xe0', 'xe1', 'xe0', 'xe1']
        mock_obj_pairs.return_value = ['group1', 'group3', 'group2', 'group3']
        mock_tp = mock.Mock()
        mock_tp.full_profile = {'uplink_0': 'data',
                                'downlink_0': 'data',
                                'uplink_1': 'data',
                                'downlink_1': 'data'
                                }
        self.scenario.create_traffic_model(mock_tp)
        mock_id_pairs.assert_called_once_with(mock_tp.full_profile)
        mock_obj_pairs.assert_called_once_with(['xe0', 'xe1', 'xe0', 'xe1'])
        self.scenario.client.create_ipv4_traffic_model.assert_called_once_with(
            uplink_endpoints, downlink_endpoints)

    @mock.patch.object(tg_rfc2544_ixia.IxiaPppoeClientScenario,
                       '_get_endpoints_src_dst_id_pairs')
    @mock.patch.object(tg_rfc2544_ixia.IxiaPppoeClientScenario,
                       '_get_endpoints_src_dst_obj_pairs')
    def test_create_traffic_model_topology_based_flows(self, mock_obj_pairs,
                                                       mock_id_pairs):
        uplink_topologies = ['topology1', 'topology3']
        downlink_topologies = ['topology2', 'topology4']
        mock_id_pairs.return_value = []
        mock_obj_pairs.return_value = []
        mock_tp = mock.Mock()
        mock_tp.full_profile = {'uplink_0': 'data',
                                'downlink_0': 'data',
                                'uplink_1': 'data',
                                'downlink_1': 'data'
                                }
        self.scenario._access_topologies = ['topology1', 'topology3']
        self.scenario._core_topologies = ['topology2', 'topology4']
        self.scenario.create_traffic_model(mock_tp)
        mock_id_pairs.assert_called_once_with(mock_tp.full_profile)
        mock_obj_pairs.assert_called_once_with([])
        self.scenario.client.create_ipv4_traffic_model.assert_called_once_with(
            uplink_topologies, downlink_topologies)

    def test__get_endpoints_src_dst_id_pairs(self):
        full_tp = OrderedDict([
            ('uplink_0', {'ipv4': {'port': 'xe0'}}),
            ('downlink_0', {'ipv4': {'port': 'xe1'}}),
            ('uplink_1', {'ipv4': {'port': 'xe0'}}),
            ('downlink_1', {'ipv4': {'port': 'xe3'}})])
        endpoints_src_dst_pairs = ['xe0', 'xe1', 'xe0', 'xe3']
        res = self.scenario._get_endpoints_src_dst_id_pairs(full_tp)
        self.assertEqual(res, endpoints_src_dst_pairs)

    def test__get_endpoints_src_dst_id_pairs_wrong_flows_number(self):
        full_tp = OrderedDict([
            ('uplink_0', {'ipv4': {'port': 'xe0'}}),
            ('downlink_0', {'ipv4': {'port': 'xe1'}}),
            ('uplink_1', {'ipv4': {'port': 'xe0'}})])
        with self.assertRaises(RuntimeError):
            self.scenario._get_endpoints_src_dst_id_pairs(full_tp)

    def test__get_endpoints_src_dst_id_pairs_no_port_key(self):
        full_tp = OrderedDict([
            ('uplink_0', {'ipv4': {'id': 1}}),
            ('downlink_0', {'ipv4': {'id': 2}})])
        self.assertEqual(
            self.scenario._get_endpoints_src_dst_id_pairs(full_tp), [])

    def test__get_endpoints_src_dst_obj_pairs_tp_with_port_key(self):
        endpoints_id_pairs = ['xe0', 'xe1',
                              'xe0', 'xe1',
                              'xe0', 'xe3',
                              'xe0', 'xe3']
        ixia_cfg = {
            'pppoe_client': {
                'sessions_per_port': 4,
                'sessions_per_svlan': 1
            },
            'flow': {
                'src_ip': [{'tg__0': 'xe0'}, {'tg__0': 'xe2'}],
                'dst_ip': [{'tg__0': 'xe1'}, {'tg__0': 'xe3'}]
            }
        }

        expected_result = ['tp1_dg1', 'tp3_dg1', 'tp1_dg2', 'tp3_dg1',
                           'tp1_dg3', 'tp4_dg1', 'tp1_dg4', 'tp4_dg1']

        self.scenario._ixia_cfg = ixia_cfg
        self.scenario._access_topologies = ['topology1', 'topology2']
        self.scenario._core_topologies = ['topology3', 'topology4']
        self.mock_IxNextgen.get_topology_device_groups.side_effect = \
            [['tp1_dg1', 'tp1_dg2', 'tp1_dg3', 'tp1_dg4'],
             ['tp2_dg1', 'tp2_dg2', 'tp2_dg3', 'tp2_dg4'],
             ['tp3_dg1'],
             ['tp4_dg1']]
        res = self.scenario._get_endpoints_src_dst_obj_pairs(
            endpoints_id_pairs)
        self.assertEqual(res, expected_result)

    def test__get_endpoints_src_dst_obj_pairs_default_flows_mapping(self):
        endpoints_id_pairs = []
        ixia_cfg = {
            'pppoe_client': {
                'sessions_per_port': 4,
                'sessions_per_svlan': 1
            },
            'flow': {
                'src_ip': [{'tg__0': 'xe0'}, {'tg__0': 'xe2'}],
                'dst_ip': [{'tg__0': 'xe1'}, {'tg__0': 'xe3'}]
            }
        }

        self.scenario._ixia_cfg = ixia_cfg
        res = self.scenario._get_endpoints_src_dst_obj_pairs(
            endpoints_id_pairs)
        self.assertEqual(res, [])

    def test_run_protocols(self):
        self.scenario.client.is_protocols_running.return_value = True
        self.scenario.run_protocols()
        self.scenario.client.start_protocols.assert_called_once()

    def test_run_protocols_timeout_exception(self):
        self.scenario.client.is_protocols_running.return_value = False
        with self.assertRaises(exceptions.WaitTimeout):
            self.scenario.run_protocols()
        self.scenario.client.start_protocols.assert_called_once()

    def test_stop_protocols(self):
        self.scenario.stop_protocols()
        self.scenario.client.stop_protocols.assert_called_once()

    def test__get_intf_addr_str_type_input(self):
        intf = '192.168.10.2/24'
        ip, mask = self.scenario._get_intf_addr(intf)
        self.assertEqual(ip, '192.168.10.2')
        self.assertEqual(mask, 24)

    def test__get_intf_addr_dict_type_input(self):
        intf = {'tg__0': 'xe0'}
        ip, mask = self.scenario._get_intf_addr(intf)
        self.assertEqual(ip, '10.1.1.1')
        self.assertEqual(mask, 24)

    @mock.patch.object(tg_rfc2544_ixia.IxiaPppoeClientScenario, '_get_intf_addr')
    def test__fill_ixia_config(self, mock_get_intf_addr):

        ixia_cfg = {
            'pppoe_client': {
                'sessions_per_port': 4,
                'sessions_per_svlan': 1,
                's_vlan': 10,
                'c_vlan': 20,
                'ip': ['10.3.3.1/24', '10.4.4.1/24']
            },
            'ipv4_client': {
                'sessions_per_port': 1,
                'sessions_per_vlan': 1,
                'vlan': 101,
                'gateway_ip': ['10.1.1.1/24', '10.2.2.1/24'],
                'ip': ['10.1.1.1/24', '10.2.2.1/24']
            }
        }

        mock_get_intf_addr.side_effect = [
            ('10.3.3.1', '24'),
            ('10.4.4.1', '24'),
            ('10.1.1.1', '24'),
            ('10.2.2.1', '24'),
            ('10.1.1.1', '24'),
            ('10.2.2.1', '24')
        ]
        self.scenario._ixia_cfg = ixia_cfg
        self.scenario._fill_ixia_config()
        self.assertEqual(mock_get_intf_addr.call_count, 6)
        self.assertEqual(self.scenario._ixia_cfg['pppoe_client']['ip'],
                         ['10.3.3.1', '10.4.4.1'])
        self.assertEqual(self.scenario._ixia_cfg['ipv4_client']['ip'],
                         ['10.1.1.1', '10.2.2.1'])
        self.assertEqual(self.scenario._ixia_cfg['ipv4_client']['prefix'],
                         ['24', '24'])

    @mock.patch('yardstick.network_services.libs.ixia_libs.ixnet.ixnet_api.Vlan')
    def test__apply_access_network_config_pap_auth(self, mock_vlan):
        _ixia_cfg = {
            'pppoe_client': {
                'sessions_per_port': 4,
                'sessions_per_svlan': 1,
                's_vlan': 10,
                'c_vlan': 20,
                'pap_user': 'test_pap',
                'pap_password': 'pap'
                }}
        pap_user = _ixia_cfg['pppoe_client']['pap_user']
        pap_passwd = _ixia_cfg['pppoe_client']['pap_password']
        self.scenario._ixia_cfg = _ixia_cfg
        self.scenario._uplink_vports = [0, 2]
        self.scenario.client.add_topology.side_effect = ['Topology 1', 'Topology 2']
        self.scenario.client.add_device_group.side_effect = ['Dg1', 'Dg2', 'Dg3',
                                                             'Dg4', 'Dg5', 'Dg6',
                                                             'Dg7', 'Dg8']
        self.scenario.client.add_ethernet.side_effect = ['Eth1', 'Eth2', 'Eth3',
                                                         'Eth4', 'Eth5', 'Eth6',
                                                         'Eth7', 'Eth8']
        self.scenario._apply_access_network_config()
        self.assertEqual(self.scenario.client.add_topology.call_count, 2)
        self.assertEqual(self.scenario.client.add_device_group.call_count, 8)
        self.assertEqual(self.scenario.client.add_ethernet.call_count, 8)
        self.assertEqual(mock_vlan.call_count, 16)
        self.assertEqual(self.scenario.client.add_vlans.call_count, 8)
        self.assertEqual(self.scenario.client.add_pppox_client.call_count, 8)
        self.scenario.client.add_topology.assert_has_calls([
            mock.call('Topology access 0', 0),
            mock.call('Topology access 1', 2)
        ])
        self.scenario.client.add_device_group.assert_has_calls([
            mock.call('Topology 1', 'SVLAN 10', 1),
            mock.call('Topology 1', 'SVLAN 11', 1),
            mock.call('Topology 1', 'SVLAN 12', 1),
            mock.call('Topology 1', 'SVLAN 13', 1),
            mock.call('Topology 2', 'SVLAN 14', 1),
            mock.call('Topology 2', 'SVLAN 15', 1),
            mock.call('Topology 2', 'SVLAN 16', 1),
            mock.call('Topology 2', 'SVLAN 17', 1)
        ])
        self.scenario.client.add_ethernet.assert_has_calls([
            mock.call('Dg1', 'Ethernet'),
            mock.call('Dg2', 'Ethernet'),
            mock.call('Dg3', 'Ethernet'),
            mock.call('Dg4', 'Ethernet'),
            mock.call('Dg5', 'Ethernet'),
            mock.call('Dg6', 'Ethernet'),
            mock.call('Dg7', 'Ethernet'),
            mock.call('Dg8', 'Ethernet')
        ])
        mock_vlan.assert_has_calls([
            mock.call(vlan_id=10),
            mock.call(vlan_id=20, vlan_id_step=1),
            mock.call(vlan_id=11),
            mock.call(vlan_id=20, vlan_id_step=1),
            mock.call(vlan_id=12),
            mock.call(vlan_id=20, vlan_id_step=1),
            mock.call(vlan_id=13),
            mock.call(vlan_id=20, vlan_id_step=1),
            mock.call(vlan_id=14),
            mock.call(vlan_id=20, vlan_id_step=1),
            mock.call(vlan_id=15),
            mock.call(vlan_id=20, vlan_id_step=1),
            mock.call(vlan_id=16),
            mock.call(vlan_id=20, vlan_id_step=1),
            mock.call(vlan_id=17),
            mock.call(vlan_id=20, vlan_id_step=1)
        ])
        self.scenario.client.add_pppox_client.assert_has_calls([
            mock.call('Eth1', 'pap', pap_user, pap_passwd),
            mock.call('Eth2', 'pap', pap_user, pap_passwd),
            mock.call('Eth3', 'pap', pap_user, pap_passwd),
            mock.call('Eth4', 'pap', pap_user, pap_passwd),
            mock.call('Eth5', 'pap', pap_user, pap_passwd),
            mock.call('Eth6', 'pap', pap_user, pap_passwd),
            mock.call('Eth7', 'pap', pap_user, pap_passwd),
            mock.call('Eth8', 'pap', pap_user, pap_passwd)
        ])

    def test__apply_access_network_config_chap_auth(self):
        _ixia_cfg = {
            'pppoe_client': {
                'sessions_per_port': 4,
                'sessions_per_svlan': 1,
                's_vlan': 10,
                'c_vlan': 20,
                'chap_user': 'test_chap',
                'chap_password': 'chap'
            }}
        chap_user = _ixia_cfg['pppoe_client']['chap_user']
        chap_passwd = _ixia_cfg['pppoe_client']['chap_password']
        self.scenario._ixia_cfg = _ixia_cfg
        self.scenario._uplink_vports = [0, 2]
        self.scenario.client.add_ethernet.side_effect = ['Eth1', 'Eth2', 'Eth3',
                                                         'Eth4', 'Eth5', 'Eth6',
                                                         'Eth7', 'Eth8']
        self.scenario._apply_access_network_config()
        self.assertEqual(self.scenario.client.add_pppox_client.call_count, 8)
        self.scenario.client.add_pppox_client.assert_has_calls([
            mock.call('Eth1', 'chap', chap_user, chap_passwd),
            mock.call('Eth2', 'chap', chap_user, chap_passwd),
            mock.call('Eth3', 'chap', chap_user, chap_passwd),
            mock.call('Eth4', 'chap', chap_user, chap_passwd),
            mock.call('Eth5', 'chap', chap_user, chap_passwd),
            mock.call('Eth6', 'chap', chap_user, chap_passwd),
            mock.call('Eth7', 'chap', chap_user, chap_passwd),
            mock.call('Eth8', 'chap', chap_user, chap_passwd)
        ])

    @mock.patch('yardstick.network_services.libs.ixia_libs.ixnet.ixnet_api.Vlan')
    def test__apply_core_network_config_no_bgp_proto(self, mock_vlan):
        self.scenario._downlink_vports = [1, 3]
        self.scenario.client.add_topology.side_effect = ['Topology 1', 'Topology 2']
        self.scenario.client.add_device_group.side_effect = ['Dg1', 'Dg2']
        self.scenario.client.add_ethernet.side_effect = ['Eth1', 'Eth2']
        self.scenario._apply_core_network_config()
        self.assertEqual(self.scenario.client.add_topology.call_count, 2)
        self.assertEqual(self.scenario.client.add_device_group.call_count, 2)
        self.assertEqual(self.scenario.client.add_ethernet.call_count, 2)
        self.assertEqual(mock_vlan.call_count, 2)
        self.assertEqual(self.scenario.client.add_vlans.call_count, 2)
        self.assertEqual(self.scenario.client.add_ipv4.call_count, 2)
        self.scenario.client.add_topology.assert_has_calls([
            mock.call('Topology core 0', 1),
            mock.call('Topology core 1', 3)
        ])
        self.scenario.client.add_device_group.assert_has_calls([
            mock.call('Topology 1', 'Core port 0', 1),
            mock.call('Topology 2', 'Core port 1', 1)
        ])
        self.scenario.client.add_ethernet.assert_has_calls([
            mock.call('Dg1', 'Ethernet'),
            mock.call('Dg2', 'Ethernet')
        ])
        mock_vlan.assert_has_calls([
            mock.call(vlan_id=101),
            mock.call(vlan_id=102)
        ])
        self.scenario.client.add_ipv4.assert_has_calls([
            mock.call('Eth1', name='ipv4', addr=ipaddress.IPv4Address('10.1.1.2'),
                      addr_step='0.0.0.1', prefix='24', gateway='10.1.1.1'),
            mock.call('Eth2', name='ipv4', addr=ipaddress.IPv4Address('10.2.2.2'),
                      addr_step='0.0.0.1', prefix='24', gateway='10.2.2.1')
        ])
        self.scenario.client.add_bgp.assert_not_called()

    def test__apply_core_network_config_with_bgp_proto(self):
        bgp_params = {
            'bgp': {
                'bgp_type': 'external',
                'dut_ip': '10.0.0.1',
                'as_number': 65000
            }
        }
        self.scenario._ixia_cfg['ipv4_client'].update(bgp_params)
        self.scenario._downlink_vports = [1, 3]
        self.scenario.client.add_ipv4.side_effect = ['ipv4_1', 'ipv4_2']
        self.scenario._apply_core_network_config()
        self.assertEqual(self.scenario.client.add_bgp.call_count, 2)
        self.scenario.client.add_bgp.assert_has_calls([
            mock.call('ipv4_1', dut_ip=bgp_params["bgp"]["dut_ip"],
                      local_as=bgp_params["bgp"]["as_number"],
                      bgp_type=bgp_params["bgp"]["bgp_type"]),
            mock.call('ipv4_2', dut_ip=bgp_params["bgp"]["dut_ip"],
                      local_as=bgp_params["bgp"]["as_number"],
                      bgp_type=bgp_params["bgp"]["bgp_type"])
        ])

    def test_update_tracking_options_raw_priority(self):
        raw_priority = {'raw': 4}
        self.scenario._ixia_cfg['priority'] = raw_priority
        self.scenario.update_tracking_options()
        self.scenario.client.set_flow_tracking.assert_called_once_with(
            ['flowGroup0', 'vlanVlanId0', 'ipv4Raw0'])

    def test_update_tracking_options_tos_priority(self):
        tos_priority = {'tos': {'precedence': [4, 7]}}
        self.scenario._ixia_cfg['priority'] = tos_priority
        self.scenario.update_tracking_options()
        self.scenario.client.set_flow_tracking.assert_called_once_with(
            ['flowGroup0', 'vlanVlanId0', 'ipv4Precedence0'])

    def test_update_tracking_options_dscp_priority(self):
        dscp_priority = {'dscp': {'defaultPHB': [4, 7]}}
        self.scenario._ixia_cfg['priority'] = dscp_priority
        self.scenario.update_tracking_options()
        self.scenario.client.set_flow_tracking.assert_called_once_with(
            ['flowGroup0', 'vlanVlanId0', 'ipv4DefaultPhb0'])

    def test_update_tracking_options_invalid_priority_data(self):
        invalid_priority = {'tos': {'inet-precedence': [4, 7]}}
        self.scenario._ixia_cfg['priority'] = invalid_priority
        self.scenario.update_tracking_options()
        self.scenario.client.set_flow_tracking.assert_called_once_with(
            ['flowGroup0', 'vlanVlanId0', 'ipv4Precedence0'])

    def test_get_tc_rfc2544_options(self):
        rfc2544_tc_opts = {'allowed_drop_rate': '0.0001 - 0.0001'}
        self.scenario._ixia_cfg['rfc2544'] = rfc2544_tc_opts
        res = self.scenario.get_tc_rfc2544_options()
        self.assertEqual(res, rfc2544_tc_opts)

    def test__get_stats(self):
        self.scenario._get_stats()
        self.scenario.client.get_pppoe_scenario_statistics.assert_called_once()

    def test_get_flow_id_data(self):
        stats = [{'id': 1, 'in_packets': 10, 'out_packets': 20}]
        key = "in_packets"
        flow_id = 1
        res = self.scenario.get_flow_id_data(stats, flow_id, key)
        self.assertEqual(res, 10)

    @mock.patch.object(tg_rfc2544_ixia.IxiaPppoeClientScenario, '_get_stats')
    @mock.patch.object(tg_rfc2544_ixia.IxiaPppoeClientScenario,
                       'get_priority_flows_stats')
    def test_generate_samples(self, mock_prio_flow_statistics,
                              mock_get_stats):
        ixia_stats = {
            'flow_statistic': [
                {'Flow_Group': 'RFC2544-1 - Flow Group 0001',
                 'Frames_Delta': '0',
                 'IP_Priority': '0',
                 'Rx_Frames': '3000',
                 'Tx_Frames': '3000',
                 'VLAN-ID': '100',
                 'Tx_Port': 'Ethernet - 001',
                 'Store-Forward_Avg_latency_ns': '2',
                 'Store-Forward_Min_latency_ns': '2',
                 'Store-Forward_Max_latency_ns': '2'},
                {'Flow_Group': 'RFC2544-2 - Flow Group 0001',
                 'Frames_Delta': '0',
                 'IP_Priority': '0',
                 'Rx_Frames': '3000',
                 'Tx_Frames': '3000',
                 'VLAN-ID': '101',
                 'Tx_Port': 'Ethernet - 002',
                 'Store-Forward_Avg_latency_ns': '2',
                 'Store-Forward_Min_latency_ns': '2',
                 'Store-Forward_Max_latency_ns': '2'
                 }],
            'port_statistics': [
                {'Frames_Tx': '3000',
                 'Valid_Frames_Rx': '3000',
                 'Bytes_Rx': '192000',
                 'Bytes_Tx': '192000',
                 'Rx_Rate_Kbps': '0.0',
                 'Tx_Rate_Kbps': '0.0',
                 'Rx_Rate_Mbps': '0.0',
                 'Tx_Rate_Mbps': '0.0',
                 'port_name': 'Ethernet - 001'},
                {'Frames_Tx': '3000',
                 'Valid_Frames_Rx': '3000',
                 'Bytes_Rx': '192000',
                 'Bytes_Tx': '192000',
                 'Rx_Rate_Kbps': '0.0',
                 'Tx_Rate_Kbps': '0.0',
                 'Rx_Rate_Mbps': '0.0',
                 'Tx_Rate_Mbps': '0.0',
                 'port_name': 'Ethernet - 002'}],
            'pppox_client_per_port': [
                {'Sessions_Down': '0',
                 'Sessions_Not_Started': '0',
                 'Sessions_Total': '1',
                 'Sessions_Up': '1',
                 'subs_port': 'Ethernet - 001'}]}

        prio_flows_stats = {
            '0': {
                'in_packets': 6000,
                'out_packets': 6000,
                'RxThroughput': 200.0,
                'TxThroughput': 200.0,
                'avg_latency_ns': 2,
                'max_latency_ns': 2,
                'min_latency_ns': 2
            }
        }

        expected_result = {'priority_stats': {
            '0': {'RxThroughput': 200.0,
                  'TxThroughput': 200.0,
                  'avg_latency_ns': 2,
                  'max_latency_ns': 2,
                  'min_latency_ns': 2,
                  'in_packets': 6000,
                  'out_packets': 6000}},
            'xe0': {'RxThroughput': 100.0,
                    'Store-Forward_Avg_latency_ns': 2,
                    'Store-Forward_Max_latency_ns': 2,
                    'Store-Forward_Min_latency_ns': 2,
                    'TxThroughput': 100.0,
                    'in_packets': 3000,
                    'out_packets': 3000,
                    'in_bytes': 192000,
                    'out_bytes': 192000,
                    'RxThroughputBps': 6400.0,
                    'TxThroughputBps': 6400.0,
                    'rx_throughput_kps': 0.0,
                    'rx_throughput_mbps': 0.0,
                    'sessions_down': 0,
                    'sessions_not_started': 0,
                    'sessions_total': 1,
                    'sessions_up': 1,
                    'tx_throughput_kps': 0.0,
                    'tx_throughput_mbps': 0.0},
            'xe1': {'RxThroughput': 100.0,
                    'Store-Forward_Avg_latency_ns': 2,
                    'Store-Forward_Max_latency_ns': 2,
                    'Store-Forward_Min_latency_ns': 2,
                    'TxThroughput': 100.0,
                    'in_packets': 3000,
                    'out_packets': 3000,
                    'in_bytes': 192000,
                    'out_bytes': 192000,
                    'RxThroughputBps': 6400.0,
                    'TxThroughputBps': 6400.0,
                    'rx_throughput_kps': 0.0,
                    'rx_throughput_mbps': 0.0,
                    'tx_throughput_kps': 0.0,
                    'tx_throughput_mbps': 0.0}}

        mock_get_stats.return_value = ixia_stats
        mock_prio_flow_statistics.return_value = prio_flows_stats
        ports = [0, 1]
        port_names = [{'name': 'xe0'}, {'name': 'xe1'}]
        duration = 30
        res_helper = mock.Mock()
        res_helper.vnfd_helper.find_interface_by_port.side_effect = \
            port_names
        samples = self.scenario.generate_samples(res_helper, ports, duration)
        self.assertIsNotNone(samples)
        self.assertIsNotNone(samples.get('xe0'))
        self.assertIsNotNone(samples.get('xe1'))
        self.assertEqual(samples, expected_result)
        mock_get_stats.assert_called_once()
        mock_prio_flow_statistics.assert_called_once()
