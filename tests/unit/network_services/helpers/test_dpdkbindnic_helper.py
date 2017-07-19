#!/usr/bin/env python

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

import re
import mock
import unittest
from yardstick.network_services.helpers.dpdknicbind_helper import DpdkNicBindHelper
from yardstick.network_services.helpers.dpdknicbind_helper import KERNEL
from yardstick.network_services.helpers.dpdknicbind_helper import DPDK


class TestDpdkNicBindHelper(unittest.TestCase):

    EXAMPLE_OUTPUT="""

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
			'dpdk': [
                {'active': False,
                 'dev_type': 'Virtio network device',
                 'driver': 'igb_uio',
                 'iface': None,
                 'unused': '',
                 'vpci': '0000:00:04.0'},
                {'active': False,
                 'dev_type': 'Virtio network device',
                 'driver': 'igb_uio',
                 'iface': None,
                 'unused': '',
                 'vpci': '0000:00:05.0'}
            ],
            'kernel': [
                {'active': True,
                 'dev_type': 'Virtio network device',
                 'driver': 'virtio-pci',
                 'iface': 'ens3',
                 'unused': 'igb_uio',
                 'vpci': '0000:00:03.0'}],
            'other': []}

    def test___init__(self):
        conn = mock.Mock()
        conn.provision_tool = mock.Mock(return_value='path_to_tool')

        dpdk_nic_bind_helper = DpdkNicBindHelper(conn)

        self.assertEquals(conn, dpdk_nic_bind_helper.ssh_helper)
        self.assertEquals({
                KERNEL : [],
                DPDK: [],
                'other': [],
            },
            dpdk_nic_bind_helper.dpdk_status)
        self.assertIsNone(dpdk_nic_bind_helper.status_nic_row_re)
        self.assertEquals('path_to_tool', dpdk_nic_bind_helper.dpdk_nic_bind)

    def test__addline(self):
        conn = mock.Mock()
        line = "0000:00:03.0 'Virtio network device' if=ens3 drv=virtio-pci unused=igb_uio *Active*"

        dpdk_nic_bind_helper = DpdkNicBindHelper(conn)

        dpdk_nic_bind_helper._addline(KERNEL, line)

        self.assertIsNotNone(dpdk_nic_bind_helper.dpdk_status)
        self.assertEquals([{
            'vpci': '0000:00:03.0',
            'dev_type': 'Virtio network device',
            'iface': 'ens3',
            'driver': 'virtio-pci',
            'unused': 'igb_uio',
            'active': True,
        }], dpdk_nic_bind_helper.dpdk_status[KERNEL])


    def test_parse_dpdk_status_output(self):
        conn = mock.Mock()

        dpdk_nic_bind_helper = DpdkNicBindHelper(conn)
        dpdk_nic_bind_helper.parse_dpdk_status_output(self.EXAMPLE_OUTPUT)

        self.maxDiff = None
        self.assertEquals(self.PARSED_EXAMPLE, dpdk_nic_bind_helper.dpdk_status)

    def test_read_status(self):
        conn = mock.Mock()
        conn.execute = mock.Mock(return_value=(0, self.EXAMPLE_OUTPUT, ''))
        conn.provision_tool = mock.Mock(return_value='path_to_tool')

        dpdk_nic_bind_helper = DpdkNicBindHelper(conn)

        self.assertEquals(self.PARSED_EXAMPLE, dpdk_nic_bind_helper.read_status())

    def test__get_bound_pci_addresses(self):
        conn = mock.Mock()

        dpdk_nic_bind_helper = DpdkNicBindHelper(conn)

        dpdk_nic_bind_helper.parse_dpdk_status_output(self.EXAMPLE_OUTPUT)

        self.assertEquals(['0000:00:04.0', '0000:00:05.0'],
                          dpdk_nic_bind_helper._get_bound_pci_addresses(DPDK))
        self.assertEquals(['0000:00:03.0'],
                          dpdk_nic_bind_helper._get_bound_pci_addresses(KERNEL))

    def test_interface_driver_map(self):
        conn = mock.Mock()

        dpdk_nic_bind_helper = DpdkNicBindHelper(conn)

        dpdk_nic_bind_helper.parse_dpdk_status_output(self.EXAMPLE_OUTPUT)

        self.assertEquals({'0000:00:04.0': 'igb_uio',
                           '0000:00:03.0': 'virtio-pci',
                           '0000:00:05.0': 'igb_uio',
                           },
                          dpdk_nic_bind_helper.interface_driver_map)

    def test_bind(self):
        conn = mock.Mock()
        conn.execute = mock.Mock(return_value=(0, '', ''))
        conn.provision_tool = mock.Mock(return_value='/opt/nsb_bin/dpdk_nic_bind.py')

        dpdk_nic_bind_helper = DpdkNicBindHelper(conn)
        dpdk_nic_bind_helper.read_status = mock.Mock()

        dpdk_nic_bind_helper.bind(['0000:00:03.0', '0000:00:04.0'], 'my_driver')

        conn.execute.assert_called_with('sudo /opt/nsb_bin/dpdk_nic_bind.py --force -b my_driver 0000:00:03.0 0000:00:04.0')
        dpdk_nic_bind_helper.read_status.assert_called_once()

