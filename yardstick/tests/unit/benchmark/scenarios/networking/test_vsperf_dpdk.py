# Copyright 2017 Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import time

import mock
import unittest

from yardstick.benchmark.scenarios.networking import vsperf_dpdk


class VsperfDPDKTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            "host": {
                "ip": "10.229.47.137",
                "user": "ubuntu",
                "password": "ubuntu",
            },
        }
        self.args = {
            'task_id': "1234-5678",
            'options': {
                'testname': 'pvp_tput',
                'traffic_type': 'rfc2544_throughput',
                'frame_size': '64',
                'test_params': 'TRAFFICGEN_DURATION=30;',
                'trafficgen_port1': 'ens4',
                'trafficgen_port2': 'ens5',
                'conf_file': 'vsperf-yardstick.conf',
                'setup_script': 'setup_yardstick.sh',
                'moongen_helper_file': '~/moongen.py',
                'moongen_host_ip': '10.5.201.151',
                'moongen_port1_mac': '8c:dc:d4:ae:7c:5c',
                'moongen_port2_mac': '8c:dc:d4:ae:7c:5d',
                'trafficgen_port1_nw': 'test2',
                'trafficgen_port2_nw': 'test3',
            },
            'sla': {
                'metrics': 'throughput_rx_fps',
                'throughput_rx_fps': 500000,
                'action': 'monitor',
            }
        }

        self.scenario = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        self._mock_ssh = mock.patch(
            'yardstick.benchmark.scenarios.networking.vsperf_dpdk.ssh')
        self.mock_ssh = self._mock_ssh.start()
        self._mock_subprocess_call = mock.patch.object(subprocess, 'call')
        self.mock_subprocess_call = self._mock_subprocess_call.start()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self._mock_ssh.stop()
        self._mock_subprocess_call.stop()

    def test_setup(self):
        # setup() specific mocks
        self.mock_subprocess_call().execute.return_value = None

        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

    def test_teardown(self):
        # setup() specific mocks
        self.mock_subprocess_call().execute.return_value = None

        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

        self.scenario.teardown()
        self.assertFalse(self.scenario.setup_done)

    def test_is_dpdk_setup_no(self):
        # setup() specific mocks
        self.mock_subprocess_call().execute.return_value = None

        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

        # is_dpdk_setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, 'dummy', '')

        result = self.scenario._is_dpdk_setup()
        self.assertFalse(result)

    def test_is_dpdk_setup_yes(self):
        # setup() specific mocks
        self.mock_subprocess_call().execute.return_value = None

        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

        # is_dpdk_setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        result = self.scenario._is_dpdk_setup()
        self.assertTrue(result)

    @mock.patch.object(time, 'sleep')
    def test_dpdk_setup_first(self, *args):
        # setup() specific mocks
        self.mock_subprocess_call().execute.return_value = None

        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

        # is_dpdk_setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, 'dummy', '')

        self.scenario.dpdk_setup()
        self.assertFalse(self.scenario._is_dpdk_setup())
        self.assertTrue(self.scenario.dpdk_setup_done)

    @mock.patch.object(time, 'sleep')
    def test_dpdk_setup_next(self, *args):
        # setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.mock_subprocess_call().execute.return_value = None

        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

        self.scenario.dpdk_setup()
        self.assertTrue(self.scenario._is_dpdk_setup())
        self.assertTrue(self.scenario.dpdk_setup_done)

    @mock.patch.object(time, 'sleep')
    def test_dpdk_setup_runtime_error(self, *args):

        # setup specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.mock_subprocess_call().execute.return_value = None

        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.mock_ssh.SSH.from_node().execute.return_value = (1, '', '')
        self.assertTrue(self.scenario.setup_done)

        self.assertRaises(RuntimeError, self.scenario.dpdk_setup)

    @mock.patch.object(subprocess, 'check_output')
    @mock.patch('time.sleep')
    def test_run_ok(self, *args):
        # setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.mock_subprocess_call().execute.return_value = None

        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

        # run() specific mocks
        self.mock_subprocess_call().execute.return_value = None
        self.mock_ssh.SSH.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n14797660.000\r\n', '')

        result = {}
        self.scenario.run(result)

        self.assertEqual(result['throughput_rx_fps'], '14797660.000')

    def test_run_failed_vsperf_execution(self):
        # setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.mock_subprocess_call().execute.return_value = None

        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

        self.mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        result = {}
        self.assertRaises(RuntimeError, self.scenario.run, result)

    def test_run_falied_csv_report(self):
        # setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.mock_subprocess_call().execute.return_value = None

        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

        # run() specific mocks
        self.mock_subprocess_call().execute.return_value = None
        self.mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        result = {}
        self.assertRaises(RuntimeError, self.scenario.run, result)
