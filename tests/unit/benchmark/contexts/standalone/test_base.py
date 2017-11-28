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

import unittest
import mock
import copy

from yardstick.benchmark.contexts.standalone.base import CloudInit

NODE = {
    'name': 'ovs',
    'role': 'OvsDpdk',
    'ip': '1.1.1.1',
    'ssh_port': 22,
    'user': 'root',
    'auth_type': 'password',
}

CLOUD_INIT = {
    'cloud_init': {
            'enabled': True,
            'generate_iso_images': True,
            'mgmt_addr': '11.191.24.2/8',
            'vm_count': 1,
            'vm_address_offset': 100,
            'iso_image_path': '/var/lib/yardstick',
            'chpasswd': {
                'root': 'passw0rd',
                'ubuntu': 'passw0rd',
            },
    },
}

class TestCloudInit(unittest.TestCase):

    def test__init__(self):
        node = copy.deepcopy(NODE)
        node.update(CLOUD_INIT)
        cloud_init = CloudInit(node)
        self.assertTrue(cloud_init.enabled)

        node['cloud_init']['enabled'] = False
        cloud_init = CloudInit(node)
        self.assertFalse(cloud_init.enabled)


    @mock.patch('yardstick.benchmark.contexts.standalone.base.tempfile')
    @mock.patch('yardstick.benchmark.contexts.standalone.base.AnsibleCommon')
    def test_generate_iso_images(self, mock_ansible_common, _):
        node = copy.deepcopy(NODE)
        node.update(CLOUD_INIT)
        node['cloud_init']['generate_iso_images'] = False
        mock_ansible_common.execute_ansible = mock.Mock()

        cloud_init = CloudInit(node)
        cloud_init.generate_iso_images()
        self.assertFalse(mock_ansible_common.return_value.execute_ansible.called)

        node['cloud_init']['generate_iso_images'] = True
        cloud_init = CloudInit(node)
        cloud_init.generate_iso_images()
        self.assertTrue(mock_ansible_common.return_value.execute_ansible.called)

    def test_iso_image_path(self):
        node = copy.deepcopy(NODE)
        node.update(CLOUD_INIT)
        cloud_init = CloudInit(node)

        self.assertEquals('/var/lib/yardstick', cloud_init.iso_image_path)
