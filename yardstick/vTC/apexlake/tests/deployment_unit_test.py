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

from __future__ import absolute_import
import unittest
import logging
import mock
import experimental_framework.deployment_unit as mut
import experimental_framework.common as common

__author__ = 'vmriccox'


class DummyHeatManager:

    def __init__(self, param):
        self.counts = 0
        pass

    def validate_heat_template(self, template_file):
        return True

    def check_stack_status(self, stack_name):
        # return 'CREATE_COMPLETE'
        self.counts += 1
        if self.counts >= 3:
            return 'CREATE_COMPLETE'
        else:
            return 'CREATE_IN_PROGRESS'

    def delete_stack(self, stack_name):
        pass


class DummyHeatManagerFailed(DummyHeatManager):

    def check_stack_status(self, stack_name):
        return 'CREATE_FAILED'

    def create_stack(self, template_file, stack_name, parameters):
        pass


class DummyHeatManagerComplete(DummyHeatManager):

    def check_stack_status(self, stack_name):
        return 'CREATE_COMPLETE'

    def create_stack(self, template_file, stack_name, parameters):
        raise Exception()


class DummyHeatManagerFailedException(DummyHeatManagerFailed):

    def create_stack(self, template_file, stack_name, parameters):
        raise Exception

    def check_stack_status(self, stack_name):
        return ''


class DummyHeatManagerDestroy:

    def __init__(self, credentials):
        self.delete_stack_counter = 0
        self.check_stack_status_counter = 0

    def check_stack_status(self, stack_name):
        if self.check_stack_status_counter < 2:
            self.check_stack_status_counter += 1
            return 'DELETE_IN_PROGRESS'
        else:
            return 'DELETE_COMPLETE'

    def create_stack(self, template_file, stack_name, parameters):
        pass

    def delete_stack(self, stack_name=None):
        if stack_name == 'stack':
            self.delete_stack_counter += 1
        else:
            return self.delete_stack_counter

    def is_stack_deployed(self, stack_name):
        return True


class DummyHeatManagerDestroyException(DummyHeatManagerDestroy):

    def delete_stack(self, stack_name=None):
        raise Exception


class DummyHeatManagerReiteration:

    def __init__(self, param):
        self.counts = 0

    def validate_heat_template(self, template_file):
        return True

    def check_stack_status(self, stack_name):
        return 'CREATE_FAILED'

    def delete_stack(self, stack_name):
        pass

    def create_stack(self, template_file=None, stack_name=None,
                     parameters=None):
        if template_file == 'template_reiteration' and \
            stack_name == 'stack_reiteration' and \
                parameters == 'parameters_reiteration':
            self.counts += 1


class DummyDeploymentUnit(mut.DeploymentUnit):

    def destroy_heat_template(self, stack_name):
        raise Exception


