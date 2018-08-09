##############################################################################
# Copyright (c) 2017 Nokia and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import time
import unittest

from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.networking import pktgen_dpdk_throughput
from yardstick.common import exceptions as y_exc
from yardstick import ssh


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

        self._mock_time = mock.patch.object(time, 'sleep')
        self.mock_time = self._mock_time.start()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self._mock_time.stop()

    @mock.patch.object(ssh, 'SSH')
    def test_setup(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        mock_ssh.execute.return_value = (0, '', '')

        p.setup()

        self.assertIsNotNone(p.server)
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

    def test_run_successful_no_sla(self):
        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
        }

        result = {}

        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        p.setup_done = True
        p.server = mock.Mock(spec=ssh.SSH)
        p.client = mock.Mock(spec=ssh.SSH)

        mock_dpdk_result = mock.Mock(return_value=149300)
        p._dpdk_get_result = mock_dpdk_result

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149776, "flows": 110}'
        p.client.execute.return_value = (0, sample_output, '')
        p.server.execute.return_value = (0, '', '')

        p.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_run_successful_sla(self):
        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
            'sla': {'max_ppm': 10000}
        }
        result = {}

        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        p.setup_done = True

        p.server = mock.Mock(spec=ssh.SSH)
        p.client = mock.Mock(spec=ssh.SSH)

        mock_dpdk_result = mock.Mock(return_value=149300)
        p._dpdk_get_result = mock_dpdk_result

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149776, "flows": 110}'
        p.client.execute.return_value = (0, sample_output, '')
        p.server.execute.return_value = (0, '', '')

        p.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_run_sla_validation_failed(self):
        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
            'sla': {'max_ppm': 1000}
        }
        result = {}

        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        p.setup_done = True

        p.server = mock.Mock(spec=ssh.SSH)
        p.client = mock.Mock(spec=ssh.SSH)

        mock_dpdk_result = mock.Mock(return_value=149300)
        p._dpdk_get_result = mock_dpdk_result

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149776, "flows": 110}'
        p.client.execute.return_value = (0, sample_output, '')
        p.server.execute.return_value = (0, '', '')

        self.assertRaises(y_exc.SLAValidationError, p.run, result)

    def test_run_script_error(self):
        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
            'sla': {'max_ppm': 1000}
        }
        result = {}

        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        p.setup_done = True

        p.server = mock.Mock(spec=ssh.SSH)
        p.client = mock.Mock(spec=ssh.SSH)

        p.client.execute.return_value = (1, '', 'FOOBAR')
        p.server.execute.return_value = (0, '', '')

        self.assertRaises(RuntimeError, p.run, result)

    def test_is_dpdk_setup(self):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)

        p.server = mock.Mock(spec=ssh.SSH)
        p.server.execute.return_value = (0, '', '')

        p._is_dpdk_setup("server")

        p.server.execute.assert_called_with(
            "ip a | grep eth1 2>/dev/null")

    def test_dpdk_setup(self):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        p.server = mock.Mock(spec=ssh.SSH)
        p.client = mock.Mock(spec=ssh.SSH)

        p.client.execute.return_value = (0, '', '')
        p.server.execute.return_value = (0, '', '')

        self.assertFalse(p.dpdk_setup_done)
        p.dpdk_setup()
        self.assertTrue(p.dpdk_setup_done)

    def test__dpdk_get_result(self):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen_dpdk_throughput.PktgenDPDK(args, self.ctx)
        p.server = mock.Mock(spec=ssh.SSH)
        p.client = mock.Mock(spec=ssh.SSH)
        p.server.execute.return_value = (0, '10000', '')

        p._dpdk_get_result()

        p.server.execute.assert_called_with(
            "sudo /dpdk/destdir/bin/dpdk-procinfo -- --stats-reset > /dev/null 2>&1")
