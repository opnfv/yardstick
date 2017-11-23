# Copyright (c) 2016-2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import unittest

import os

from yardstick.error import IncorrectConfig, SSHError
from yardstick.error import IncorrectNodeSetup
from yardstick.error import IncorrectSetup
from yardstick.network_services.helpers.dpdkbindnic_helper import DpdkInterface
from yardstick.network_services.helpers.dpdkbindnic_helper import DpdkNode
from yardstick.network_services.helpers.dpdkbindnic_helper import DpdkBindHelper
from yardstick.network_services.helpers.dpdkbindnic_helper import DpdkBindHelperException
from yardstick.network_services.helpers.dpdkbindnic_helper import NETWORK_KERNEL
from yardstick.network_services.helpers.dpdkbindnic_helper import NETWORK_DPDK
from yardstick.network_services.helpers.dpdkbindnic_helper import CRYPTO_KERNEL
from yardstick.network_services.helpers.dpdkbindnic_helper import CRYPTO_DPDK
from yardstick.network_services.helpers.dpdkbindnic_helper import NETWORK_OTHER
from yardstick.network_services.helpers.dpdkbindnic_helper import CRYPTO_OTHER


NAME = "tg_0"


class TestDpdkInterface(unittest.TestCase):

    SAMPLE_NETDEVS = {
        'enp11s0': {
            'address': '0a:de:ad:be:ef:f5',
            'device': '0x1533',
            'driver': 'igb',
            'ifindex': '2',
            'interface_name': 'enp11s0',
            'operstate': 'down',
            'pci_bus_id': '0000:0b:00.0',
            'subsystem_device': '0x1533',
            'subsystem_vendor': '0x15d9',
            'vendor': '0x8086'
        },
        'lan': {
            'address': '0a:de:ad:be:ef:f4',
            'device': '0x153a',
            'driver': 'e1000e',
            'ifindex': '3',
            'interface_name': 'lan',
            'operstate': 'up',
            'pci_bus_id': '0000:00:19.0',
            'subsystem_device': '0x153a',
            'subsystem_vendor': '0x15d9',
            'vendor': '0x8086'
        }
    }

    SAMPLE_VM_NETDEVS = {
        'eth1': {
            'address': 'fa:de:ad:be:ef:5b',
            'device': '0x0001',
            'driver': 'virtio_net',
            'ifindex': '3',
            'interface_name': 'eth1',
            'operstate': 'down',
            'pci_bus_id': '0000:00:04.0',
            'vendor': '0x1af4'
        }
    }

    def test_parse_netdev_info(self):
        output = """\
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/ifindex:2
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/address:0a:de:ad:be:ef:f5
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/operstate:down
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/device/vendor:0x8086
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/device/device:0x1533
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/device/subsystem_vendor:0x15d9
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/device/subsystem_device:0x1533
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/driver:igb
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/pci_bus_id:0000:0b:00.0
/sys/devices/pci0000:00/0000:00:19.0/net/lan/ifindex:3
/sys/devices/pci0000:00/0000:00:19.0/net/lan/address:0a:de:ad:be:ef:f4
/sys/devices/pci0000:00/0000:00:19.0/net/lan/operstate:up
/sys/devices/pci0000:00/0000:00:19.0/net/lan/device/vendor:0x8086
/sys/devices/pci0000:00/0000:00:19.0/net/lan/device/device:0x153a
/sys/devices/pci0000:00/0000:00:19.0/net/lan/device/subsystem_vendor:0x15d9
/sys/devices/pci0000:00/0000:00:19.0/net/lan/device/subsystem_device:0x153a
/sys/devices/pci0000:00/0000:00:19.0/net/lan/driver:e1000e
/sys/devices/pci0000:00/0000:00:19.0/net/lan/pci_bus_id:0000:00:19.0
"""
        res = DpdkBindHelper.parse_netdev_info(output)
        self.assertDictEqual(res, self.SAMPLE_NETDEVS)

    def test_parse_netdev_info_virtio(self):
        output = """\
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/ifindex:3
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/address:fa:de:ad:be:ef:5b
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/operstate:down
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/device/vendor:0x1af4
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/device/device:0x0001
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/driver:virtio_net
"""
        res = DpdkBindHelper.parse_netdev_info(output)
        self.assertDictEqual(res, self.SAMPLE_VM_NETDEVS)

    def test_probe_missing_values(self):
        mock_dpdk_node = mock.Mock()
        mock_dpdk_node.netdevs = self.SAMPLE_NETDEVS.copy()

        interface = {'local_mac': '0a:de:ad:be:ef:f5'}
        dpdk_intf = DpdkInterface(mock_dpdk_node, interface)

        dpdk_intf.probe_missing_values()
        self.assertEqual(interface['vpci'], '0000:0b:00.0')

        interface['local_mac'] = '0a:de:ad:be:ef:f4'
        dpdk_intf.probe_missing_values()
        self.assertEqual(interface['vpci'], '0000:00:19.0')

    def test_probe_missing_values_no_update(self):
        mock_dpdk_node = mock.Mock()
        mock_dpdk_node.netdevs = self.SAMPLE_NETDEVS.copy()
        del mock_dpdk_node.netdevs['enp11s0']['driver']
        del mock_dpdk_node.netdevs['lan']['driver']

        interface = {'local_mac': '0a:de:ad:be:ef:f5'}
        dpdk_intf = DpdkInterface(mock_dpdk_node, interface)

        dpdk_intf.probe_missing_values()
        self.assertNotIn('vpci', interface)
        self.assertNotIn('driver', interface)

    def test_probe_missing_values_negative(self):
        mock_dpdk_node = mock.Mock()
        mock_dpdk_node.netdevs.values.side_effect = IncorrectNodeSetup

        interface = {'local_mac': '0a:de:ad:be:ef:f5'}
        dpdk_intf = DpdkInterface(mock_dpdk_node, interface)

        with self.assertRaises(IncorrectConfig):
            dpdk_intf.probe_missing_values()


