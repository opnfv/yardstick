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

from __future__ import absolute_import
from __future__ import division
import unittest
import mock
import subprocess

from yardstick.network_services.helpers.cpu import \
    CpuSysCores


class TestCpuSysCores(unittest.TestCase):

    def test___init__(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(1, "", ""))
            cpu_topo = CpuSysCores(ssh_mock)
            self.assertIsNotNone(cpu_topo.connection)

    def test__get_core_details(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(1, "", ""))
            cpu_topo = CpuSysCores(ssh_mock)
            subprocess.check_output = mock.Mock(return_value=0)
            lines = ["cpu:1", "topo:2", ""]
            self.assertEqual([{'topo': '2', 'cpu': '1'}],
                             cpu_topo._get_core_details(lines))

    def test_get_core_socket(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = mock.Mock(return_value=(1, "cpu:1\ntest:2\n \n", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(1, "", ""))
            cpu_topo = CpuSysCores(ssh_mock)
            subprocess.check_output = mock.Mock(return_value=0)
            cpu_topo._get_core_details = \
                mock.Mock(side_effect=[[{'Core(s) per socket': '2', 'Thread(s) per core': '1'}],
                                       [{'physical id': '2', 'processor': '1'}]])
            self.assertEqual({'thread_per_core': 1, '2': ['1'],
                              'cores_per_socket': 2},
                             cpu_topo.get_core_socket())
