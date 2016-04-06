#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.networking.ping_node.Ping_node

import mock
import unittest

from yardstick.benchmark.scenarios.networking import ping_node


class PingTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            "nodes": {
                "node1": {
                    "ip": "10.20.0.3",
                    "key_filename": "/root/.ssh/id_rsa",
                    "role": "Controller",
                    "name": "node1.LF",
                    "user": "root"
                },
                "node2": {
                    "ip": "10.20.0.4",
                    "key_filename": "/root/.ssh/id_rsa",
                    "role": "Controller",
                    "name": "node2.LF",
                    "user": "root"
                }
            }
        }

    @mock.patch('yardstick.benchmark.scenarios.networking.ping_node.ssh')
    def test_ping_node_successful(self, mock_ssh):

        args = {
            'options': {'packetsize': 200, 'host': 'node1', 'target': 'node2'},
        }
        result = {}

        p = ping_node.Ping_node(args, self.ctx)

        mock_ssh.SSH().execute.return_value = (0, '100', '')
        p.run(result)
        self.assertEqual(result, {'rtt': 100.0})

        self.assertEqual(result, {'rtt': 100.0})


def main():
    unittest.main()

if __name__ == '__main__':
    main()
