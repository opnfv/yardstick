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

from yardstick import exceptions as y_exc
from yardstick.benchmark.scenarios.networking import vsperf_dpdk
from yardstick.common import exceptions as y_exc
from yardstick import ssh


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
        self._mock_ssh = mock.patch.object(ssh, 'SSH')
        self.mock_ssh = self._mock_ssh.start()
        self._mock_subprocess_call = mock.patch.object(subprocess, 'call')
        self.mock_subprocess_call = self._mock_subprocess_call.start()
        mock_call_obj = mock.Mock()
        mock_call_obj.execute.return_value = None
        self.mock_subprocess_call.return_value = mock_call_obj

        self._mock_log_info = mock.patch.object(vsperf_dpdk.LOG, 'info')
        self.mock_log_info = self._mock_log_info.start()

        self.addCleanup(self._cleanup)

        self.scenario = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)
        self.scenario.setup()

    def _cleanup(self):
        self._mock_ssh.stop()
        self._mock_subprocess_call.stop()
        self._mock_log_info.stop()

    def test_setup(self):
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

    def test_teardown(self):
        self.scenario.teardown()
        self.assertFalse(self.scenario.setup_done)

    def test_is_dpdk_setup_no(self):
        # is_dpdk_setup() specific mocks
        self.mock_ssh.from_node().execute.return_value = (0, 'dummy', '')

        self.assertFalse(self.scenario._is_dpdk_setup())

    def test_is_dpdk_setup_yes(self):
        # is_dpdk_setup() specific mocks
        self.mock_ssh.from_node().execute.return_value = (0, '', '')

        self.assertTrue(self.scenario._is_dpdk_setup())

    @mock.patch.object(time, 'sleep')
    def test_dpdk_setup_first(self, *args):
        # is_dpdk_setup() specific mocks
        self.mock_ssh.from_node().execute.return_value = (0, 'dummy', '')

        self.scenario.dpdk_setup()
        self.assertFalse(self.scenario._is_dpdk_setup())
        self.assertTrue(self.scenario.dpdk_setup_done)

    @mock.patch.object(time, 'sleep')
    def test_dpdk_setup_next(self, *args):
        self.mock_ssh.from_node().execute.return_value = (0, '', '')

        self.scenario.dpdk_setup()
        self.assertTrue(self.scenario._is_dpdk_setup())
        self.assertTrue(self.scenario.dpdk_setup_done)

    @mock.patch.object(subprocess, 'check_output')
    def test_run_ok(self, *args):
        # run() specific mocks
        self.mock_ssh.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n14797660.000\r\n', '')

        result = {}
        self.scenario.run(result)
        self.assertEqual(result['throughput_rx_fps'], '14797660.000')

    @mock.patch.object(time, 'sleep')
    @mock.patch.object(subprocess, 'check_output')
    def test_vsperf_run_sla_fail(self, *args):
        self.mock_ssh.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n123456.000\r\n', '')

        with self.assertRaises(y_exc.SLAValidationError) as raised:
            self.scenario.run({})

        self.assertIn('VSPERF_throughput_rx_fps(123456.000000) < '
                      'SLA_throughput_rx_fps(500000.000000)',
                      str(raised.exception))

    @mock.patch.object(time, 'sleep')
    @mock.patch.object(subprocess, 'check_output')
    def test_vsperf_run_sla_fail_metric_not_collected(self, *args):
        self.mock_ssh.from_node().execute.return_value = (
            0, 'nonexisting_metric\r\n123456.000\r\n', '')

        with self.assertRaises(y_exc.SLAValidationError) as raised:
            self.scenario.run({})

        self.assertIn('throughput_rx_fps was not collected by VSPERF',
                      str(raised.exception))

    @mock.patch.object(time, 'sleep')
    @mock.patch.object(subprocess, 'check_output')
    def test_vsperf_run_sla_fail_metric_not_collected_faulty_csv(self, *args):
        self.scenario.setup()

        self.mock_ssh.from_node().execute.return_value = (
            0, 'faulty output not csv', '')

        with self.assertRaises(y_exc.SLAValidationError) as raised:
            self.scenario.run({})

        self.assertIn('throughput_rx_fps was not collected by VSPERF',
                      str(raised.exception))

    @mock.patch.object(time, 'sleep')
    @mock.patch.object(subprocess, 'check_output')
    def test_vsperf_run_sla_fail_sla_not_defined(self, *args):
        del self.scenario.scenario_cfg['sla']['throughput_rx_fps']
        self.scenario.setup()

        self.mock_ssh.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n14797660.000\r\n', '')

        with self.assertRaises(y_exc.SLAValidationError) as raised:
            self.scenario.run({})

        self.assertIn('throughput_rx_fps is not defined in SLA',
                      str(raised.exception))
