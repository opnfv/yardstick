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
from yardstick.benchmark.contexts import sriov

MOCKS = {
    'yardstick.benchmark.contexts': mock.MagicMock(),
    'yardstick.benchmark.contexts.sriov': mock.MagicMock(),
    'yardstick.benchmark.contexts.standalone': mock.MagicMock(),
}


class StandaloneContextTestCase(unittest.TestCase):

    NODES_SAMPLE = "nodes_sample_new.yaml"
    NODES_DUPLICATE_SAMPLE = "nodes_duplicate_sample_new.yaml"

    def setUp(self):
        self.test_context = standalone.StandaloneContext()

    def test_construct(self):
        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.file_path)
        self.assertEqual(self.test_context.nodes, [])
        self.assertEqual(self.test_context.nfvi_node, [])

    def test_unsuccessful_init(self):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath("error_file")
        }
        self.assertRaises(IOError, self.test_context.init, attrs)

    def test_successful_init(self):
        attrs = {
            'name': 'sriov',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.123.123.122',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.get_nfvi_obj = mock.Mock()
        self.test_context.init(attrs)
        self.assertEqual(self.test_context.name, "sriov")
        self.assertEqual(len(self.test_context.nodes), 3)
        self.assertEqual(len(self.test_context.nfvi_node), 2)
        self.assertEqual(self.test_context.nfvi_node[0]["name"], "sriov")

    def test__get_server_with_dic_attr_name(self):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.123.123.122',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.init(attrs)
        attr_name = {'name': 'foo.bar'}
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result, None)

    def test__get_server_not_found(self):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.123.123.122',
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

    def test__get_server_duplicate(self):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_DUPLICATE_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.123.123.122',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.init(attrs)
        attr_name = 'sriov.foo'
        self.assertRaises(
            ValueError,
            self.test_context._get_server,
            attr_name)

    def test__get_server_found(self):
        attrs = {
            'name': 'sriov',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.123.123.122',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.init(attrs)
        attr_name = 'sriov.sriov'
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result['ip'], '10.123.123.122')
        self.assertEqual(result['name'], 'sriov.sriov')
        self.assertEqual(result['user'], 'root')

    def test_deploy(self):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.123.123.122',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.get_nfvi_obj = mock.MagicMock()
        self.test_context.init(attrs)
        self.test_context.nfvi_obj.ssh_remote_machine = mock.Mock()
        self.test_context.nfvi_obj.first_run = True
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

    def test_undeploy(self):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }
        self.test_context.nfvi_node = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.123.123.122',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
        self.test_context.get_nfvi_obj = mock.MagicMock()
        self.test_context.init(attrs)
        self.test_context.nfvi_obj.destroy_vm = mock.Mock()
        self.assertIsNone(self.test_context.undeploy())

    def test_get_nfvi_obj(self):
        with mock.patch('yardstick.benchmark.contexts.sriov'):
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
                'ip': '10.123.123.122',
                'role': 'Sriov',
                'user': 'root',
                'images': '/var/lib/libvirt/images/ubuntu1.img',
                'phy_driver': 'i40e',
                'password': 'password',
                'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]
            self.test_context.get_nfvi_obj = mock.MagicMock()
            self.test_context.init(attrs)
            self.test_context.get_context_impl = mock.Mock(
                return_value=sriov.Sriov)
            self.assertIsNotNone(self.test_context.get_nfvi_obj())

    def test_get_context_impl_correct_obj(self):
        with mock.patch.dict("sys.modules", MOCKS):
            self.assertIsNotNone(self.test_context.get_context_impl('Sriov'))

    def test_get_context_impl_wrong_obj(self):
        with mock.patch.dict("sys.modules", MOCKS):
            self.assertRaises(
                ValueError,
                lambda: self.test_context.get_context_impl('wrong_object'))

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

if __name__ == '__main__':
    unittest.main()
