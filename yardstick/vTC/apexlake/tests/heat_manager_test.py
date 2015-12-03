# Copyright (c) 2015 Intel Research and Development Ireland Ltd.
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

__author__ = 'gpetralx'


import unittest
from experimental_framework import heat_manager
from heatclient import client
import mock


def get_mock_heat(version, *args, **kwargs):
    return MockHeat()


class MockStacks(object):
    def __init__(self, stacks):
        self.stacks = stacks

    def list(self):
        list_name = list()
        for stack in self.stacks:
            list_name.append(stack.stack_name)
        print list_name
        return self.stacks

    def validate(self, template=None):
        return False

    def delete(self, id):
        for stack in self.stacks:
            if stack.id == id:
                return self.stacks.remove(stack)

    def create(self, stack_name=None, files=None, template=None,
               parameters=None):
        print stack_name
        self.stacks.append(MockStack(stack_name))


class MockStacks_2(object):
    def __init__(self, stacks):
        self.stacks = stacks

    def list(self):
        raise Exception


class MockStack(object):
    def __init__(self, stack_name):
        self.name = stack_name

    @property
    def stack_status(self):
        return self.stack_name + '_status'

    @property
    def stack_name(self):
        return self.name

    @property
    def id(self):
        return self.name

    def __eq__(self, other):
        return self.name == other


class MockHeat(object):
    def __init__(self):
        stacks = [MockStack('stack_1'), MockStack('stack_2')]
        self.stacks_list = MockStacks(stacks)

    @property
    def stacks(self):
        return self.stacks_list


class MockHeat_2(MockHeat):
    def __init__(self):
        stacks = [MockStack('stack_1'), MockStack('stack_2')]
        self.stacks_list = MockStacks_2(stacks)


class HeatManagerMock(heat_manager.HeatManager):
    def init_heat(self):
        if self.heat is None:
            self.heat = MockHeat()

class HeatManagerMock_2(heat_manager.HeatManager):
    def init_heat(self):
        if self.heat is None:
            self.heat = MockHeat_2()


# class DummyStacks():
#
#     def create(self, stack_name, files, template, parameters):
#         pass
#
#
# class DummyHeatClient(client.Client):
#
#     def __init__(self):
#         client.Client.__init__(self)
#         self.stacks = DummyStacks()


class TestHeatManager(unittest.TestCase):

    def setUp(self):
        credentials = dict()
        credentials['ip_controller'] = '1.1.1.1'
        credentials['heat_url'] = 'http://heat_url'
        credentials['user'] = 'user'
        credentials['password'] = 'password'
        credentials['auth_uri'] = 'auth_uri'
        credentials['project'] = 'project'
        self.heat_manager = HeatManagerMock(credentials)
        self.heat_manager.init_heat()

    def tearDown(self):
        pass

    def test_is_stack_deployed_for_success(self):
        self.assertTrue(self.heat_manager.is_stack_deployed('stack_1'))
        self.assertFalse(self.heat_manager.is_stack_deployed('stack_n'))

    def test_check_status_for_success(self):
        self.assertEqual('stack_1_status',
                         self.heat_manager.check_stack_status('stack_1'))
        self.assertEqual('NOT_FOUND',
                         self.heat_manager.check_stack_status('stack_x'))

    def test_validate_template_for_success(self):
        template_file = \
            'tests/data/test_templates/VTC_base_single_vm_wait_1.yaml'
        with self.assertRaises(ValueError):
            self.heat_manager.validate_heat_template(template_file)

    def test_delete_stack_for_success(self):
        self.assertTrue(self.heat_manager.delete_stack('stack_1'))
        self.assertFalse(self.heat_manager.delete_stack('stack_x'))

    def test_delete_stack_for_success_2(self):
        self.assertTrue(self.heat_manager.delete_stack('stack_1'))

    @mock.patch('heatclient.common.template_utils.get_template_contents')
    @mock.patch('heatclient.client.Client')
    # @mock.patch('heatclient.client.Client', side_effect=DummyHeatClient)
    def test_create_stack_for_success(self, mock_stack_create,
                                      mock_get_template_contents):
        return_value = ({'template': 'template'}, 'template')
        mock_get_template_contents.return_value = return_value
        self.heat_manager.create_stack('template', 'stack_n', 'parameters')
        self.assertTrue(self.heat_manager.is_stack_deployed('stack_n'))


class TestHeatManager_2(unittest.TestCase):

    def setUp(self):
        credentials = dict()
        credentials['ip_controller'] = '1.1.1.1'
        credentials['heat_url'] = 'http://heat_url'
        credentials['user'] = 'user'
        credentials['password'] = 'password'
        credentials['auth_uri'] = 'auth_uri'
        credentials['project'] = 'project'
        self.heat_manager = HeatManagerMock_2(credentials)

    def tearDown(self):
        pass

    def test_delete_stack_for_success_2(self):
        self.assertFalse(self.heat_manager.delete_stack('stack_1'))


class KeystoneMock(object):
    @property
    def auth_token(self):
        return 'token'


class TestHeatInit(unittest.TestCase):
    def setUp(self):
        credentials = dict()
        credentials['ip_controller'] = '1.1.1.1'
        credentials['heat_url'] = 'http://heat_url'
        credentials['user'] = 'user'
        credentials['password'] = 'password'
        credentials['auth_uri'] = 'auth_uri'
        credentials['project'] = 'project'
        self.heat_manager = heat_manager.HeatManager(credentials)

    def tearDown(self):
        pass

    @mock.patch('heatclient.client.Client')
    @mock.patch('keystoneclient.v2_0.client.Client')
    def test_heat_init_for_sanity(self, keystone_client, heat_client):
        keystone_client.return_value = KeystoneMock()
        heat_client.return_value = MockHeat()
        self.heat_manager.init_heat()
        keystone_client.assert_called_once_with(username='user',
                                                tenant_name='project',
                                                password='password',
                                                auth_url='auth_uri')
        heat_client.assert_called_once_with('1',  endpoint='http://heat_url',
                                            token='token')
