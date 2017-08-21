#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 ZTE and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.networking.pktgen.Pktgen

from __future__ import absolute_import
import unittest

import mock

import yardstick.common.utils as utils
from yardstick.benchmark.scenarios.networking import pktgen_dpdk


@mock.patch('yardstick.benchmark.scenarios.networking.pktgen_dpdk.time')
@mock.patch('yardstick.benchmark.scenarios.networking.pktgen_dpdk.ssh')
class PktgenDPDKLatencyTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
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

    def test_pktgen_dpdk_successful_setup(self, mock_ssh, mock_time):

        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk.PktgenDPDKLatency(args, self.ctx)
        p.setup()

        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.assertIsNotNone(p.server)
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

    def test_pktgen_dpdk_successful_get_port_ip(self, mock_ssh, mock_time):

        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk.PktgenDPDKLatency(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        utils.get_port_ip(p.server, "eth1")

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "ifconfig eth1 |grep 'inet addr' |awk '{print $2}' |cut -d ':' -f2 ")

    def test_pktgen_dpdk_unsuccessful_get_port_ip(self, mock_ssh, mock_time):

        args = {
            'options': {'packetsize': 60},
        }

        p = pktgen_dpdk.PktgenDPDKLatency(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, utils.get_port_ip, p.server, "eth1")

    def test_pktgen_dpdk_successful_get_port_mac(self, mock_ssh, mock_time):

        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk.PktgenDPDKLatency(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        utils.get_port_mac(p.server, "eth1")

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "ifconfig |grep HWaddr |grep eth1 |awk '{print $5}' ")

    def test_pktgen_dpdk_unsuccessful_get_port_mac(self, mock_ssh, mock_time):

        args = {
            'options': {'packetsize': 60},
        }

        p = pktgen_dpdk.PktgenDPDKLatency(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, utils.get_port_mac, p.server, "eth1")

    def test_pktgen_dpdk_successful_no_sla(self, mock_ssh, mock_time):

        args = {
            'options': {'packetsize': 60},
        }

        result = {}
        p = pktgen_dpdk.PktgenDPDKLatency(args, self.ctx)

        sample_output = '100\n110\n112\n130\n149\n150\n90\n150\n200\n162\n'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)
        # with python 3 we get float, might be due python division changes
        # AssertionError: {'avg_latency': 132.33333333333334} != {
        # 'avg_latency': 132}
        delta = result['avg_latency'] - 132
        self.assertLessEqual(delta, 1)

    def test_pktgen_dpdk_successful_sla(self, mock_ssh, mock_time):

        args = {
            'options': {'packetsize': 60},
            'sla': {'max_latency': 100}
        }
        result = {}

        p = pktgen_dpdk.PktgenDPDKLatency(args, self.ctx)

        sample_output = '100\n100\n100\n100\n100\n100\n100\n100\n100\n100\n'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)

        self.assertEqual(result, {"avg_latency": 100})

    def test_pktgen_dpdk_unsuccessful_sla(self, mock_ssh, mock_time):

        args = {
            'options': {'packetsize': 60},
            'sla': {'max_latency': 100}
        }
        result = {}

        p = pktgen_dpdk.PktgenDPDKLatency(args, self.ctx)

        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        sample_output = '100\n110\n112\n130\n149\n150\n90\n150\n200\n162\n'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, result)

    def test_pktgen_dpdk_unsuccessful_script_error(self, mock_ssh, mock_time):

        args = {
            'options': {'packetsize': 60},
            'sla': {'max_latency': 100}
        }
        result = {}

        p = pktgen_dpdk.PktgenDPDKLatency(args, self.ctx)

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, result)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
