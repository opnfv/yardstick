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
import unittest
import mock

from tests.unit.test_case import STL_MOCKS
from tests.unit.test_case import YardstickTestCase

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.benchmark.contexts.standalone import StandaloneContext

MOCKS = {
    'yardstick.benchmark.contexts': mock.MagicMock(),
    'yardstick.benchmark.contexts.standalone': mock.MagicMock(),
    'yardstick.benchmark.contexts.standalone.sriov': mock.MagicMock(),
    'yardstick.benchmark.contexts.standalone.ovsdpdk': mock.MagicMock(),
}

SAMPLE_FILE = "standalone_sample_write_to_file.txt"


class StandaloneContextTestCase(YardstickTestCase):

    NODES_SAMPLE = "nodes_sample_new.yaml"
    NODES_SAMPLE_SRIOV = "nodes_sample_new_sriov.yaml"
    NODES_DUPLICATE_SAMPLE = "nodes_duplicate_sample_new.yaml"

    NODES_SAMPLE_OVSDPDK = "nodes_sample_ovs.yaml"
    NODES_SAMPLE_OVSDPDK_ROLE = "nodes_sample_ovsdpdk.yaml"
    NODES_DUPLICATE_OVSDPDK = "nodes_duplicate_sample_ovs.yaml"

    @classmethod
    def make_attrs(cls, name=None, filename=None, relative=True):
        if name is None:
            name = 'ctx1'

        if filename is None:
            filename = cls.NODES_SAMPLE

        if relative:
            filename = cls.get_file_abspath(filename)

        return {
            'name': name,
            'file': filename,
        }


