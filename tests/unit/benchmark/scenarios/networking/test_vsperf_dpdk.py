#!/usr/bin/env python

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

# Unittest for yardstick.benchmark.scenarios.networking.vsperf.VsperfDPDK

from __future__ import absolute_import
try:
    from unittest import mock
except ImportError:
    import mock
import unittest

from yardstick.benchmark.scenarios.networking import vsperf_dpdk


@mock.patch('yardstick.benchmark.scenarios.networking.vsperf_dpdk.subprocess')
@mock.patch('yardstick.benchmark.scenarios.networking.vsperf_dpdk.ssh')
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

    def test_vsperf_dpdk_setup(self, mock_ssh, mock_subprocess):
        p = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

    def test_vsperf_dpdk_teardown(self, mock_ssh, mock_subprocess):
        p = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

        p.teardown()
        self.assertEqual(p.setup_done, False)

    def test_vsperf_dpdk_is_dpdk_setup_no(self, mock_ssh, mock_subprocess):
        p = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

        # is_dpdk_setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, 'dummy', '')

        result = p._is_dpdk_setup()
        self.assertEqual(result, False)

    def test_vsperf_dpdk_is_dpdk_setup_yes(self, mock_ssh, mock_subprocess):
        p = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

        # is_dpdk_setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        result = p._is_dpdk_setup()
        self.assertEqual(result, True)

    def test_vsperf_dpdk_dpdk_setup_first(self, mock_ssh, mock_subprocess):
        p = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

        # is_dpdk_setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, 'dummy', '')

        p.dpdk_setup()
        self.assertEqual(p._is_dpdk_setup(), False)
        self.assertEqual(p.dpdk_setup_done, True)

    def test_vsperf_dpdk_dpdk_setup_next(self, mock_ssh, mock_subprocess):
        p = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

        # dpdk_setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        p.dpdk_setup()
        self.assertEqual(p._is_dpdk_setup(), True)
        self.assertEqual(p.dpdk_setup_done, True)

    def test_vsperf_dpdk_dpdk_setup_fail(self, mock_ssh, mock_subprocess):
        p = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

        # dpdk_setup() specific mocks
        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p.dpdk_setup)

    def test_vsperf_dpdk_run_ok(self, mock_ssh, mock_subprocess):
        p = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

        # run() specific mocks
        mock_subprocess.call().execute.return_value = None
        mock_subprocess.call().execute.return_value = None
        mock_ssh.SSH.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n14797660.000\r\n', '')

        result = {}
        p.run(result)

        self.assertEqual(result['throughput_rx_fps'], '14797660.000')

    def test_vsperf_dpdk_run_falied_vsperf_execution(self, mock_ssh,
                                                mock_subprocess):
        p = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

        # run() specific mocks
        mock_subprocess.call().execute.return_value = None
        mock_subprocess.call().execute.return_value = None
        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        result = {}
        self.assertRaises(RuntimeError, p.run, result)

    def test_vsperf_dpdk_run_falied_csv_report(self, mock_ssh, mock_subprocess):
        p = vsperf_dpdk.VsperfDPDK(self.args, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

        # run() specific mocks
        mock_subprocess.call().execute.return_value = None
        mock_subprocess.call().execute.return_value = None
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        result = {}
        self.assertRaises(RuntimeError, p.run, result)

def main():
    unittest.main()


if __name__ == '__main__':
    main()
