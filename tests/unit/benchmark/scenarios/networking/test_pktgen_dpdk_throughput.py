##############################################################################
# Copyright (c) 2017 Nokia and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
#!/usr/bin/env python

# Unittest for yardstick.benchmark.scenarios.networking.pktgen.PktgenDPDK

from __future__ import absolute_import
import unittest

from oslo_serialization import jsonutils
import mock

from yardstick.benchmark.scenarios.networking import pktgen_dpdk_throughput


@mock.patch('yardstick.benchmark.scenarios.networking.pktgen_dpdk_throughput.ssh')
@mock.patch('yardstick.benchmark.scenarios.networking.pktgen_dpdk_throughput.time')
class PktgenDPDKTestCase(unittest.TestCase):

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
            }
        }

    def test_pktgen_dpdk_throughput_successful_setup(self, mock__time, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        p.setup()

        mock_ssh.SSH().execute.return_value = (0, '', '')
        self.assertIsNotNone(p.server)
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

    def test_pktgen_dpdk_throughput_successful_no_sla(self, mock__time, mock_ssh):
        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
        }

        result = {}

        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)

        p.server = mock_ssh.SSH()
        p.client = mock_ssh.SSH()

        mock_dpdk_result = mock.Mock()
        mock_dpdk_result.return_value = 149300
        p._dpdk_get_result = mock_dpdk_result

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149776, "flows": 110}'
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')

        p.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_pktgen_dpdk_throughput_successful_sla(self, mock__time, mock_ssh):
        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
            'sla': {'max_ppm': 10000}
        }
        result = {}

        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)

        p.server = mock_ssh.SSH()
        p.client = mock_ssh.SSH()

        mock_dpdk_result = mock.Mock()
        mock_dpdk_result.return_value = 149300
        p._dpdk_get_result = mock_dpdk_result

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149776, "flows": 110}'
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')

        p.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_pktgen_dpdk_throughput_unsuccessful_sla(self, mock__time, mock_ssh):
        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
            'sla': {'max_ppm': 1000}
        }
        result = {}

        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)

        p.server = mock_ssh.SSH()
        p.client = mock_ssh.SSH()

        mock_dpdk_result = mock.Mock()
        mock_dpdk_result.return_value = 149300
        p._dpdk_get_result = mock_dpdk_result

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149776, "flows": 110}'
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, result)

    def test_pktgen_dpdk_throughput_unsuccessful_script_error(self, mock__time, mock_ssh):
        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
            'sla': {'max_ppm': 1000}
        }
        result = {}

        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)

        p.server = mock_ssh.SSH()
        p.client = mock_ssh.SSH()

        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, result)

    def test_pktgen_dpdk_throughput_is_dpdk_setup(self, mock__time, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        p.server = mock_ssh.SSH()

        mock_ssh.SSH().execute.return_value = (0, '', '')

        p._is_dpdk_setup("server")

        mock_ssh.SSH().execute.assert_called_with(
            "ip a | grep eth1 2>/dev/null")

    def test_pktgen_dpdk_throughput_dpdk_setup(self, mock__time, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        p.server = mock_ssh.SSH()
        p.client = mock_ssh.SSH()

        mock_ssh.SSH().execute.return_value = (0, '', '')

        p.dpdk_setup()

        self.assertEqual(p.dpdk_setup_done, True)

    def test_pktgen_dpdk_throughput_dpdk_get_result(self, mock__time, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        p.server = mock_ssh.SSH()
        p.client = mock_ssh.SSH()

        mock_ssh.SSH().execute.return_value = (0, '10000', '')

        p._dpdk_get_result()

        mock_ssh.SSH().execute.assert_called_with(
            "sudo /dpdk/destdir/bin/dpdk-procinfo -- --stats-reset > /dev/null 2>&1")

def main():
    unittest.main()

if __name__ == '__main__':
    main()
