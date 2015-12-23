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

import os
import time
# import logging

from experimental_framework import heat_manager
from experimental_framework import common

# LOG = logging.getLogger(__name__)
# LOG = common.LOG


class DeploymentUnit:
    """
    This unit is in charge to manage the deployment of the workloads under
    test and any other workloads necessary to
    the benchmark
    """

    def __init__(self, openstack_credentials):
        self.heat_manager = heat_manager.HeatManager(openstack_credentials)
        self.deployed_stacks = list()

    def destroy_heat_template(self, stack_name):
        """
        Destroys a stack
        :param stack_name: Stack of the name to be destroyed (sting)
        :return: None
        """
        try:
            if self.heat_manager.check_stack_status(stack_name):
                if stack_name in self.deployed_stacks:
                    self.deployed_stacks.remove(stack_name)
                self.heat_manager.delete_stack(stack_name)

            status = self.heat_manager.check_stack_status(stack_name)
            while status and 'DELETE_IN_PROGRESS' in status:
                common.LOG.info(status)
                time.sleep(5)
                status = self.heat_manager.check_stack_status(stack_name)
            return True
        except:
            return False

    def destroy_all_deployed_stacks(self):
        """
        Destroys all the stacks currently deployed
        :return: None
        """
        for stack in self.deployed_stacks:
            if self.heat_manager.is_stack_deployed(stack):
                self.destroy_heat_template(stack)

    def deploy_heat_template(self, template_file, stack_name, parameters,
                             attempt=0):
        """
        Deploys a heat template and in case of failure retries 3 times
        :param template_file: full path file name of the heat template
        :param stack_name: name of the stack to deploy
        :param parameters: parameters to be given to the heat template
        :param attempt: number of current attempt
        :return: returns True in case the creation is completed
                 returns False in case the creation is failed
        """
        MAX_RETRY = 3
        if not os.path.isfile(template_file):
            raise ValueError('The specified file does not exist ("' +
                             template_file + '")')
        self.heat_manager.validate_heat_template(template_file)
        try:
            self.heat_manager.create_stack(template_file, stack_name,
                                           parameters)
            deployed = True
        except Exception as e:
            deployed = False

        if not deployed and 'COMPLETE' in \
                self.heat_manager.check_stack_status(stack_name):
            try:
                self.destroy_heat_template(stack_name)
            except:
                pass

        status = self.heat_manager.check_stack_status(stack_name)
        while status and 'CREATE_IN_PROGRESS' in status:
            time.sleep(5)
            status = self.heat_manager.check_stack_status(stack_name)
        if status and ('FAILED' in status or 'NOT_FOUND' in status):
            if attempt < MAX_RETRY:
                attempt += 1
                try:
                    self.destroy_heat_template(stack_name)
                except Exception as e:
                    common.LOG.debug(e.message)
                    pass
                return self.deploy_heat_template(template_file, stack_name,
                                                 parameters, attempt)
            else:
                try:
                    self.destroy_heat_template(stack_name)
                except Exception as e:
                    common.LOG.debug(e.message)
                finally:
                    return False
        if self.heat_manager.check_stack_status(stack_name) and \
                        'COMPLETE' in self.heat_manager.\
                        check_stack_status(stack_name):
            self.deployed_stacks.append(stack_name)
            return True