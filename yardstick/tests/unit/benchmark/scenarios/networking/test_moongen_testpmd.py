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

# Unittest for yardstick.benchmark.scenarios.networking.MoongenTestPMD

from __future__ import absolute_import
try:
    from unittest import mock
except ImportError:
    import mock
import unittest

from yardstick.benchmark.scenarios.networking import moongen_testpmd


@mock.patch('yardstick.benchmark.scenarios.networking.moongen_testpmd.subprocess')
class MoongenTestPMDTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            "host": {
                "ip": "10.229.47.137",
                "user": "ubuntu",
                "password": "ubuntu",
            },
        }
        self.TestPMDargs = {
            'task_id': "1234-5678",
            'options': {
                'multistream': 1,
                'frame_size': 1024,
                'testpmd_queue': 2,
                'trafficgen_port1': 'ens5',
                'trafficgen_port2': 'ens6',
                'moongen_host_user': 'root',
                'moongen_host_passwd': 'root',
                'moongen_host_ip': '10.5.201.151',
                'moongen_dir': '/home/lua-trafficgen',
                'moongen_runBidirec': 'true',
                'Package_Loss': 0,
                'SearchRuntime': 60,
                'moongen_port1_mac': '88:cf:98:2f:4d:ed',
                'moongen_port2_mac': '88:cf:98:2f:4d:ee',
                'forward_type': 'testpmd',
            },
            'sla': {
                'metrics': 'throughput_rx_mpps',
                'throughput_rx_mpps': 0.5,
                'action': 'monitor',
            }
        }
        self.L2fwdargs = {
            'task_id': "1234-5678",
            'options': {
                'multistream': 1,
                'frame_size': 1024,
                'testpmd_queue': 2,
                'trafficgen_port1': 'ens5',
                'trafficgen_port2': 'ens6',
                'moongen_host_user': 'root',
                'moongen_host_passwd': 'root',
                'moongen_host_ip': '10.5.201.151',
                'moongen_dir': '/home/lua-trafficgen',
                'moongen_runBidirec': 'true',
                'Package_Loss': 0,
                'SearchRuntime': 60,
                'moongen_port1_mac': '88:cf:98:2f:4d:ed',
                'moongen_port2_mac': '88:cf:98:2f:4d:ee',
                'forward_type': 'l2fwd',
            },
            'sla': {
                'metrics': 'throughput_rx_mpps',
                'throughput_rx_mpps': 0.5,
                'action': 'monitor',
            }
        }

        self._mock_ssh = mock.patch(
            'yardstick.benchmark.scenarios.networking.moongen_testpmd.ssh')
        self.mock_ssh = self._mock_ssh.start()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self._mock_ssh.stop()

    def test_MoongenTestPMD_setup(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

    def test_MoongenTestPMD_teardown(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        p.teardown()
        self.assertFalse(p.setup_done)

    def test_MoongenTestPMD_l2fwd_is_forward_setup_no(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.L2fwdargs, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        # is_dpdk_setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        result = p._is_forward_setup()
        self.assertFalse(result)

    def test_MoongenTestPMD_l2fwd_is_forward_setup_yes(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.L2fwdargs, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        # is_dpdk_setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, 'dummy', '')

        result = p._is_forward_setup()
        self.assertTrue(result)

    def test_MoongenTestPMD_testpmd_is_forward_setup_no(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        # is_dpdk_setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, 'dummy', '')

        result = p._is_forward_setup()
        self.assertFalse(result)

    def test_MoongenTestPMD_testpmd_is_forward_setup_yes(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        # is_dpdk_setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        result = p._is_forward_setup()
        self.assertTrue(result)

    @mock.patch('time.sleep')
    def test_MoongenTestPMD_testpmd_forward_setup_first(self, _, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        # is_dpdk_setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, 'dummy', '')

        p.forward_setup()
        self.assertFalse(p._is_forward_setup())
        self.assertTrue(p.forward_setup_done)

    @mock.patch('time.sleep')
    def test_MoongenTestPMD_testpmd_dpdk_setup_next(self, _, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        # setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        p.forward_setup()
        self.assertTrue(p._is_forward_setup())
        self.assertTrue(p.forward_setup_done)

    @mock.patch('time.sleep')
    def test_MoongenTestPMD_l2fwd_forward_setup_first(self, _, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.L2fwdargs, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        # is_dpdk_setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        p.forward_setup()
        self.assertFalse(p._is_forward_setup())
        self.assertTrue(p.forward_setup_done)

    @mock.patch('time.sleep')
    def test_MoongenTestPMD_l2fwd_dpdk_setup_next(self, _, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.L2fwdargs, self.ctx)

        # setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, 'dummy', '')
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        p.forward_setup()
        self.assertTrue(p._is_forward_setup())
        self.assertTrue(p.forward_setup_done)

    def test_moongen_testpmd_generate_config_file(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        # setup() specific mocks
        mock_subprocess.call().execute.return_value = None

        p.generate_config_file(frame_size=1, traffic_type=1, multistream=1,
                               runBidirec="True", tg_port1_vlan=1,
                               tg_port2_vlan=2, SearchRuntime=1,
                               Package_Loss=0)
        self.assertTrue(p.CONFIG_FILE)

    def test_moongen_testpmd_result_to_data_match(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        mock_subprocess.call().execute.return_value = None
        result=("[REPORT]Device 1->0: Tx frames: 420161490 Rx Frames: 420161490"
                " frame loss: 0, 0.000000% Rx Mpps: 7.002708\n[REPORT]      "
                "total: Tx frames: 840321216 Rx Frames: 840321216 frame loss: "
                "0, 0.000000% Tx Mpps: 14.005388 Rx Mpps: 14.005388\n'")
        p.result_to_data(result=result, frame_size=0)
        self.assertTrue(p.TO_DATA)

    def test_moongen_testpmd_result_to_data_not_match(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        mock_subprocess.call().execute.return_value = None
        result=("")
        p.result_to_data(result=result, frame_size=0)
        self.assertTrue(p.TO_DATA)

    @mock.patch('time.sleep')
    def test_moongen_testpmd_run_ok(self, _, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)
        p.setup_done = True
        p.forward_setup_done = True
        p.setup()

        # run() specific mocks
        p.server = self.mock_ssh.SSH.from_node()
        mock_subprocess.call().execute.return_value = None
        mock_subprocess.call().execute.return_value = None
        result=("[REPORT]Device 1->0: Tx frames: 420161490 Rx Frames: 420161490"
                " frame loss: 0, 0.000000% Rx Mpps: 7.002708\n[REPORT]      "
                "total: Tx frames: 840321216 Rx Frames: 840321216 frame loss: "
                "0, 0.000000% Tx Mpps: 14.005388 Rx Mpps: 14.005388\n'")
        self.mock_ssh.SSH.from_node().execute.return_value = (
            0, result, '')

        test_result = {}
        p.run(test_result)

        self.assertEqual(test_result['rx_mpps'], 14.005388)

    def test_moongen_testpmd_run_falied_vsperf_execution(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        # setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        # run() specific mocks
        mock_subprocess.call().execute.return_value = None
        mock_subprocess.call().execute.return_value = None
        self.mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        result = {}
        self.assertRaises(RuntimeError, p.run, result)

    def test_moongen_testpmd_run_falied_csv_report(self, mock_subprocess):
        p = moongen_testpmd.MoongenTestPMD(self.TestPMDargs, self.ctx)

        # setup() specific mocks
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        mock_subprocess.call().execute.return_value = None

        p.setup()
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

        # run() specific mocks
        mock_subprocess.call().execute.return_value = None
        mock_subprocess.call().execute.return_value = None
        self.mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        result = {}
        self.assertRaises(RuntimeError, p.run, result)

def main():
    unittest.main()


if __name__ == '__main__':
    main()

