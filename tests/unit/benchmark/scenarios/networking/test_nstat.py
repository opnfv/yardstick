#!/usr/bin/env python

##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.networking.nstat.Nstat

from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.networking import nstat

@mock.patch('yardstick.benchmark.scenarios.networking.nstat.ssh')
class NstatTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            "host": {
                "ip": "192.168.50.28",
                "user": "root",
                "key_filename": "mykey.key"
            }
        }

    def test_nstat_successful_setup(self, mock_ssh):

        n = nstat.Nstat({}, self.ctx)
        n.setup()

        mock_ssh.SSH().execute.return_value = (0, '', '')
        self.assertIsNotNone(n.client)
        self.assertEqual(n.setup_done, True)

    def test_nstat_successful_no_sla(self, mock_ssh):

        options = {
            "duration": 60
        }
        args = {
            "options": options,
        }
        n = nstat.Nstat(args, self.ctx)
        result = {}

        sample_output = '{"IpInReceives":"1020", "IP_datagram_error_rate":".001",\
        "IcmpInMsgs":"221", "Icmp_message_error_rate":"0", "TcpInSegs":"35",\
        "Tcp_segment_error_rate":"0", "UdpInDatagrams":"600",\
        "Udp_datagram_error_rate":"0"}'
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')

        n.run(result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_nstat_successful_sla(self, mock_ssh):

        options = {
            "duration": 60
        }
        sla = {
            "IP_datagram_error_rate": 0.1
        }
        args = {
            "options": options,
            "sla": sla
        }
        n = nstat.Nstat(args, self.ctx)
        result = {}

        sample_output = '{"IpInReceives":"1020", "IP_datagram_error_rate":".001",\
        "IcmpInMsgs":"221", "Icmp_message_error_rate":"0", "TcpInSegs":"35",\
        "Tcp_segment_error_rate":"0", "UdpInDatagrams":"600",\
        "Udp_datagram_error_rate":"0"}'
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')

        n.run(result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_nstat_unsuccessful_script_error(self, mock_ssh):

        options = {
            "duration": 60
        }
        sla = {
            "IP_datagram_error_rate": 0.1
        }
        args = {
            "options": options,
            "sla": sla
        }
        n = nstat.Nstat(args, self.ctx)
        result = {}

        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, n.run, result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
