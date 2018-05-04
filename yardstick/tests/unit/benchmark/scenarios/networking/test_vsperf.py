# Copyright 2016 Intel Corporation.
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

# Unittest for yardstick.benchmark.scenarios.networking.vsperf.Vsperf

from __future__ import absolute_import
try:
    from unittest import mock
except ImportError:
    import mock
import unittest

from yardstick.benchmark.scenarios.networking import vsperf
from yardstick import exceptions as y_exc


@mock.patch('yardstick.benchmark.scenarios.networking.vsperf.subprocess')
@mock.patch('yardstick.benchmark.scenarios.networking.vsperf.ssh')
class VsperfTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            "host": {
                "ip": "10.229.47.137",
                "user": "ubuntu",
                "password": "ubuntu",
            },
        }
        self.args = {
            'options': {
                'testname': 'p2p_rfc2544_continuous',
                'traffic_type': 'continuous',
                'frame_size': '64',
                'bidirectional': 'True',
                'iload': 100,
                'trafficgen_port1': 'eth1',
                'trafficgen_port2': 'eth3',
                'external_bridge': 'br-ex',
                'conf_file': 'vsperf-yardstick.conf',
                'setup_script': 'setup_yardstick.sh',
                'test_params': 'TRAFFICGEN_DURATION=30;',
            },
            'sla': {
                'metrics': 'throughput_rx_fps',
                'throughput_rx_fps': 500000,
                'action': 'monitor',
            }
        }

    def test_vsperf_setup(self, mock_ssh, mock_subprocess):
        p = vsperf.Vsperf(self.args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

    def test_vsperf_teardown(self, mock_ssh, mock_subprocess):
        p = vsperf.Vsperf(self.args, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        p.teardown()
        self.assertFalse(p.setup_done)

    def test_vsperf_run_ok(self, mock_ssh, mock_subprocess):
        p = vsperf.Vsperf(self.args, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        # run() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_ssh.SSH.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n14797660.000\r\n', '')

        result = {}
        p.run(result)

        self.assertEqual(result['throughput_rx_fps'], '14797660.000')

    def test_vsperf_run_falied_vsperf_execution(self, mock_ssh,
                                                mock_subprocess):
        p = vsperf.Vsperf(self.args, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        # run() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        result = {}
        self.assertRaises(RuntimeError, p.run, result)

    def test_vsperf_run_falied_csv_report(self, mock_ssh, mock_subprocess):
        p = vsperf.Vsperf(self.args, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        # run() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        result = {}
        self.assertRaises(RuntimeError, p.run, result)

    def test_vsperf_run_sla_fail(self, mock_ssh, *args):
        p = vsperf.Vsperf(self.args, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        # run() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_ssh.SSH.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n123456.000\r\n', '')

        result = {}
        with self.assertRaises(y_exc.SLAValidationError) as raised:
            p.run(result)

        self.assertTrue('VSPERF_throughput_rx_fps(123456.000000) < '
                        'SLA_throughput_rx_fps(500000.000000)'
                        in str(raised.exception))

    def test_vsperf_run_sla_fail_metric_not_collected(self, mock_ssh, *args):
        p = vsperf.Vsperf(self.args, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        # run() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_ssh.SSH.from_node().execute.return_value = (
            0, 'nonexisting_metric\r\n14797660.000\r\n', '')

        result = {}
        with self.assertRaises(y_exc.SLAValidationError) as raised:
            p.run(result)

        self.assertTrue('throughput_rx_fps was not collected by VSPERF'
                        in str(raised.exception))

    def test_vsperf_run_sla_fail_metric_not_defined_in_sla(self, mock_ssh,
                                                           *args):
        sample_scenario_cfg = self.args.copy()
        del sample_scenario_cfg['sla']['throughput_rx_fps']
        p = vsperf.Vsperf(sample_scenario_cfg, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        # run() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_ssh.SSH.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n14797660.000\r\n', '')

        result = {}
        with self.assertRaises(y_exc.SLAValidationError) as raised:
            p.run(result)

        self.assertTrue('throughput_rx_fps is not defined in SLA'
                        in str(raised.exception))
