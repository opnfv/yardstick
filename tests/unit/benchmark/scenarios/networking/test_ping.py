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

import mock
import unittest

from yardstick.benchmark.scenarios.networking import ping


class PingTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'cirros',
                'key_filename': "mykey.key"
            },
            "target": {
                "ipaddr": "10.229.17.105",
            }
        }

    @mock.patch('yardstick.benchmark.scenarios.networking.ping.ssh')
    def test_ping_successful_no_sla(self, mock_ssh):

        p = ping.Ping(self.ctx)

        args = {
            'options': {'packetsize': 200},
            }
        result = {}

        mock_ssh.SSH().execute.return_value = (0, '100', '')
        p.run(args, result)
        self.assertEqual(result, {'rtt': 100.0})

    @mock.patch('yardstick.benchmark.scenarios.networking.ping.ssh')
    def test_ping_successful_sla(self, mock_ssh):

        p = ping.Ping(self.ctx)

        args = {
            'options': {'packetsize': 200},
            'ipaddr': '172.16.0.138',
            'sla': {'max_rtt': 150}
            }
        result = {}

        mock_ssh.SSH().execute.return_value = (0, '100', '')
        p.run(args, result)
        self.assertEqual(result, {'rtt': 100.0})

    @mock.patch('yardstick.benchmark.scenarios.networking.ping.ssh')
    def test_ping_unsuccessful_sla(self, mock_ssh):

        p = ping.Ping(self.ctx)

        args = {
            'options': {'packetsize': 200},
            'ipaddr': '172.16.0.138',
            'sla': {'max_rtt': 50}
            }
        result = {}

        mock_ssh.SSH().execute.return_value = (0, '100', '')
        self.assertRaises(AssertionError, p.run, args, result)

    @mock.patch('yardstick.benchmark.scenarios.networking.ping.ssh')
    def test_ping_unsuccessful_script_error(self, mock_ssh):

        p = ping.Ping(self.ctx)

        args = {
            'options': {'packetsize': 200},
            'ipaddr': '172.16.0.138',
            'sla': {'max_rtt': 50}
            }
        result = {}

        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, args, result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
