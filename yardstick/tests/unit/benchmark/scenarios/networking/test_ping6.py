#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.networking.ping.Ping

from __future__ import absolute_import
import mock
import unittest

from yardstick.benchmark.scenarios.networking import ping6


class PingTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'nodes': {
                'host1': {
                    'ip': '172.16.0.137',
                    'user': 'cirros',
                    'role': "Controller",
                    'key_filename': "mykey.key",
                    'password': "root"
                },
                'host2': {
                    "ip": "172.16.0.138",
                    "key_filename": "/root/.ssh/id_rsa",
                    "role": "Compute",
                    "name": "node3.IPV6",
                    "user": "root"
                },
            }
        }

    def test_get_controller_node(self):
        args = {
            'options': {'host': 'host1', 'packetsize': 200, 'ping_count': 5},
            'sla': {'max_rtt': 50}
        }
        p = ping6.Ping6(args, self.ctx)
        controller_node = p._get_controller_node(['host1', 'host2'])
        self.assertEqual(controller_node, 'host1')

    @mock.patch('yardstick.benchmark.scenarios.networking.ping6.ssh')
    def test_ping_successful_setup(self, mock_ssh):
        args = {
            'options': {'host': 'host1', 'packetsize': 200, 'ping_count': 5},
            'sla': {'max_rtt': 50}
        }
        p = ping6.Ping6(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '0', '')
        p.setup()

        self.assertEqual(p.setup_done, True)

    @mock.patch('yardstick.benchmark.scenarios.networking.ping6.ssh')
    def test_ping_successful_no_sla(self, mock_ssh):
        args = {
            'options': {'host': 'host1', 'packetsize': 200, 'ping_count': 5},

        }
        result = {}

        p = ping6.Ping6(args, self.ctx)
        p.client = mock_ssh.SSH.from_node()
        mock_ssh.SSH.from_node().execute.side_effect = [(0, 'host1', ''), (0, 100, '')]
        p.run(result)
        self.assertEqual(result, {'rtt': 100.0})

    @mock.patch('yardstick.benchmark.scenarios.networking.ping6.ssh')
    def test_ping_successful_sla(self, mock_ssh):
        args = {
            'options': {'host': 'host1', 'packetsize': 200, 'ping_count': 5},
            'sla': {'max_rtt': 150}
        }
        result = {}

        p = ping6.Ping6(args, self.ctx)
        p.client = mock_ssh.SSH.from_node()
        mock_ssh.SSH.from_node().execute.side_effect = [(0, 'host1', ''), (0, 100, '')]
        p.run(result)
        self.assertEqual(result, {'rtt': 100.0})

    @mock.patch('yardstick.benchmark.scenarios.networking.ping6.ssh')
    def test_ping_unsuccessful_sla(self, mock_ssh):
        args = {
            'options': {'host': 'host1', 'packetsize': 200, 'ping_count': 5},
            'sla': {'max_rtt': 50}
        }
        result = {}

        p = ping6.Ping6(args, self.ctx)
        p.client = mock_ssh.SSH.from_node()
        mock_ssh.SSH.from_node().execute.side_effect = [(0, 'host1', ''), (0, 100, '')]
        self.assertRaises(AssertionError, p.run, result)

    @mock.patch('yardstick.benchmark.scenarios.networking.ping6.ssh')
    def test_ping_unsuccessful_script_error(self, mock_ssh):

        args = {
            'options': {'host': 'host1', 'packetsize': 200, 'ping_count': 5},
            'sla': {'max_rtt': 150}
        }
        result = {}

        p = ping6.Ping6(args, self.ctx)
        p.client = mock_ssh.SSH.from_node()
        mock_ssh.SSH.from_node().execute.side_effect = [
            (0, 'host1', ''), (1, '', 'FOOBAR')]
        self.assertRaises(RuntimeError, p.run, result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
