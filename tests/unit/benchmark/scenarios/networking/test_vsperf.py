#!/usr/bin/env python

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

import mock
import unittest
import os
import subprocess

from yardstick.benchmark.scenarios.networking import vsperf


@mock.patch('yardstick.benchmark.scenarios.networking.vsperf.subprocess')
@mock.patch('yardstick.benchmark.scenarios.networking.vsperf.ssh')
@mock.patch("__builtin__.open", return_value=None)
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
                'testname': 'rfc2544_p2p_continuous',
                'traffic_type': 'continuous',
                'pkt_sizes': '64',
                'bidirectional': 'True',
                'iload': 100,
                'duration': 29,
                'trafficgen_port1': 'eth1',
                'trafficgen_port2': 'eth3',
                'external_bridge': 'br-ex',
                'conf-file': 'vsperf-yardstick.conf',
                'setup-script': 'setup_yardstick.sh',
            },
            'sla': {
                'metrics': 'throughput_rx_fps',
                'throughput_rx_fps': 500000,
                'action': 'monitor',
            }
        }

    def test_vsperf_setup(self, mock_open, mock_ssh, mock_subprocess):
        p = vsperf.Vsperf(self.args, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

    def test_vsperf_teardown(self, mock_open, mock_ssh, mock_subprocess):
        p = vsperf.Vsperf(self.args, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

        p.teardown()
        self.assertEqual(p.setup_done, False)

    def test_vsperf_run_ok(self, mock_open, mock_ssh, mock_subprocess):
        p = vsperf.Vsperf(self.args, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        # run() specific mocks
        mock_ssh.SSH().execute.return_value = (0, '', '')
        mock_ssh.SSH().execute.return_value = (0, 'throughput_rx_fps\r\n14797660.000\r\n', '')

        result = {}
        p.run(result)

        self.assertEqual(result['throughput_rx_fps'], '14797660.000')

    def test_vsperf_run_falied_vsperf_execution(self, mock_open, mock_ssh, mock_subprocess):
        p = vsperf.Vsperf(self.args, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        # run() specific mocks
        mock_ssh.SSH().execute.return_value = (1, '', '')

        result = {}
        self.assertRaises(RuntimeError, p.run, result)

    def test_vsperf_run_falied_csv_report(self, mock_open, mock_ssh, mock_subprocess):
        p = vsperf.Vsperf(self.args, self.ctx)

        # setup() specific mocks
        mock_ssh.SSH().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        # run() specific mocks
        mock_ssh.SSH().execute.return_value = (0, '', '')
        mock_ssh.SSH().execute.return_value = (1, '', '')

        result = {}
        self.assertRaises(RuntimeError, p.run, result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