class TestDpdkNode(unittest.TestCase):

    INTERFACES = [
        {'name': 'name1',
         'virtual-interface': {
             'local_mac': 404,
             'vpci': 'pci10',
         }},
        {'name': 'name2',
         'virtual-interface': {
             'local_mac': 404,
             'vpci': 'pci2',
         }},
        {'name': 'name3',
         'virtual-interface': {
             'local_mac': 404,
             'vpci': 'some-pci1',
         }},
    ]

    def test_probe_dpdk_drivers(self):
        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.return_value = 0, '', ''

        interfaces = [
            {'name': 'name1',
             'virtual-interface': {
                 'local_mac': 404,
                 'vpci': 'pci10',
             }},
            {'name': 'name2',
             'virtual-interface': {
                 'local_mac': 404,
                 'vpci': 'pci2',
             }},
            {'name': 'name3',
             'virtual-interface': {
                 'local_mac': 404,
                 'vpci': 'some-pci1',
             }},
        ]

        dpdk_node = DpdkNode(NAME, interfaces, mock_ssh_helper)
        dpdk_helper = dpdk_node.dpdk_helper

        dpdk_helper.probe_real_kernel_drivers = mock.Mock()
        dpdk_helper.real_kernel_interface_driver_map = {
            'pci1': 'driver1',
            'pci2': 'driver2',
            'pci3': 'driver3',
            'pci4': 'driver1',
            'pci6': 'driver3',
        }

        dpdk_node._probe_dpdk_drivers()
        self.assertNotIn('driver', interfaces[0]['virtual-interface'])
        self.assertEqual(interfaces[1]['virtual-interface']['driver'], 'driver2')
        self.assertEqual(interfaces[2]['virtual-interface']['driver'], 'driver1')

    def test_check(self):
        def update():
            if not mock_force_rebind.called:
                raise IncorrectConfig

            interfaces[0]['virtual-interface'].update({
                'vpci': '0000:01:02.1',
                'local_ip': '10.20.30.40',
                'netmask': '255.255.0.0',
                'driver': 'ixgbe',
            })

        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.return_value = 0, '', ''

        interfaces = [
            {'name': 'name1',
             'virtual-interface': {
                 'local_mac': 404,
             }},
        ]

        dpdk_node = DpdkNode(NAME, interfaces, mock_ssh_helper)
        dpdk_node._probe_missing_values = mock_probe_missing = mock.Mock(side_effect=update)
        dpdk_node._force_rebind = mock_force_rebind = mock.Mock()

        self.assertIsNone(dpdk_node.check())
        self.assertEqual(mock_probe_missing.call_count, 2)

    @mock.patch('yardstick.network_services.helpers.dpdkbindnic_helper.DpdkInterface')
    def test_check_negative(self, mock_intf_type):
        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.return_value = 0, '', ''

        mock_intf_type().check.side_effect = SSHError

        dpdk_node = DpdkNode(NAME, self.INTERFACES, mock_ssh_helper)

        with self.assertRaises(IncorrectSetup):
            dpdk_node.check()

    def test_probe_netdevs(self):
        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.return_value = 0, '', ''

        expected = {'key1': 500, 'key2': 'hello world'}
        update = {'key1': 1000, 'key3': []}

        dpdk_node = DpdkNode(NAME, self.INTERFACES, mock_ssh_helper)
        dpdk_helper = dpdk_node.dpdk_helper
        dpdk_helper.find_net_devices = mock.Mock(side_effect=[expected, update])

        self.assertDictEqual(dpdk_node.netdevs, {})
        dpdk_node._probe_netdevs()
        self.assertDictEqual(dpdk_node.netdevs, expected)

        expected = {'key1': 1000, 'key2': 'hello world', 'key3': []}
        dpdk_node._probe_netdevs()
        self.assertDictEqual(dpdk_node.netdevs, expected)

    def test_probe_netdevs_setup_negative(self):
        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.return_value = 0, '', ''

        dpdk_node = DpdkNode(NAME, self.INTERFACES, mock_ssh_helper)
        dpdk_helper = dpdk_node.dpdk_helper
        dpdk_helper.find_net_devices = mock.Mock(side_effect=DpdkBindHelperException)

        with self.assertRaises(DpdkBindHelperException):
            dpdk_node._probe_netdevs()

    def test_force_rebind(self):
        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.return_value = 0, '', ''

        dpdk_node = DpdkNode(NAME, self.INTERFACES, mock_ssh_helper)
        dpdk_helper = dpdk_node.dpdk_helper
        dpdk_helper.force_dpdk_rebind = mock_helper_func = mock.Mock()

        dpdk_node._force_rebind()
        self.assertEqual(mock_helper_func.call_count, 1)