@mock.patch("experimental_framework.deployment_unit.time")
class TestDeploymentUnit(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('experimental_framework.heat_manager.HeatManager',
                side_effect=DummyHeatManager)
    def test_constructor_for_sanity(self, mock_heat_manager, mock_time):
        du = mut.DeploymentUnit(dict())
        self.assertTrue(isinstance(du.heat_manager, DummyHeatManager))
        mock_heat_manager.assert_called_once_with(dict())
        self.assertEqual(du.deployed_stacks, list())

    @mock.patch('experimental_framework.heat_manager.HeatManager',
                side_effect=DummyHeatManager)
    @mock.patch('os.path.isfile')
    def test_deploy_heat_template_for_failure(self, mock_os_is_file,
                                              mock_heat_manager, mock_time):
        mock_os_is_file.return_value = False
        du = mut.DeploymentUnit(dict())
        template_file = ''
        stack_name = ''
        parameters = ''
        self.assertRaises(ValueError, du.deploy_heat_template, template_file,
                          stack_name, parameters, 0)

    @mock.patch('experimental_framework.heat_manager.HeatManager',
                side_effect=DummyHeatManager)
    @mock.patch('os.path.isfile')
    def test_deploy_heat_template_for_success(self, mock_os_is_file,
                                              mock_heat_manager, mock_time):
        mock_os_is_file.return_value = True
        du = mut.DeploymentUnit(dict())
        template_file = ''
        stack_name = ''
        parameters = ''
        common.LOG = logging.getLogger()
        output = du.deploy_heat_template(template_file, stack_name,
                                         parameters, 0)
        self.assertEqual(output, True)

    @mock.patch('experimental_framework.heat_manager.HeatManager',
                side_effect=DummyHeatManagerComplete)
    @mock.patch('os.path.isfile')
    def test_deploy_heat_template_2_for_success(self, mock_os_is_file,
                                                mock_heat_manager, mock_time):
        mock_os_is_file.return_value = True
        du = mut.DeploymentUnit(dict())
        template_file = ''
        stack_name = ''
        parameters = ''
        common.LOG = logging.getLogger()
        output = du.deploy_heat_template(template_file, stack_name,
                                         parameters, 0)
        self.assertEqual(output, True)

    @mock.patch('experimental_framework.heat_manager.HeatManager',
                side_effect=DummyHeatManagerComplete)
    @mock.patch('os.path.isfile')
    @mock.patch('experimental_framework.deployment_unit.DeploymentUnit',
                side_effect=DummyDeploymentUnit)
    def test_deploy_heat_template_3_for_success(self, mock_dep_unit,
                                                mock_os_is_file,
                                                mock_heat_manager, mock_time):
        mock_os_is_file.return_value = True
        du = mut.DeploymentUnit(dict())
        template_file = ''
        stack_name = ''
        parameters = ''
        common.LOG = logging.getLogger()
        output = du.deploy_heat_template(template_file, stack_name,
                                         parameters, 0)
        self.assertEqual(output, True)

    @mock.patch('experimental_framework.common.LOG')
    @mock.patch('experimental_framework.heat_manager.HeatManager',
                side_effect=DummyHeatManagerFailed)
    @mock.patch('os.path.isfile')
    def test_deploy_heat_template_for_success_2(self, mock_os_is_file,
                                                mock_heat_manager, mock_log, mock_time):
        mock_os_is_file.return_value = True
        du = DummyDeploymentUnit(dict())
        template_file = ''
        stack_name = ''
        parameters = ''
        output = du.deploy_heat_template(template_file, stack_name,
                                         parameters, 0)
        self.assertEqual(output, False)

    @mock.patch('experimental_framework.heat_manager.HeatManager',
                side_effect=DummyHeatManagerDestroy)
    @mock.patch('experimental_framework.common.LOG')
    def test_destroy_heat_template_for_success(self, mock_log,
                                               mock_heat_manager, mock_time):
        openstack_credentials = dict()
        du = mut.DeploymentUnit(openstack_credentials)
        du.deployed_stacks = ['stack']
        stack_name = 'stack'
        self.assertTrue(du.destroy_heat_template(stack_name))
        self.assertEqual(du.heat_manager.delete_stack(None), 1)

    @mock.patch('experimental_framework.heat_manager.HeatManager',
                side_effect=DummyHeatManagerDestroyException)
    @mock.patch('experimental_framework.common.LOG')
    def test_destroy_heat_template_for_success_2(self, mock_log,
                                                 mock_heat_manager, mock_time):
        openstack_credentials = dict()
        du = mut.DeploymentUnit(openstack_credentials)
        du.deployed_stacks = ['stack']
        stack_name = 'stack'
        self.assertFalse(du.destroy_heat_template(stack_name))

    def test_destroy_all_deployed_stacks_for_success(self, mock_time):
        du = DeploymentUnitDestroy()
        du.destroy_all_deployed_stacks()
        self.assertTrue(du.destroy_heat_template())

    @mock.patch('experimental_framework.heat_manager.HeatManager',
                side_effect=DummyHeatManagerReiteration)
    @mock.patch('os.path.isfile')
    def test_deploy_heat_template_for_success_3(self, mock_os_is_file,
                                                mock_heat_manager, mock_time):
        mock_os_is_file.return_value = True
        du = mut.DeploymentUnit(dict())
        template = 'template_reiteration'
        stack = 'stack_reiteration'
        parameters = 'parameters_reiteration'
        output = du.deploy_heat_template(template, stack, parameters, 0)
        self.assertFalse(output)
        self.assertEqual(du.heat_manager.counts, 4)


class DeploymentUnitDestroy(mut.DeploymentUnit):

    def __init__(self):
        self.deployed_stacks = ['stack']
        self.heat_manager = DummyHeatManagerDestroy(dict())
        self.destroy_all_deployed_stacks_called_correctly = False

    def destroy_heat_template(self, template_name=None):
        if template_name == 'stack':
            self.destroy_all_deployed_stacks_called_correctly = True
        return self.destroy_all_deployed_stacks_called_correctly
