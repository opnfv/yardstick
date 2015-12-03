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

__author__ = 'vmriccox'


from keystoneclient.v2_0 import client as keystoneClient
from heatclient import client as heatClient
from heatclient.common import template_utils

from experimental_framework import common


class HeatManager:

    def __init__(self, credentials):
        self.ip_controller = credentials['ip_controller']
        self.heat_url = credentials['heat_url']
        self.user = credentials['user']
        self.password = credentials['password']
        self.auth_uri = credentials['auth_uri']
        self.project_id = credentials['project']
        self.heat = None

        # TODO: verify that init_heat is useless in the constructor
        # self.init_heat()

    def init_heat(self):
        keystone = keystoneClient.Client(username=self.user,
                                         password=self.password,
                                         tenant_name=self.project_id,
                                         auth_url=self.auth_uri)
        auth_token = keystone.auth_token
        self.heat = heatClient.Client('1', endpoint=self.heat_url,
                                      token=auth_token)

    def print_stacks(self, name=None):
        for stack in self.heat.stacks.list():
            if (name and stack.stack_name == name) or not name:
                common.LOG.info("Stack Name: " + stack.stack_name)
                common.LOG.info("Stack Status: " + stack.stack_status)

    def create_stack(self, template_file, stack_name, parameters):
        self.init_heat()
        # self.print_stacks()
        tpl_files, template = \
            template_utils.get_template_contents(template_file)

        fields = {
            'template': template,
            'files': dict(list(tpl_files.items()))
        }
        self.heat.stacks.create(stack_name=stack_name, files=fields['files'],
                                template=template, parameters=parameters)
        self.print_stacks(stack_name)

    def is_stack_deployed(self, stack_name):
        self.init_heat()
        if stack_name in self.heat.stacks.list():
            return True
        return False

    def check_stack_status(self, stack_name):
        """
        Returns a string representing the status of a stack from Heat
        perspective
        :param stack_name: Name of the stack to be checked (type: str)
        :return: (type: str)
        """
        for stack in self.heat.stacks.list():
            if stack.stack_name == stack_name:
                return stack.stack_status
        return 'NOT_FOUND'

    def validate_heat_template(self, heat_template_file):
        self.init_heat()
        if not self.heat.stacks.validate(template=open(heat_template_file,
                                                       'r').read()):
            raise ValueError('The provided heat template "' +
                             heat_template_file +
                             '" is not in the correct format')

    def delete_stack(self, stack_name):
        self.init_heat()
        try:
            for stack in self.heat.stacks.list():
                if stack.stack_name == stack_name:
                    self.heat.stacks.delete(stack.id)
                    return True
        except:
            pass
        return False

