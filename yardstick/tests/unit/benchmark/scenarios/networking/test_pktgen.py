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

from yardstick import ssh
from yardstick.benchmark.scenarios.networking.pktgen import Pktgen
from yardstick import exceptions as y_exc


class PktgenTestCase(unittest.TestCase):

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

        self.mock_SSH.from_node().execute.return_value = (0, '', '')
        self.mock_SSH.from_node().run.return_value = 0

        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_SSH.stop()

    def test_pktgen_successful_setup(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.assertIsNotNone(scenario.server)
        self.assertIsNotNone(scenario.client)
        self.assertTrue(scenario.setup_done)

    def test_pktgen_successful_iptables_setup(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()
        scenario.number_of_ports = 10

        scenario._iptables_setup()

        self.mock_SSH.from_node().run.assert_called_with(
            "sudo iptables -F; "
            "sudo iptables -A INPUT -p udp --dport 1000:%s -j DROP"
            % 1010, timeout=60)

    def test_pktgen_unsuccessful_iptables_setup(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()
        scenario.number_of_ports = 10

        self.mock_SSH.from_node().run.side_effect = y_exc.SSHError
        self.assertRaises(y_exc.SSHError, scenario._iptables_setup)

    def test_pktgen_successful_iptables_get_result(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()
        scenario.number_of_ports = 10

        self.mock_SSH.from_node().execute.return_value = (0, '150000', '')
        result = scenario._iptables_get_result()
        expected_result = 150000
        self.assertEqual(result, expected_result)

        self.mock_SSH.from_node().execute.assert_called_with(
            "sudo iptables -L INPUT -vnx |"
            "awk '/dpts:1000:%s/ {{printf \"%%s\", $1}}'"
            % 1010, raise_on_error=True)

    def test_pktgen_unsuccessful_iptables_get_result(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()
        scenario.number_of_ports = 10

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError
        self.assertRaises(y_exc.SSHError, scenario._iptables_get_result)

    def test_pktgen_successful_no_sla(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        scenario._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = jsonutils.dumps({"packets_per_second": 9753,
                                         "errors": 0,
                                         "packets_sent": 149776,
                                         "packetsize": 60,
                                         "flows": 110,
                                         "ppm": 3179})
        self.mock_SSH.from_node().execute.return_value = (0, sample_output, '')

        result = {}
        scenario.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_pktgen_successful_sla(self):
        self.scenario_cfg['sla'] = {'max_ppm': 10000}
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        scenario._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = jsonutils.dumps({"packets_per_second": 9753,
                                         "errors": 0,
                                         "packets_sent": 149776,
                                         "packetsize": 60,
                                         "flows": 110,
                                         "ppm": 3179})
        self.mock_SSH.from_node().execute.return_value = (0, sample_output, '')

        result = {}
        scenario.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_pktgen_unsuccessful_sla(self):
        self.scenario_cfg['sla'] = {'max_ppm': 1000}
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        scenario._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = jsonutils.dumps({"packets_per_second": 9753,
                                         "errors": 0,
                                         "packets_sent": 149776,
                                         "packetsize": 60,
                                         "flows": 110})
        self.mock_SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, scenario.run, {})

    def test_pktgen_unsuccessful_script_error(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError
        self.assertRaises(y_exc.SSHError, scenario.run, {})

    def test_pktgen_get_vnic_driver_name(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, 'ixgbevf', '')

        vnic_driver_name = scenario._get_vnic_driver_name()
        self.assertEqual(vnic_driver_name, 'ixgbevf')

    def test_pktgen_unsuccessful_get_vnic_driver_name(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError

        self.assertRaises(y_exc.SSHError, scenario._get_vnic_driver_name)

    def test_pktgen_get_sriov_queue_number(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '2', '')

        scenario.queue_number = scenario._get_sriov_queue_number()
        self.assertEqual(scenario.queue_number, 2)

    def test_pktgen_unsuccessful_get_sriov_queue_number(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError

        self.assertRaises(y_exc.SSHError, scenario._get_sriov_queue_number)

    def test_pktgen_get_available_queue_number(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '4', '')

        self.assertEqual(scenario._get_available_queue_number(), 4)

        self.mock_SSH.from_node().execute.assert_called_with(
            "sudo ethtool -l eth0 | grep Combined | head -1 |"
            "awk '{printf $2}'", raise_on_error=True)

    def test_pktgen_unsuccessful_get_available_queue_number(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError

        self.assertRaises(y_exc.SSHError, scenario._get_available_queue_number)

    def test_pktgen_get_usable_queue_number(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '1', '')

        self.assertEqual(scenario._get_usable_queue_number(), 1)

        self.mock_SSH.from_node().execute.assert_called_with(
            "sudo ethtool -l eth0 | grep Combined | tail -1 |"
            "awk '{printf $2}'", raise_on_error=True)

    def test_pktgen_unsuccessful_get_usable_queue_number(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError

        self.assertRaises(y_exc.SSHError, scenario._get_usable_queue_number)

    def test_pktgen_enable_ovs_multiqueue(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        scenario._get_usable_queue_number = mock.Mock(return_value=1)
        scenario._get_available_queue_number = mock.Mock(return_value=4)

        scenario.queue_number = scenario._enable_ovs_multiqueue()
        self.assertEqual(scenario.queue_number, 4)
        self.mock_SSH.from_node().run.assert_has_calls(
            (mock.call("sudo ethtool -L eth0 combined 4"),
             mock.call("sudo ethtool -L eth0 combined 4")))

    def test_pktgen_enable_ovs_multiqueue_1q(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        scenario._get_usable_queue_number = mock.Mock(return_value=1)
        scenario._get_available_queue_number = mock.Mock(return_value=1)

        scenario.queue_number = scenario._enable_ovs_multiqueue()
        self.assertEqual(scenario.queue_number, 1)
        self.mock_SSH.from_node().run.assert_not_called()

    def test_pktgen_unsuccessful_enable_ovs_multiqueue(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().run.side_effect = y_exc.SSHError

        scenario._get_usable_queue_number = mock.Mock(return_value=1)
        scenario._get_available_queue_number = mock.Mock(return_value=4)

        self.assertRaises(y_exc.SSHError, scenario._enable_ovs_multiqueue)

    def test_pktgen_setup_irqmapping_ovs(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '10', '')

        scenario._setup_irqmapping_ovs(4)

        self.mock_SSH.from_node().run.assert_called_with(
            "echo 8 | sudo tee /proc/irq/10/smp_affinity")

    def test_pktgen_setup_irqmapping_ovs_1q(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '10', '')

        scenario._setup_irqmapping_ovs(1)

        self.mock_SSH.from_node().run.assert_called_with(
            "echo 1 | sudo tee /proc/irq/10/smp_affinity")

    def test_pktgen_unsuccessful_setup_irqmapping_ovs(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError

        self.assertRaises(y_exc.SSHError, scenario._setup_irqmapping_ovs, 4)

    def test_pktgen_unsuccessful_setup_irqmapping_ovs_1q(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError

        self.assertRaises(y_exc.SSHError, scenario._setup_irqmapping_ovs, 1)

    def test_pktgen_setup_irqmapping_sriov(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '10', '')

        scenario._setup_irqmapping_sriov(2)

        self.mock_SSH.from_node().run.assert_called_with(
            "echo 2 | sudo tee /proc/irq/10/smp_affinity")

    def test_pktgen_setup_irqmapping_sriov_1q(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '10', '')

        scenario._setup_irqmapping_sriov(1)

        self.mock_SSH.from_node().run.assert_called_with(
            "echo 1 | sudo tee /proc/irq/10/smp_affinity")

    def test_pktgen_unsuccessful_setup_irqmapping_sriov(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError

        self.assertRaises(y_exc.SSHError, scenario._setup_irqmapping_sriov, 2)

    def test_pktgen_unsuccessful_setup_irqmapping_sriov_1q(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError

        self.assertRaises(y_exc.SSHError, scenario._setup_irqmapping_sriov, 1)

    def test_pktgen_is_irqbalance_disabled(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '', '')

        result = scenario._is_irqbalance_disabled()
        self.assertFalse(result)

        self.mock_SSH.from_node().execute.assert_called_with(
            "grep ENABLED /etc/default/irqbalance", raise_on_error=True)

    def test_pktgen_unsuccessful_is_irqbalance_disabled(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.side_effect = y_exc.SSHError

        self.assertRaises(y_exc.SSHError, scenario._is_irqbalance_disabled)

    def test_pktgen_disable_irqbalance(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        scenario._disable_irqbalance()

        self.mock_SSH.from_node().run.assert_called_with(
            "sudo service irqbalance disable")

    def test_pktgen_unsuccessful_disable_irqbalance(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().run.side_effect = y_exc.SSHError

        self.assertRaises(y_exc.SSHError, scenario._disable_irqbalance)

    def test_pktgen_multiqueue_setup_ovs(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '4', '')

        scenario._is_irqbalance_disabled = mock.Mock(return_value=False)
        scenario._get_vnic_driver_name = mock.Mock(return_value="virtio_net")
        scenario._get_usable_queue_number = mock.Mock(return_value=1)
        scenario._get_available_queue_number = mock.Mock(return_value=4)

        scenario.multiqueue_setup()

        self.assertEqual(scenario.queue_number, 4)
        self.assertTrue(scenario.multiqueue_setup_done)

    def test_pktgen_multiqueue_setup_ovs_1q(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '1', '')

        scenario._is_irqbalance_disabled = mock.Mock(return_value=False)
        scenario._get_vnic_driver_name = mock.Mock(return_value="virtio_net")
        scenario._get_usable_queue_number = mock.Mock(return_value=1)
        scenario._get_available_queue_number = mock.Mock(return_value=1)

        scenario.multiqueue_setup()

        self.assertEqual(scenario.queue_number, 1)
        self.assertTrue(scenario.multiqueue_setup_done)

    def test_pktgen_multiqueue_setup_sriov(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '2', '')

        scenario._is_irqbalance_disabled = mock.Mock(return_value=False)
        scenario._get_vnic_driver_name = mock.Mock(return_value="ixgbevf")

        scenario.multiqueue_setup()

        self.assertEqual(scenario.queue_number, 2)
        self.assertTrue(scenario.multiqueue_setup_done)

    def test_pktgen_multiqueue_setup_sriov_1q(self):
        scenario = Pktgen(self.scenario_cfg, self.context_cfg)
        scenario.setup()

        self.mock_SSH.from_node().execute.return_value = (0, '1', '')

        scenario._is_irqbalance_disabled = mock.Mock(return_value=False)
        scenario._get_vnic_driver_name = mock.Mock(return_value="ixgbevf")

        scenario.multiqueue_setup()

        self.assertEqual(scenario.queue_number, 1)
        self.assertTrue(scenario.multiqueue_setup_done)

    def test_pktgen_run_with_setup_done(self):
        scenario_cfg = {
            'options': {
                'packetsize': 60,
                'number_of_ports': 10,
                'duration': 20,
                'multiqueue': True},
            'sla': {
                'max_ppm': 1}
        }
        scenario = Pktgen(scenario_cfg, self.context_cfg)
        scenario.server = self.mock_SSH.from_node()
        scenario.client = self.mock_SSH.from_node()

        scenario.setup_done = True
        scenario.multiqueue_setup_done = True

        scenario._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = jsonutils.dumps({"packets_per_second": 9753,
                                         "errors": 0,
                                         "packets_sent": 149300,
                                         "flows": 110,
                                         "ppm": 0})
        self.mock_SSH.from_node().execute.return_value = (0, sample_output, '')

        result = {}
        scenario.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_pktgen_run_with_ovs_multiqueque(self):
        scenario_cfg = {
            'options': {
                'packetsize': 60,
                'number_of_ports': 10,
                'duration': 20,
                'multiqueue': True},
            'sla': {'max_ppm': 1}
        }
        scenario = Pktgen(scenario_cfg, self.context_cfg)
        scenario.setup()

        scenario._get_vnic_driver_name = mock.Mock(return_value="virtio_net")
        scenario._get_usable_queue_number = mock.Mock(return_value=1)
        scenario._get_available_queue_number = mock.Mock(return_value=4)
        scenario._enable_ovs_multiqueue = mock.Mock(return_value=4)
        scenario._setup_irqmapping_ovs = mock.Mock()
        scenario._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = jsonutils.dumps({"packets_per_second": 9753,
                                         "errors": 0,
                                         "packets_sent": 149300,
                                         "flows": 110,
                                         "ppm": 0})
        self.mock_SSH.from_node().execute.return_value = (0, sample_output, '')

        result = {}
        scenario.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)

    def test_pktgen_run_with_sriov_multiqueque(self):
        scenario_cfg = {
            'options': {
                'packetsize': 60,
                'number_of_ports': 10,
                'duration': 20,
                'multiqueue': True},
            'sla': {'max_ppm': 1}
        }
        scenario = Pktgen(scenario_cfg, self.context_cfg)
        scenario.setup()

        scenario._get_vnic_driver_name = mock.Mock(return_value="ixgbevf")
        scenario._get_sriov_queue_number = mock.Mock(return_value=2)
        scenario._setup_irqmapping_sriov = mock.Mock()
        scenario._iptables_get_result = mock.Mock(return_value=149300)

        sample_output = jsonutils.dumps({"packets_per_second": 9753,
                                         "errors": 0,
                                         "packets_sent": 149300,
                                         "flows": 110,
                                         "ppm": 0})
        self.mock_SSH.from_node().execute.return_value = (0, sample_output, '')

        result = {}
        scenario.run(result)
        expected_result = jsonutils.loads(sample_output)
        expected_result["packets_received"] = 149300
        expected_result["packetsize"] = 60
        self.assertEqual(result, expected_result)
