##############################################################################
# Copyright (c) 2015 ZTE and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest
import time
import logging

import yardstick.common.utils as utils
from yardstick import ssh
from yardstick.benchmark.scenarios.networking import pktgen_dpdk
from yardstick.common import exceptions as y_exc


logging.disable(logging.CRITICAL)


class PktgenDPDKLatencyTestCase(unittest.TestCase):

    def setUp(self):
        self.context_cfg = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'root',
                'key_filename': 'mykey.key'
            },
            'target': {
                'ip': '172.16.0.138',
                'user': 'root',
                'key_filename': 'mykey.key',
                'ipaddr': '172.16.0.138'
            }
        }
        self.scenario_cfg = {
            'options': {'packetsize': 60}
        }

        self._mock_SSH = mock.patch.object(ssh, 'SSH')
        self.mock_SSH = self._mock_SSH.start()

        self._mock_time_sleep = mock.patch.object(time, 'sleep')
        self.mock_time_sleep = self._mock_time_sleep.start()

        self.mock_SSH.from_node().execute.return_value = (0, '', '')

        self.addCleanup(self._stop_mock)

        self.scenario = pktgen_dpdk.PktgenDPDKLatency(self.scenario_cfg,
                                                      self.context_cfg)
        self.scenario.server = self.mock_SSH.from_node()
        self.scenario.client = self.mock_SSH.from_node()

    def _stop_mock(self):
        self._mock_SSH.stop()
        self._mock_time_sleep.stop()

    def test_setup(self):
        scenario = pktgen_dpdk.PktgenDPDKLatency(self.scenario_cfg,
                                                 self.context_cfg)
        scenario.setup()

        self.assertIsNotNone(scenario.server)
        self.assertIsNotNone(scenario.client)
        self.assertTrue(scenario.setup_done)

    def test_get_port_ip_command(self):
        utils.get_port_ip(self.scenario.server, "eth1")

        self.mock_SSH.from_node().execute.assert_called_with(
            "ifconfig eth1 |grep 'inet addr' "
            "|awk '{print $2}' |cut -d ':' -f2 ")

    def test_get_port_mac_command(self):
        utils.get_port_mac(self.scenario.server, "eth1")

        self.mock_SSH.from_node().execute.assert_called_with(
            "ifconfig |grep HWaddr |grep eth1 |awk '{print $5}' ")

    def test_run_no_sla(self):
        sample_output = '100\n110\n112\n130\n149\n150\n90\n150\n200\n162\n'
        self.mock_SSH.from_node().execute.return_value = (0, sample_output, '')

        result = {}
        self.scenario.run(result)
        # with python 3 we get float, might be due python division changes
        # AssertionError: {'avg_latency': 132.33333333333334} != {
        # 'avg_latency': 132}
        delta = result['avg_latency'] - 132
        self.assertLessEqual(delta, 1)

    def test_run_sla(self):
        self.scenario_cfg['sla'] = {'max_latency': 100}
        scenario = pktgen_dpdk.PktgenDPDKLatency(self.scenario_cfg,
                                                 self.context_cfg)

        sample_output = '100\n100\n100\n100\n100\n100\n100\n100\n100\n100\n'
        self.mock_SSH.from_node().execute.return_value = (0, sample_output, '')

        result = {}
        scenario.run(result)

        self.assertEqual(result, {"avg_latency": 100})

    def test_run_sla_error(self):
        self.scenario_cfg['sla'] = {'max_latency': 100}
        scenario = pktgen_dpdk.PktgenDPDKLatency(self.scenario_cfg,
                                                 self.context_cfg)

        sample_output = '100\n110\n112\n130\n149\n150\n90\n150\n200\n162\n'
        self.mock_SSH.from_node().execute.return_value = (0, sample_output, '')

        with self.assertRaises(y_exc.SLAValidationError):
            scenario.run({})

    def test_run_command_count(self):
        self.scenario.run({})
        self.assertEqual(self.mock_SSH.from_node().execute.call_count, 6)

    def test_run_last_command_raise_on_error(self):
        self.mock_SSH.from_node().execute.side_effect = ((0, '', ''),
                                                         (0, '', ''),
                                                         (0, '', ''),
                                                         (0, '', ''),
                                                         (0, '', ''),
                                                         y_exc.SSHError)
        with self.assertRaises(y_exc.SSHError):
            self.scenario.run({})
        self.assertEqual(self.mock_SSH.from_node().execute.call_count, 6)