class TestDpdkBindHelper(unittest.TestCase):
    bin_path = "/opt/nsb_bin"
    EXAMPLE_OUTPUT = """

Network devices using DPDK-compatible driver
============================================
0000:00:04.0 'Virtio network device' drv=igb_uio unused=
0000:00:05.0 'Virtio network device' drv=igb_uio unused=

Network devices using kernel driver
===================================
0000:00:03.0 'Virtio network device' if=ens3 drv=virtio-pci unused=igb_uio *Active*

Other network devices
=====================
<none>

Crypto devices using DPDK-compatible driver
===========================================
<none>

Crypto devices using kernel driver
==================================
<none>

Other crypto devices
====================
<none>
"""

    PARSED_EXAMPLE = {
        NETWORK_DPDK: [
            {'active': False,
             'dev_type': 'Virtio network device',
             'driver': 'igb_uio',
             'iface': None,
             'unused': '',
             'vpci': '0000:00:04.0',
             },
            {'active': False,
             'dev_type': 'Virtio network device',
             'driver': 'igb_uio',
             'iface': None,
             'unused': '',
             'vpci': '0000:00:05.0',
             }
        ],
        NETWORK_KERNEL: [
            {'active': True,
             'dev_type': 'Virtio network device',
             'driver': 'virtio-pci',
             'iface': 'ens3',
             'unused': 'igb_uio',
             'vpci': '0000:00:03.0',
             }
        ],
        CRYPTO_KERNEL: [],
        CRYPTO_DPDK: [],
        NETWORK_OTHER: [],
        CRYPTO_OTHER: [],
    }

    CLEAN_STATUS = {
        NETWORK_KERNEL: [],
        NETWORK_DPDK: [],
        CRYPTO_KERNEL: [],
        CRYPTO_DPDK: [],
        NETWORK_OTHER: [],
        CRYPTO_OTHER: [],
    }

    ONE_INPUT_LINE = ("0000:00:03.0 'Virtio network device' if=ens3 "
                      "drv=virtio-pci unused=igb_uio *Active*")

    ONE_INPUT_LINE_PARSED = [{
        'vpci': '0000:00:03.0',
        'dev_type': 'Virtio network device',
        'iface': 'ens3',
        'driver': 'virtio-pci',
        'unused': 'igb_uio',
        'active': True,
    }]

    def test___init__(self):
        conn = mock.Mock()
        conn.provision_tool = mock.Mock(return_value='path_to_tool')
        conn.join_bin_path.return_value = os.path.join(self.bin_path, DpdkBindHelper.DPDK_DEVBIND)

        dpdk_bind_helper = DpdkBindHelper(conn)

        self.assertEqual(conn, dpdk_bind_helper.ssh_helper)
        self.assertEqual(self.CLEAN_STATUS, dpdk_bind_helper.dpdk_status)
        self.assertIsNone(dpdk_bind_helper.status_nic_row_re)
        self.assertEqual(dpdk_bind_helper.dpdk_devbind,
                         os.path.join(self.bin_path, dpdk_bind_helper.DPDK_DEVBIND))
        self.assertIsNone(dpdk_bind_helper._status_cmd_attr)

    def test__dpdk_execute(self):
        conn = mock.Mock()
        conn.execute = mock.Mock(return_value=(0, 'output', 'error'))
        conn.provision_tool = mock.Mock(return_value='tool_path')
        dpdk_bind_helper = DpdkBindHelper(conn)
        self.assertEqual((0, 'output', 'error'), dpdk_bind_helper._dpdk_execute('command'))

    def test__dpdk_execute_failure(self):
        conn = mock.Mock()
        conn.execute = mock.Mock(return_value=(1, 'output', 'error'))
        conn.provision_tool = mock.Mock(return_value='tool_path')
        dpdk_bind_helper = DpdkBindHelper(conn)
        with self.assertRaises(DpdkBindHelperException):
            dpdk_bind_helper._dpdk_execute('command')

    def test__addline(self):
        conn = mock.Mock()

        dpdk_bind_helper = DpdkBindHelper(conn)

        dpdk_bind_helper._add_line(NETWORK_KERNEL, self.ONE_INPUT_LINE)

        self.assertIsNotNone(dpdk_bind_helper.dpdk_status)
        self.assertEqual(self.ONE_INPUT_LINE_PARSED, dpdk_bind_helper.dpdk_status[NETWORK_KERNEL])

    def test__switch_active_dict_by_header(self):
        line = "Crypto devices using DPDK-compatible driver"
        olddict = 'olddict'
        self.assertEqual(CRYPTO_DPDK, DpdkBindHelper._switch_active_dict(line, olddict))

    def test__switch_active_dict_by_header_empty(self):
        line = "<none>"
        olddict = 'olddict'
        self.assertEqual(olddict, DpdkBindHelper._switch_active_dict(line, olddict))

    def test_parse_dpdk_status_output(self):
        conn = mock.Mock()

        dpdk_bind_helper = DpdkBindHelper(conn)

        dpdk_bind_helper._parse_dpdk_status_output(self.EXAMPLE_OUTPUT)

        self.maxDiff = None
        self.assertEqual(self.PARSED_EXAMPLE, dpdk_bind_helper.dpdk_status)

    def test_kernel_bound_pci_addresses(self):
        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.return_value = 0, '', ''

        expected = ['a', 'b', 3]

        dpdk_helper = DpdkBindHelper(mock_ssh_helper)
        dpdk_helper.dpdk_status = {
            NETWORK_DPDK: [{'vpci': 4}, {'vpci': 5}, {'vpci': 'g'}],
            NETWORK_KERNEL: [{'vpci': 'a'}, {'vpci': 'b'}, {'vpci': 3}],
            CRYPTO_DPDK: [],
        }

        result = dpdk_helper.kernel_bound_pci_addresses
        self.assertEqual(result, expected)

    def test_find_net_devices_negative(self):
        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.return_value = 1, 'error', 'debug'

        dpdk_helper = DpdkBindHelper(mock_ssh_helper)

        self.assertDictEqual(dpdk_helper.find_net_devices(), {})

    def test_read_status(self):
        conn = mock.Mock()
        conn.execute = mock.Mock(return_value=(0, self.EXAMPLE_OUTPUT, ''))
        conn.provision_tool = mock.Mock(return_value='path_to_tool')

        dpdk_bind_helper = DpdkBindHelper(conn)

        self.assertEqual(self.PARSED_EXAMPLE, dpdk_bind_helper.read_status())

    def test__get_bound_pci_addresses(self):
        conn = mock.Mock()

        dpdk_bind_helper = DpdkBindHelper(conn)

        dpdk_bind_helper._parse_dpdk_status_output(self.EXAMPLE_OUTPUT)

        self.assertEqual(['0000:00:04.0', '0000:00:05.0'],
                          dpdk_bind_helper._get_bound_pci_addresses(NETWORK_DPDK))
        self.assertEqual(['0000:00:03.0'],
                          dpdk_bind_helper._get_bound_pci_addresses(NETWORK_KERNEL))

    def test_interface_driver_map(self):
        conn = mock.Mock()

        dpdk_bind_helper = DpdkBindHelper(conn)

        dpdk_bind_helper._parse_dpdk_status_output(self.EXAMPLE_OUTPUT)

        self.assertEqual({'0000:00:04.0': 'igb_uio',
                          '0000:00:03.0': 'virtio-pci',
                          '0000:00:05.0': 'igb_uio',
                          },
                         dpdk_bind_helper.interface_driver_map)

    def test_bind(self):
        conn = mock.Mock()
        conn.execute = mock.Mock(return_value=(0, '', ''))
        conn.join_bin_path.return_value = os.path.join(self.bin_path, DpdkBindHelper.DPDK_DEVBIND)

        dpdk_bind_helper = DpdkBindHelper(conn)
        dpdk_bind_helper.read_status = mock.Mock()

        dpdk_bind_helper.bind(['0000:00:03.0', '0000:00:04.0'], 'my_driver')

        conn.execute.assert_called_with('sudo /opt/nsb_bin/dpdk-devbind.py --force '
                                        '-b my_driver 0000:00:03.0 0000:00:04.0')
        dpdk_bind_helper.read_status.assert_called_once()

    def test_bind_single_pci(self):
        conn = mock.Mock()
        conn.execute = mock.Mock(return_value=(0, '', ''))
        conn.join_bin_path.return_value = os.path.join(self.bin_path, DpdkBindHelper.DPDK_DEVBIND)

        dpdk_bind_helper = DpdkBindHelper(conn)
        dpdk_bind_helper.read_status = mock.Mock()

        dpdk_bind_helper.bind('0000:00:03.0', 'my_driver')

        conn.execute.assert_called_with('sudo /opt/nsb_bin/dpdk-devbind.py --force '
                                        '-b my_driver 0000:00:03.0')
        dpdk_bind_helper.read_status.assert_called_once()

    def test_rebind_drivers(self):
        conn = mock.Mock()

        dpdk_bind_helper = DpdkBindHelper(conn)

        dpdk_bind_helper.bind = mock.Mock()
        dpdk_bind_helper.used_drivers = {
            'd1': ['0000:05:00.0'],
            'd3': ['0000:05:01.0', '0000:05:02.0'],
        }

        dpdk_bind_helper.rebind_drivers()

        dpdk_bind_helper.bind.assert_any_call(['0000:05:00.0'], 'd1', True)
        dpdk_bind_helper.bind.assert_any_call(['0000:05:01.0', '0000:05:02.0'], 'd3', True)

    def test_save_used_drivers(self):
        conn = mock.Mock()
        dpdk_bind_helper = DpdkBindHelper(conn)
        dpdk_bind_helper.dpdk_status = self.PARSED_EXAMPLE

        dpdk_bind_helper.save_used_drivers()

        expected = {
            'igb_uio': ['0000:00:04.0', '0000:00:05.0'],
            'virtio-pci': ['0000:00:03.0'],
        }

        self.assertDictEqual(expected, dpdk_bind_helper.used_drivers)

    def test_force_dpdk_rebind(self):
        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.return_value = 0, '', ''

        dpdk_helper = DpdkBindHelper(mock_ssh_helper, 'driver2')
        dpdk_helper.dpdk_status = {
            NETWORK_DPDK: [
                {
                    'vpci': 'pci1',
                },
                {
                    'vpci': 'pci3',
                },
                {
                    'vpci': 'pci6',
                },
                {
                    'vpci': 'pci3',
                },
            ]
        }
        dpdk_helper.real_kernel_interface_driver_map = {
            'pci1': 'real_driver1',
            'pci2': 'real_driver2',
            'pci3': 'real_driver1',
            'pci4': 'real_driver4',
            'pci6': 'real_driver6',
        }
        dpdk_helper.load_dpdk_driver = mock.Mock()
        dpdk_helper.read_status = mock.Mock()
        dpdk_helper.save_real_kernel_interface_driver_map = mock.Mock()
        dpdk_helper.save_used_drivers = mock.Mock()
        dpdk_helper.bind = mock_bind = mock.Mock()

        dpdk_helper.force_dpdk_rebind()
        self.assertEqual(mock_bind.call_count, 2)

    def test_save_real_kernel_drivers(self):
        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.return_value = 0, '', ''

        dpdk_helper = DpdkBindHelper(mock_ssh_helper)
        dpdk_helper.real_kernel_drivers = {
            'abc': '123',
        }
        dpdk_helper.real_kernel_interface_driver_map = {
            'abc': 'AAA',
            'def': 'DDD',
            'abs': 'AAA',
            'ghi': 'GGG',
        }

        # save_used_drivers must be called before save_real_kernel_drivers can be
        with self.assertRaises(AttributeError):
            dpdk_helper.save_real_kernel_drivers()

        dpdk_helper.save_used_drivers()

        expected_used_drivers = {
            'AAA': ['abc', 'abs'],
            'DDD': ['def'],
            'GGG': ['ghi'],
        }
        dpdk_helper.save_real_kernel_drivers()
        self.assertDictEqual(dpdk_helper.used_drivers, expected_used_drivers)
        self.assertDictEqual(dpdk_helper.real_kernel_drivers, {})

    def test_get_real_kernel_driver(self):
        mock_ssh_helper = mock.Mock()
        mock_ssh_helper.execute.side_effect = [
            (0, 'non-matching text', ''),
            (0, 'pre Kernel modules: real_driver1', ''),
            (0, 'before Ethernet middle Virtio network device after', ''),
        ]

        dpdk_helper = DpdkBindHelper(mock_ssh_helper)

        self.assertIsNone(dpdk_helper.get_real_kernel_driver('abc'))
        self.assertEqual(dpdk_helper.get_real_kernel_driver('abc'), 'real_driver1')
        self.assertEqual(dpdk_helper.get_real_kernel_driver('abc'), DpdkBindHelper.VIRTIO_DRIVER)