@mock.patch('yardstick.benchmark.contexts.standalone.time')
class TestStandaloneContext(StandaloneContextTestCase):

    FILE_OBJ = __file__

    def setUp(self):
        self.test_context = StandaloneContext()
        self.test_context.nodes = [{
            'name': 'sriov',
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'ip': '10.123.123.122',
            'role': 'Sriov',
            'user': 'root',
            'images': '/var/lib/libvirt/images/ubuntu1.img',
            'phy_driver': 'i40e',
            'password': 'password',
            'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

    def test_read_from_file(self, *_):
        correct_file_path = self.get_file_abspath(self.NODES_SAMPLE)
        test_obj = StandaloneContext()
        self.assertIsNotNone(test_obj.read_from_file(correct_file_path))

    def test_write_to_file(self, *_):
        test_obj = StandaloneContext()
        self.assertIsNone(test_obj.write_to_file(SAMPLE_FILE, "some content"))

    def test___init__(self, *_):
        test_context = StandaloneContext()
        self.assertIsNone(test_context.name)
        self.assertIsNone(test_context.file_path)
        self.assertEqual(test_context.nodes, [])

    def test_init_bad_name(self, *_):
        attrs = {}
        with self.assertRaises(KeyError):
            self.test_context.init(attrs)

    def test_init_bad_file(self, *_):
        attrs = self.make_attrs('foo', 'error_file')
        with self.assertRaises(IOError):
            self.test_context.init(attrs)

    @mock.patch("yardstick.ssh.SSH")
    def test__make_vm_template(self, mock_ssh, *_):
        attrs = self.make_attrs('sriov')

        mock_ssh.execute.return_value = 0, 'vm1', ''

        self.test_context._ssh_helper = mock_ssh
        self.test_context.init(attrs)

        with self.assertRaises(NotImplementedError):
            self.test_context._make_vm_template()

    @mock.patch("yardstick.ssh.SSH")
    def test__get_server_with_dic_attr_name(self, mock_ssh, *_):
        attrs = self.make_attrs('foo')
        attr_name = {'name': 'foo.bar'}

        self.test_context._ssh_helper = mock_ssh
        self.test_context.init(attrs)

        result = self.test_context._get_server(attr_name)
        self.assertIsNone(result)

    @mock.patch("yardstick.ssh.SSH")
    def test__get_server_not_found(self, mock_ssh, *_):
        attrs = self.make_attrs('foo')
        attr_name = 'bar.foo'

        self.test_context._ssh_helper = mock_ssh
        self.test_context.init(attrs)

        result = self.test_context._get_server(attr_name)
        self.assertIsNone(result)

    @mock.patch("yardstick.ssh.SSH")
    def test__get_server_duplicate(self, mock_ssh, *_):
        attrs = self.make_attrs('foo', self.NODES_DUPLICATE_SAMPLE)
        attr_name = 'sriov.foo'

        self.test_context._ssh_helper = mock_ssh
        self.test_context.init(attrs)

        with self.assertRaises(ValueError):
            self.test_context._get_server(attr_name)

    @mock.patch("yardstick.ssh.SSH")
    def test__get_server_found(self, mock_ssh, *_):
        attrs = self.make_attrs('sriov')
        attr_name = 'sriov.sriov'

        self.test_context.nodes[0]['name'] = 'sriov2'
        self.test_context._ssh_helper = mock_ssh
        self.test_context.init(attrs)

        result = self.test_context._get_server(attr_name)
        self.assertEqual(result['ip'], '10.123.123.122')
        self.assertEqual(result['name'], 'sriov.sriov')

    @mock.patch("yardstick.ssh.SSH")
    def test_deploy(self, mock_ssh, *_):
        attrs = self.make_attrs('sriov')

        mock_ssh.execute.return_value = 0, '', ''

        self.test_context._ssh_helper = mock_ssh
        self.test_context._setup_context = mock.Mock()
        self.test_context._make_vm_template = mock.Mock()
        self.test_context.write_to_file = mock.Mock()
        self.test_context._install_required_libraries = mock.Mock()
        self.test_context.init(attrs)
        self.test_context.first_run = True

        self.assertIsNone(self.test_context.deploy())

    @mock.patch("yardstick.ssh.SSH")
    def test_deploy_not_first_time(self, mock_ssh, *_):
        attrs = self.make_attrs('sriov')

        mock_ssh.execute.return_value = 0, '', ''

        self.test_context._ssh_helper = mock_ssh
        self.test_context._setup_context = mock.Mock()
        self.test_context._make_vm_template = mock.Mock()
        self.test_context.write_to_file = mock.Mock()
        self.test_context._install_required_libraries = mock.Mock()
        self.test_context.init(attrs)
        self.test_context.first_run = False

        self.assertIsNone(self.test_context.deploy())

    @mock.patch("yardstick.ssh.SSH")
    def test_deploy_vm_deploy_disabled(self, mock_ssh, *_):
        attrs = self.make_attrs('sriov')

        mock_ssh.execute.return_value = 0, 'vm1', ''

        self.test_context._ssh_helper = mock_ssh
        self.test_context.init(attrs)
        self.test_context.first_run = True
        self.test_context.vm_deploy = False

        self.assertIsNone(self.test_context.deploy())

    @mock.patch("yardstick.ssh.SSH")
    def test_undeploy(self, mock_ssh, *_):
        attrs = self.make_attrs('sriov')

        mock_ssh.execute.return_value = 0, '', ''

        self.test_context._ssh_helper = mock_ssh
        self.test_context.init(attrs)
        self.test_context.vm_deploy = True

        self.assertIsNone(self.test_context.undeploy())

    @mock.patch("yardstick.ssh.SSH")
    def test_undeploy_not_deployed(self, mock_ssh, *_):
        attrs = self.make_attrs('sriov')

        mock_ssh.execute.return_value = 0, '', ''

        self.test_context._ssh_helper = mock_ssh
        self.test_context.init(attrs)
        self.test_context.vm_deploy = False

        self.assertIsNone(self.test_context.undeploy())

    @mock.patch("yardstick.ssh.SSH")
    def test__start_vm_already_strated(self, mock_ssh, *_):
        attrs = self.make_attrs('sriov')

        mock_ssh.execute.return_value = 0, 'vm1', ''

        self.test_context._ssh_helper = mock_ssh
        self.test_context.init(attrs)
        self.test_context.vm_deploy = False

        self.assertIsNone(self.test_context._start_vm(remote_cfg_file))

    @mock.patch.dict("sys.modules", MOCKS)
    def test_get_context_impl_wrong_obj(self, *_):
        with self.assertRaises(ValueError):
            self.test_context.get_context_type('wrong_object')

    def test__get_network(self, *_):
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
