##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest

from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.networking import pktgen


@mock.patch('yardstick.benchmark.scenarios.networking.pktgen.ssh')
class PktgenTestCase(unittest.TestCase):

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

    def test_pktgen_successful_setup(self, mock_ssh):

        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.setup()

        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.assertIsNotNone(p.server)
        self.assertIsNotNone(p.client)
        self.assertTrue(p.setup_done)

    def test_pktgen_successful_iptables_setup(self, mock_ssh):

        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.number_of_ports = args['options']['number_of_ports']

        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        p._iptables_setup()

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "sudo iptables -F; "
            "sudo iptables -A INPUT -p udp --dport 1000:%s -j DROP"
            % 1010, timeout=60)

    def test_pktgen_unsuccessful_iptables_setup(self, mock_ssh):

        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
        }

        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.number_of_ports = args['options']['number_of_ports']

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p._iptables_setup)

    def test_pktgen_successful_iptables_get_result(self, mock_ssh):

        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
        }

        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.number_of_ports = args['options']['number_of_ports']

        mock_ssh.SSH.from_node().execute.return_value = (0, '150000', '')
        p._iptables_get_result()

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "sudo iptables -L INPUT -vnx |"
            "awk '/dpts:1000:%s/ {{printf \"%%s\", $1}}'"
            % 1010)

    def test_pktgen_unsuccessful_iptables_get_result(self, mock_ssh):

        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
        }

        p = pktgen.Pktgen(args, self.ctx)

        p.server = mock_ssh.SSH.from_node()
        p.number_of_ports = args['options']['number_of_ports']

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p._iptables_get_result)

    def test_pktgen_successful_no_sla(self, mock_ssh):

        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
        }
        result = {}

        p = pktgen.Pktgen(args, self.ctx)

        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        p._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149776, "packetsize": 60, "flows": 110, "ppm": 3179}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_pktgen_successful_sla(self, mock_ssh):

        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
            'sla': {'max_ppm': 10000}
        }
        result = {}

        p = pktgen.Pktgen(args, self.ctx)

        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        p._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149776, "packetsize": 60, "flows": 110, "ppm": 3179}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_pktgen_unsuccessful_sla(self, mock_ssh):

        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
            'sla': {'max_ppm': 1000}
        }
        result = {}

        p = pktgen.Pktgen(args, self.ctx)

        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        p._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149776, "packetsize": 60, "flows": 110}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, result)

    def test_pktgen_unsuccessful_script_error(self, mock_ssh):

        args = {
            'options': {'packetsize': 60, 'number_of_ports': 10},
            'sla': {'max_ppm': 1000}
        }
        result = {}

        p = pktgen.Pktgen(args, self.ctx)

        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, result)

    def test_pktgen_get_vnic_driver_name(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, 'ixgbevf', '')

        vnic_driver_name = p._get_vnic_driver_name()
        self.assertEqual(vnic_driver_name, 'ixgbevf')

    def test_pktgen_unsuccessful_get_vnic_driver_name(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p._get_vnic_driver_name)

    def test_pktgen_get_sriov_queue_number(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '2', '')

        p.queue_number = p._get_sriov_queue_number()
        self.assertEqual(p.queue_number, 2)

    def test_pktgen_unsuccessful_get_sriov_queue_number(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p._get_sriov_queue_number)

    def test_pktgen_get_available_queue_number(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '4', '')

        p._get_available_queue_number()

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "sudo ethtool -l eth0 | grep Combined | head -1 |"
            "awk '{printf $2}'")

    def test_pktgen_unsuccessful_get_available_queue_number(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p._get_available_queue_number)

    def test_pktgen_get_usable_queue_number(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '1', '')

        p._get_usable_queue_number()

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "sudo ethtool -l eth0 | grep Combined | tail -1 |"
            "awk '{printf $2}'")

    def test_pktgen_unsuccessful_get_usable_queue_number(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p._get_usable_queue_number)

    def test_pktgen_enable_ovs_multiqueue(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '4', '')

        p._get_usable_queue_number = mock.Mock(return_value=1)
        p._get_available_queue_number = mock.Mock(return_value=4)

        p.queue_number = p._enable_ovs_multiqueue()
        self.assertEqual(p.queue_number, 4)

    def test_pktgen_enable_ovs_multiqueue_1q(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '1', '')

        p._get_usable_queue_number = mock.Mock(return_value=1)
        p._get_available_queue_number = mock.Mock(return_value=1)

        p.queue_number = p._enable_ovs_multiqueue()
        self.assertEqual(p.queue_number, 1)

    def test_pktgen_unsuccessful_enable_ovs_multiqueue(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        p._get_usable_queue_number = mock.Mock(return_value=1)
        p._get_available_queue_number = mock.Mock(return_value=4)

        self.assertRaises(RuntimeError, p._enable_ovs_multiqueue)

    def test_pktgen_setup_irqmapping_ovs(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '10', '')

        p._setup_irqmapping_ovs(4)

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "echo 8 | sudo tee /proc/irq/10/smp_affinity")

    def test_pktgen_setup_irqmapping_ovs_1q(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '10', '')

        p._setup_irqmapping_ovs(1)

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "echo 1 | sudo tee /proc/irq/10/smp_affinity")

    def test_pktgen_unsuccessful_setup_irqmapping_ovs(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p._setup_irqmapping_ovs, 4)

    def test_pktgen_unsuccessful_setup_irqmapping_ovs_1q(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p._setup_irqmapping_ovs, 1)

    def test_pktgen_setup_irqmapping_sriov(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '10', '')

        p._setup_irqmapping_sriov(2)

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "echo 2 | sudo tee /proc/irq/10/smp_affinity")

    def test_pktgen_setup_irqmapping_sriov_1q(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '10', '')

        p._setup_irqmapping_sriov(1)

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "echo 1 | sudo tee /proc/irq/10/smp_affinity")

    def test_pktgen_unsuccessful_setup_irqmapping_sriov(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p._setup_irqmapping_sriov, 2)

    def test_pktgen_unsuccessful_setup_irqmapping_sriov_1q(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p._setup_irqmapping_sriov, 1)

    def test_pktgen_is_irqbalance_disabled(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        p._is_irqbalance_disabled()

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "grep ENABLED /etc/default/irqbalance")

    def test_pktgen_unsuccessful_is_irqbalance_disabled(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p._is_irqbalance_disabled)

    def test_pktgen_disable_irqbalance(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        p._disable_irqbalance()

        mock_ssh.SSH.from_node().execute.assert_called_with(
            "sudo service irqbalance disable")

    def test_pktgen_unsuccessful_disable_irqbalance(self, mock_ssh):
        args = {
            'options': {'packetsize': 60},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')

        self.assertRaises(RuntimeError, p._disable_irqbalance)

    def test_pktgen_multiqueue_setup_ovs(self, mock_ssh):
        args = {
            'options': {'packetsize': 60, 'multiqueue': True},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '4', '')

        p._is_irqbalance_disabled = mock.Mock(return_value=False)
        p._get_vnic_driver_name = mock.Mock(return_value="virtio_net")
        p._get_usable_queue_number = mock.Mock(return_value=1)
        p._get_available_queue_number = mock.Mock(return_value=4)

        p.multiqueue_setup()

        self.assertEqual(p.queue_number, 4)

    def test_pktgen_multiqueue_setup_ovs_1q(self, mock_ssh):
        args = {
            'options': {'packetsize': 60, 'multiqueue': True},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '1', '')

        p._is_irqbalance_disabled = mock.Mock(return_value=False)
        p._get_vnic_driver_name = mock.Mock(return_value="virtio_net")
        p._get_usable_queue_number = mock.Mock(return_value=1)
        p._get_available_queue_number = mock.Mock(return_value=1)

        p.multiqueue_setup()

        self.assertEqual(p.queue_number, 1)

    def test_pktgen_multiqueue_setup_sriov(self, mock_ssh):
        args = {
            'options': {'packetsize': 60, 'multiqueue': True},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '2', '')

        p._is_irqbalance_disabled = mock.Mock(return_value=False)
        p._get_vnic_driver_name = mock.Mock(return_value="ixgbevf")

        p.multiqueue_setup()

        self.assertEqual(p.queue_number, 2)

    def test_pktgen_multiqueue_setup_sriov_1q(self, mock_ssh):
        args = {
            'options': {'packetsize': 60, 'multiqueue': True},
        }
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (0, '1', '')

        p._is_irqbalance_disabled = mock.Mock(return_value=False)
        p._get_vnic_driver_name = mock.Mock(return_value="ixgbevf")

        p.multiqueue_setup()

        self.assertEqual(p.queue_number, 1)

    def test_pktgen_run_with_setup_done(self, mock_ssh):
        args = {
            'options': {
                'packetsize': 60,
                'number_of_ports': 10,
                'duration': 20,
                'multiqueue': True},
            'sla': {
                'max_ppm': 1}}
        result = {}
        p = pktgen.Pktgen(args, self.ctx)
        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        p.setup_done = True
        p.multiqueue_setup_done = True

        mock_iptables_result = mock.Mock()
        mock_iptables_result.return_value = 149300
        p._iptables_get_result = mock_iptables_result

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149300, "flows": 110, "ppm": 0}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_pktgen_run_with_ovs_multiqueque(self, mock_ssh):
        args = {
            'options': {
                'packetsize': 60,
                'number_of_ports': 10,
                'duration': 20,
                'multiqueue': True},
            'sla': {
                'max_ppm': 1}}
        result = {}

        p = pktgen.Pktgen(args, self.ctx)

        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        p._get_vnic_driver_name = mock.Mock(return_value="virtio_net")
        p._get_usable_queue_number = mock.Mock(return_value=1)
        p._get_available_queue_number = mock.Mock(return_value=4)
        p._enable_ovs_multiqueue = mock.Mock(return_value=4)
        p._setup_irqmapping_ovs = mock.Mock()
        p._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149300, "flows": 110, "ppm": 0}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_pktgen_run_with_sriov_multiqueque(self, mock_ssh):
        args = {
            'options': {
                'packetsize': 60,
                'number_of_ports': 10,
                'duration': 20,
                'multiqueue': True},
            'sla': {
                'max_ppm': 1}}
        result = {}

        p = pktgen.Pktgen(args, self.ctx)

        p.server = mock_ssh.SSH.from_node()
        p.client = mock_ssh.SSH.from_node()

        p._get_vnic_driver_name = mock.Mock(return_value="ixgbevf")
        p._get_sriov_queue_number = mock.Mock(return_value=2)
        p._setup_irqmapping_sriov = mock.Mock()
        p._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = '{"packets_per_second": 9753, "errors": 0, \
            "packets_sent": 149300, "flows": 110, "ppm": 0}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)
