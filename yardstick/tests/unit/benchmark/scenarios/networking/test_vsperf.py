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

import mock
import unittest
import subprocess
import yardstick.ssh as ssh

from yardstick.benchmark.scenarios.networking import vsperf
from yardstick import exceptions as y_exc


class VsperfTestCase(unittest.TestCase):

    def setUp(self):
        self.context_cfg = {
            "host": {
                "ip": "10.229.47.137",
                "user": "ubuntu",
                "password": "ubuntu",
            },
        }
        self.scenario_cfg = {
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

        self._mock_SSH = mock.patch.object(ssh, 'SSH')
        self.mock_SSH = self._mock_SSH.start()
        self.mock_SSH.from_node().execute.return_value = (0, '', '')

        self._mock_subprocess_call = mock.patch.object(subprocess, 'call')
        self.mock_subprocess_call = self._mock_subprocess_call.start()
        self.mock_subprocess_call.return_value = None

        self.addCleanup(self._stop_mock)

        self.scenario = vsperf.Vsperf(self.scenario_cfg, self.context_cfg)

    def _stop_mock(self):
        self._mock_SSH.stop()
        self._mock_subprocess_call.stop()

    def test_setup(self):
        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

    def test_setup_tg_port_not_set(self):
        del self.scenario_cfg['options']['trafficgen_port1']
        del self.scenario_cfg['options']['trafficgen_port2']
        scenario = vsperf.Vsperf(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_subprocess_call.assert_called_once_with(
            'setup_yardstick.sh setup', shell=True)
        self.assertIsNone(scenario.tg_port1)
        self.assertIsNone(scenario.tg_port2)
        self.assertIsNotNone(scenario.client)
        self.assertTrue(scenario.setup_done)

    def test_setup_no_setup_script(self):
        del self.scenario_cfg['options']['setup_script']
        scenario = vsperf.Vsperf(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_subprocess_call.assert_has_calls(
            (mock.call('sudo bash -c "ovs-vsctl add-port br-ex eth1"',
                       shell=True),
             mock.call('sudo bash -c "ovs-vsctl add-port br-ex eth3"',
                       shell=True)))
        self.assertEqual(2, self.mock_subprocess_call.call_count)
        self.assertIsNone(scenario.setup_script)
        self.assertIsNotNone(scenario.client)
        self.assertTrue(scenario.setup_done)

    def test_run_ok(self):
        self.scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n14797660.000\r\n', '')

        result = {}
        self.scenario.run(result)

        self.assertEqual(result['throughput_rx_fps'], '14797660.000')

    def test_run_ok_setup_not_done(self):
        self.mock_SSH.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n14797660.000\r\n', '')

        result = {}
        self.scenario.run(result)

        self.assertTrue(self.scenario.setup_done)
        self.assertEqual(result['throughput_rx_fps'], '14797660.000')

    def test_run_ssh_command_call_counts(self):
        self.scenario.run({})

        self.assertEqual(self.mock_SSH.from_node().execute.call_count, 2)
        self.mock_SSH.from_node().run.assert_called_once()

    def test_run_sla_fail(self):
        self.mock_SSH.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n123456.000\r\n', '')

        with self.assertRaises(y_exc.SLAValidationError) as raised:
            self.scenario.run({})

        self.assertTrue('VSPERF_throughput_rx_fps(123456.000000) < '
                        'SLA_throughput_rx_fps(500000.000000)'
                        in str(raised.exception))

    def test_run_sla_fail_metric_not_collected(self):
        self.mock_SSH.from_node().execute.return_value = (
            0, 'nonexisting_metric\r\n14797660.000\r\n', '')

        with self.assertRaises(y_exc.SLAValidationError) as raised:
            self.scenario.run({})

        self.assertTrue('throughput_rx_fps was not collected by VSPERF'
                        in str(raised.exception))

    def test_run_sla_fail_metric_not_defined_in_sla(self):
        del self.scenario_cfg['sla']['throughput_rx_fps']
        scenario = vsperf.Vsperf(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (
            0, 'throughput_rx_fps\r\n14797660.000\r\n', '')

        with self.assertRaises(y_exc.SLAValidationError) as raised:
            scenario.run({})
        self.assertTrue('throughput_rx_fps is not defined in SLA'
                        in str(raised.exception))

    def test_teardown(self):
        self.scenario.setup()
        self.assertIsNotNone(self.scenario.client)
        self.assertTrue(self.scenario.setup_done)

        self.scenario.teardown()
        self.assertFalse(self.scenario.setup_done)

    def test_teardown_tg_port_not_set(self):
        del self.scenario_cfg['options']['trafficgen_port1']
        del self.scenario_cfg['options']['trafficgen_port2']
        scenario = vsperf.Vsperf(self.scenario_cfg, self.context_cfg)
        scenario.teardown()

        self.mock_subprocess_call.assert_called_once_with(
            'setup_yardstick.sh teardown', shell=True)
        self.assertFalse(scenario.setup_done)

    def test_teardown_no_setup_script(self):
        del self.scenario_cfg['options']['setup_script']
        scenario = vsperf.Vsperf(self.scenario_cfg, self.context_cfg)
        scenario.teardown()

        self.mock_subprocess_call.assert_has_calls(
            (mock.call('sudo bash -c "ovs-vsctl del-port br-ex eth1"',
                       shell=True),
             mock.call('sudo bash -c "ovs-vsctl del-port br-ex eth3"',
                       shell=True)))
        self.assertEqual(2, self.mock_subprocess_call.call_count)
        self.assertFalse(scenario.setup_done)
