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
import experimental_framework.heat_template_generation as heat_gen
import mock
import os
import experimental_framework.common as common


def reset_common():
    common.LOG = None
    common.CONF_FILE = None
    common.DEPLOYMENT_UNIT = None
    common.ITERATIONS = None
    common.BASE_DIR = None
    common.RESULT_DIR = None
    common.TEMPLATE_DIR = None
    common.TEMPLATE_NAME = None
    common.TEMPLATE_FILE_EXTENSION = None
    common.PKTGEN = None
    common.PKTGEN_DIR = None
    common.PKTGEN_DPDK_DIRECTORY = None
    common.PKTGEN_PROGRAM = None
    common.PKTGEN_COREMASK = None
    common.PKTGEN_MEMCHANNEL = None
    common.PKTGEN_BUS_SLOT_NIC_1 = None
    common.PKTGEN_BUS_SLOT_NIC_2 = None
    common.INFLUXDB_IP = None
    common.INFLUXDB_PORT = None
    common.INFLUXDB_DB_NAME = None


class TestGeneratesTemplate(unittest.TestCase):
    def setUp(self):
        self.deployment_configuration = {
            'vnic_type': ['normal', 'direct'],
            'ram': ['1024'],
            'vcpus': ['2']
        }
        self.template_name = 'VTC_base_single_vm_wait.tmp'
        # common.init()

    def tearDown(self):
        reset_common()

    @mock.patch('experimental_framework.common.LOG')
    @mock.patch('experimental_framework.common.get_template_dir')
    def test_generates_template_for_success(self, mock_template_dir,
                                            mock_log):
        generated_templates_dir = 'tests/data/generated_templates/'
        mock_template_dir.return_value = generated_templates_dir
        test_templates = 'tests/data/test_templates/'
        heat_gen.generates_templates(self.template_name,
                                     self.deployment_configuration)
        for dirname, dirnames, filenames in os.walk(test_templates):
            for filename in filenames:
                with open(test_templates + filename) as test:
                    with open(generated_templates_dir + filename) as generated:
                        self.assertListEqual(test.readlines(),
                                             generated.readlines())

        t_name = '/tests/data/generated_templates/VTC_base_single_vm_wait.tmp'
        self.template_name = "{}{}".format(os.getcwd(), t_name)
        heat_gen.generates_templates(self.template_name,
                                     self.deployment_configuration)
        for dirname, dirnames, filenames in os.walk(test_templates):
            for filename in filenames:
                with open(test_templates + filename) as test:
                    with open(generated_templates_dir + filename) as generated:
                        self.assertListEqual(test.readlines(),
                                             generated.readlines())

    @mock.patch('experimental_framework.common.get_template_dir')
    def test_get_all_heat_templates_for_success(self, template_dir):
        generated_templates = 'tests/data/generated_templates/'
        template_dir.return_value = generated_templates
        extension = '.yaml'
        expected = ['experiment_1.yaml', 'experiment_2.yaml']
        result = heat_gen.get_all_heat_templates(generated_templates,
                                                 extension)
        self.assertListEqual(expected, result)
