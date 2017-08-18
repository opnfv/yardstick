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
#

# Unittest for yardstick.benchmark.contexts.standalone

from __future__ import absolute_import

import os
import unittest

import mock

from yardstick.benchmark.contexts import standalone
from yardstick.benchmark.contexts.standalone import ovsdpdk, sriov

MOCKS = {
    'yardstick.benchmark.contexts': mock.MagicMock(),
    'yardstick.benchmark.contexts.standalone.sriov': mock.MagicMock(),
    'yardstick.benchmark.contexts.standalone.ovsdpdk': mock.MagicMock(),
    'yardstick.benchmark.contexts.standalone': mock.MagicMock(),
}


@mock.patch('yardstick.benchmark.contexts.standalone.ovsdpdk.time')
@mock.patch('yardstick.benchmark.contexts.standalone.time')
@mock.patch('yardstick.benchmark.contexts.standalone.sriov.time')
class StandaloneContextTestCase(unittest.TestCase):
    NODES_SAMPLE = "nodes_sample_new.yaml"
    NODES_SAMPLE_SRIOV = "nodes_sample_new_sriov.yaml"
    NODES_DUPLICATE_SAMPLE = "nodes_duplicate_sample_new.yaml"

    NODES_SAMPLE_OVSDPDK = "nodes_sample_ovs.yaml"
    NODES_SAMPLE_OVSDPDK_ROLE = "nodes_sample_ovsdpdk.yaml"
    NODES_DUPLICATE_OVSDPDK = "nodes_duplicate_sample_ovs.yaml"

    def setUp(self):
        self.test_context = standalone.StandaloneContext()

    def test_construct(self, mock_sriov_time, mock_standlalone_time, mock_ovsdpdk_time):
        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.file_path)
        self.assertEqual(self.test_context.nodes, [])
        self.assertEqual(self.test_context.nfvi_node, [])

    def test_unsuccessful_init(self, mock_sriov_time, mock_standlalone_time, mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath("error_file")
        }
        self.assertRaises(IOError, self.test_context.init, attrs)

    def test_successful_init_sriov(self, mock_sriov_time, mock_standlalone_time,
                                   mock_ovsdpdk_time):
        attrs_sriov = {
            'name': 'sriov',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.223.197.140',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'intel123',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.get_nfvi_obj = mock.Mock()
        self.test_context.init(attrs_sriov)
        self.assertEqual(self.test_context.name, "sriov")
        self.assertEqual(len(self.test_context.nodes), 2)
        self.assertEqual(len(self.test_context.nfvi_node), 2)
        self.assertEqual(self.test_context.nfvi_node[0]["name"], "sriov")

    def test_successful_init_ovs(self, mock_sriov_time, mock_standlalone_time, mock_ovsdpdk_time):
        attrs_ovs = {
            'name': 'ovs',
            'file': self._get_file_abspath(self.NODES_SAMPLE_OVSDPDK)
        }
        self.test_context.nfvi_node = [{
            'name': 'ovs',
            'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
            'ip': '10.223.197.140',
            'role': 'Ovsdpdk',
            'user': 'root',
            'vpath': '/usr/local/',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.get_nfvi_obj = mock.Mock()
        self.test_context.init(attrs_ovs)
        self.assertEqual(self.test_context.name, "ovs")
        self.assertEqual(len(self.test_context.nodes), 2)
        self.assertEqual(len(self.test_context.nfvi_node), 2)
        self.assertEqual(self.test_context.nfvi_node[0]["name"], "ovs")

    def test__get_server_with_dic_attr_name_sriov(self, mock_sriov_time, mock_standlalone_time,
                                                  mock_ovsdpdk_time):
        attrs_sriov = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.223.197.140',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'intel123',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.init(attrs_sriov)
        attr_name = {'name': 'foo.bar'}
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result, None)

    def test__get_server_with_dic_attr_name_ovs(self, mock_sriov_time, mock_standlalone_time,
                                                mock_ovsdpdk_time):
        attrs_ovs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE_OVSDPDK)
        }
        self.test_context.nfvi_node = [{
            'name': 'ovs',
            'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
            'ip': '10.223.197.140',
            'role': 'Ovsdpdk',
            'user': 'root',
            'vpath': '/usr/local/',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'intel123',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.init(attrs_ovs)
        attr_name = {'name': 'foo.bar'}
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result, None)

    def test__get_server_not_found_sriov(self, mock_sriov_time, mock_standlalone_time,
                                         mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.223.197.140',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.init(attrs)
        attr_name = 'bar.foo'
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result, None)

    def test__get_server_not_found_ovs(self, mock_sriov_time, mock_standlalone_time,
                                       mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE_OVSDPDK)
        }
        self.test_context.nfvi_node = [{
            'name': 'ovs',
            'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
            'ip': '10.223.197.140',
            'role': 'Ovsdpdk',
            'user': 'root',
            'vpath': '/usr/local/',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.init(attrs)
        attr_name = 'bar.foo'
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result, None)

    def test__get_server_duplicate_sriov(self, mock_sriov_time, mock_standlalone_time,
                                         mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_DUPLICATE_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.223.197.140',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.get_nfvi_obj = mock.Mock(return_value="sriov")
        self.test_context.init(attrs)
        attr_name = 'sriov.foo'
        # self.test_context.name = "sriov"
        self.assertRaises(ValueError, self.test_context._get_server, attr_name)

    def test__get_server_duplicate_ovs(self, mock_sriov_time, mock_standlalone_time,
                                       mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_DUPLICATE_OVSDPDK)
        }
        self.test_context.nfvi_node = [{
            'name': 'ovs',
            'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
            'ip': '10.223.197.140',
            'role': 'Ovsdpdk',
            'user': 'root',
            'vpath': '/usr/local/',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'intel123',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

        self.test_context.get_nfvi_obj = mock.Mock(return_value="OvsDpdk")
        self.test_context.init(attrs)

        attr_name = 'ovs.foo'
        self.assertRaises(
            ValueError,
            self.test_context._get_server,
            attr_name)

    def test__get_server_found_sriov(self, mock_sriov_time, mock_standlalone_time,
                                     mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE_SRIOV)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.223.197.140',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'intel123',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

        self.test_context.get_nfvi_obj = mock.Mock(return_value="OvsDpdk")
        self.test_context.init(attrs)
        attr_name = 'sriov.foo'
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result['ip'], '10.123.123.122')
        self.assertEqual(result['name'], 'sriov.foo')
        self.assertEqual(result['user'], 'root')

    def test__get_server_found_ovs(self, mock_sriov_time, mock_standlalone_time,
                                   mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE_OVSDPDK_ROLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'ovs',
            'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
            'ip': '10.223.197.140',
            'role': 'Ovsdpdk',
            'user': 'root',
            'vpath': '/usr/local/',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.get_nfvi_obj = mock.Mock(return_value="OvsDpdk")
        self.test_context.init(attrs)
        attr_name = 'ovs.foo'
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result['ip'], '10.223.197.222')
        self.assertEqual(result['name'], 'ovs.foo')
        self.assertEqual(result['user'], 'root')

    def test__deploy_unsuccessful(self, mock_sriov_time, mock_standlalone_time, mock_ovsdpdk_time):
        self.test_context.vm_deploy = False

    def test__deploy_sriov_firsttime(self, mock_sriov_time, mock_standlalone_time,
                                     mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.223.197.140',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'intel123',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

        MYSRIOV = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.223.197.140',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'intel123',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

        self.test_context.vm_deploy = True

        self.test_context.get_nfvi_obj = mock.MagicMock()
        self.test_context.init(attrs)
        self.test_context.nfvi_obj.sriov = MYSRIOV
        self.test_context.nfvi_obj.ssh_remote_machine = mock.Mock()
        self.test_context.nfvi_obj.first_run = True
        self.test_context.nfvi_obj.install_req_libs()
        self.test_context.nfvi_obj.get_nic_details = mock.Mock()
        PORTS = ['0000:06:00.0', '0000:06:00.1']
        NIC_DETAILS = {
            'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'pci': ['0000:06:00.0', '0000:06:00.1'],
            'phy_driver': 'i40e'}
        DRIVER = 'i40e'
        result = self.test_context.nfvi_obj.setup_sriov_context(
            PORTS,
            NIC_DETAILS,
            DRIVER)
        print("{0}".format(result))
        self.assertIsNone(self.test_context.deploy())

    def test__deploy_sriov_notfirsttime(self, mock_sriov_time, mock_standlalone_time,
                                        mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.223.197.140',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'intel123',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        MYSRIOV = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.223.197.140',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'intel123',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

        self.test_context.vm_deploy = True
        self.test_context.get_nfvi_obj = mock.MagicMock()
        self.test_context.init(attrs)
        self.test_context.nfvi_obj.sriov = MYSRIOV
        self.test_context.nfvi_obj.ssh_remote_machine = mock.Mock()
        self.test_context.nfvi_obj.first_run = False
        self.test_context.nfvi_obj.get_nic_details = mock.Mock()
        PORTS = ['0000:06:00.0', '0000:06:00.1']
        NIC_DETAILS = {
            'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'pci': ['0000:06:00.0', '0000:06:00.1'],
            'phy_driver': 'i40e'}
        DRIVER = 'i40e'
        result = self.test_context.nfvi_obj.setup_sriov_context(
            PORTS,
            NIC_DETAILS,
            DRIVER)
        print("{0}".format(result))
        self.assertIsNone(self.test_context.deploy())

    def test__deploy_ovs_firsttime(self, mock_sriov_time, mock_standlalone_time,
                                   mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE_OVSDPDK)
        }

        self.test_context.nfvi_node = [{
            'name': 'ovs',
            'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
            'ip': '10.223.197.140',
            'role': 'Ovsdpdk',
            'user': 'root',
            'vpath': '/usr/local/',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

        MYOVS = [{
            'name': 'ovs',
            'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
            'ip': '10.223.197.140',
            'role': 'Ovsdpdk',
            'user': 'root',
            'vpath': '/usr/local/',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'flow': ['ovs-ofctl add-flow br0 in_port=1,action=output:3',
                     'ovs-ofctl add-flow br0 in_port=3,action=output:1'
                     'ovs-ofctl add-flow br0 in_port=4,action=output:2'
                     'ovs-ofctl add-flow br0 in_port=2,action=output:4'],
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

        self.test_context.vm_deploy = True
        self.test_context.get_nfvi_obj = mock.MagicMock()
        self.test_context.init(attrs)
        self.test_context.ovs = MYOVS
        self.test_context.nfvi_obj.ssh_remote_machine = mock.Mock()
        self.test_context.nfvi_obj.first_run = True
        self.test_context.nfvi_obj.install_req_libs()
        self.test_context.nfvi_obj.get_nic_details = mock.Mock()
        PORTS = ['0000:06:00.0', '0000:06:00.1']
        NIC_DETAILS = {
            'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
            'vports_mac': ['00:00:00:00:00:05', '00:00:00:00:00:06'],
            'pci': ['0000:06:00.0', '0000:06:00.1'],
            'phy_driver': 'i40e'}
        DRIVER = 'i40e'

        self.test_context.nfvi_obj.setup_ovs = mock.Mock()
        self.test_context.nfvi_obj.start_ovs_serverswitch = mock.Mock()
        self.test_context.nfvi_obj.setup_ovs_bridge = mock.Mock()
        self.test_context.nfvi_obj.add_oflows = mock.Mock()

        result = self.test_context.nfvi_obj.setup_ovs_context(
            PORTS,
            NIC_DETAILS,
            DRIVER)
        print("{0}".format(result))
        self.assertIsNone(self.test_context.deploy())

    def test__deploy_ovs_notfirsttime(self, mock_sriov_time, mock_standlalone_time,
                                      mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE_OVSDPDK)
        }
        self.test_context.nfvi_node = [{
            'name': 'ovs',
            'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
            'ip': '10.223.197.140',
            'role': 'Ovsdpdk',
            'user': 'root',
            'vpath': '/usr/local/',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

        MYOVS = [{
            'name': 'ovs',
            'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
            'ip': '10.223.197.140',
            'role': 'Ovsdpdk',
            'user': 'root',
            'vpath': '/usr/local/',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'flow': ['ovs-ofctl add-flow br0 in_port=1,action=output:3',
                     'ovs-ofctl add-flow br0 in_port=3,action=output:1'
                     'ovs-ofctl add-flow br0 in_port=4,action=output:2'
                     'ovs-ofctl add-flow br0 in_port=2,action=output:4'],
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

        self.test_context.vm_deploy = True
        self.test_context.get_nfvi_obj = mock.MagicMock()
        self.test_context.init(attrs)
        self.test_context.ovs = MYOVS
        self.test_context.nfvi_obj.ssh_remote_machine = mock.Mock()
        self.test_context.nfvi_obj.first_run = False
        self.test_context.nfvi_obj.get_nic_details = mock.Mock()
        PORTS = ['0000:06:00.0', '0000:06:00.1']
        NIC_DETAILS = {
            'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
            'vports_mac': ['00:00:00:00:00:05', '00:00:00:00:00:06'],
            'pci': ['0000:06:00.0', '0000:06:00.1'],
            'phy_driver': 'i40e'}
        DRIVER = 'i40e'

        self.test_context.nfvi_obj.setup_ovs(PORTS)
        self.test_context.nfvi_obj.start_ovs_serverswitch()
        self.test_context.nfvi_obj.setup_ovs_bridge()
        self.test_context.nfvi_obj.add_oflows()

        result = self.test_context.nfvi_obj.setup_ovs_context(
            PORTS,
            NIC_DETAILS,
            DRIVER)
        print("{0}".format(result))
        self.assertIsNone(self.test_context.deploy())

    def test_undeploy_sriov(self, mock_sriov_time, mock_standlalone_time, mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.223.197.140',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'intel123',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.get_nfvi_obj = mock.MagicMock()
        self.test_context.init(attrs)
        self.test_context.nfvi_obj.destroy_vm = mock.Mock()
        self.assertIsNone(self.test_context.undeploy())

    def test_undeploy_ovs(self, mock_sriov_time, mock_standlalone_time, mock_ovsdpdk_time):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE_OVSDPDK)
        }

        self.test_context.nfvi_node = [{
            'name': 'ovs',
            'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
            'ip': '10.223.197.140',
            'role': 'Ovsdpdk',
            'user': 'root',
            'vpath': '/usr/local/',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

        self.test_context.get_nfvi_obj = mock.MagicMock()
        self.test_context.init(attrs)
        self.test_context.nfvi_obj.destroy_vm = mock.Mock()
        self.assertIsNone(self.test_context.undeploy())

    def test_get_nfvi_obj_sriov(self, mock_sriov_time, mock_standlalone_time, mock_ovsdpdk_time):
        with mock.patch('yardstick.benchmark.contexts.standalone.sriov'):
            attrs = {
                'name': 'sriov',
                'file': self._get_file_abspath(self.NODES_SAMPLE)
            }
            self.test_context.init(attrs)
            self.test_context.nfvi_obj.file_path = self._get_file_abspath(
                self.NODES_SAMPLE)
            self.test_context.nfvi_node = [{
                'name': 'sriov',
                'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
                'ip': '10.223.197.140',
                'role': 'Sriov',
                'user': 'root',
                'images': '/var/lib/libvirt/images/ubuntu1.img',
                'phy_driver': 'i40e',
                'password': 'intel123',
                'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
            self.test_context.get_nfvi_obj = mock.MagicMock()
            self.test_context.init(attrs)
            self.test_context.get_context_impl = mock.Mock(
                return_value=sriov.Sriov)
            self.assertIsNotNone(self.test_context.get_nfvi_obj())

    def test_get_nfvi_obj_ovs(self, mock_sriov_time, mock_standlalone_time, mock_ovsdpdk_time):
        with mock.patch('yardstick.benchmark.contexts.standalone.ovsdpdk'):
            attrs = {
                'name': 'ovs',
                'file': self._get_file_abspath(self.NODES_SAMPLE_OVSDPDK)
            }
            self.test_context.init(attrs)
            self.test_context.nfvi_obj.file_path = self._get_file_abspath(
                self.NODES_SAMPLE)
            self.test_context.nfvi_node = [{
                'name': 'ovs',
                'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
                'ip': '10.223.197.140',
                'role': 'Ovsdpdk',
                'user': 'root',
                'vpath': '/usr/local/',
                'images': '/var/lib/libvirt/images/ubuntu1.img',
                'phy_driver': 'i40e',
                'password': 'password',
                'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
            self.test_context.get_nfvi_obj = mock.MagicMock()
            self.test_context.init(attrs)
            self.test_context.get_context_impl = mock.Mock(
                return_value=ovsdpdk.Ovsdpdk)
            self.assertIsNotNone(self.test_context.get_nfvi_obj())

    def test_get_context_impl_correct_obj(self, mock_sriov_time, mock_standlalone_time,
                                          mock_ovsdpdk_time):
        with mock.patch.dict("sys.modules", MOCKS):
            self.assertIsNotNone(self.test_context.get_context_impl('Sriov'))

    def test_get_context_impl_wrong_obj(self, mock_sriov_time, mock_standlalone_time,
                                        mock_ovsdpdk_time):
        with mock.patch.dict("sys.modules", MOCKS):
            self.assertRaises(
                ValueError,
                lambda: self.test_context.get_context_impl('wrong_object'))

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test__get_network(self, mock_sriov_time, mock_standlalone_time, mock_ovsdpdk_time):
        network1 = {
            'name': 'net_1',
            'vld_id': 'vld111',
            'segmentation_id': 'seg54',
            'network_type': 'type_a',
            'physical_network': 'phys',
        }
        network2 = {
            'name': 'net_2',
            'vld_id': 'vld999',
        }
        self.test_context.networks = {
            'a': network1,
            'b': network2,
        }

        attr_name = None
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = {}
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = {'vld_id': 'vld777'}
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = 'vld777'
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = {'vld_id': 'vld999'}
        expected = {
            "name": 'net_2',
            "vld_id": 'vld999',
            "segmentation_id": None,
            "network_type": None,
            "physical_network": None,
        }
        result = self.test_context._get_network(attr_name)
        self.assertDictEqual(result, expected)

        attr_name = 'a'
        expected = network1
        result = self.test_context._get_network(attr_name)
        self.assertDictEqual(result, expected)

if __name__ == '__main__':
    unittest.main()

