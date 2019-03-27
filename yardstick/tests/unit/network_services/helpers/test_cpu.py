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

from __future__ import division
import unittest
import mock
import subprocess

from yardstick.network_services.helpers.cpu import \
    CpuSysCores


class TestCpuSysCores(unittest.TestCase):

    def setUp(self):
        self._mock_ssh = mock.patch("yardstick.ssh.SSH")
        self.mock_ssh = self._mock_ssh.start()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self._mock_ssh.stop()

    def test___init__(self):
        self.mock_ssh.execute.return_value = 1, "", ""
        self.mock_ssh.put.return_value = 1, "", ""
        cpu_topo = CpuSysCores(self.mock_ssh)
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
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "cpu:1\ntest:2\n \n", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(1, "", ""))
            cpu_topo = CpuSysCores(ssh_mock)
            subprocess.check_output = mock.Mock(return_value=0)
            cpu_topo._get_core_details = \
                mock.Mock(side_effect=[[{'Core(s) per socket': '2', 'Thread(s) per core': '1'}],
                                       [{'physical id': '2', 'processor': '1'}]])
            self.assertEqual({'thread_per_core': '1', '2': ['1'],
                              'cores_per_socket': '2'},
                             cpu_topo.get_core_socket())

    def test_validate_cpu_cfg(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "cpu:1\ntest:2\n \n", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(1, "", ""))
            cpu_topo = CpuSysCores(ssh_mock)
            subprocess.check_output = mock.Mock(return_value=0)
            cpu_topo._get_core_details = \
                mock.Mock(side_effect=[[{'Core(s) per socket': '2', 'Thread(s) per core': '1'}],
                                       [{'physical id': '2', 'processor': '1'}]])
            cpu_topo.core_map = \
                {'thread_per_core': '1', '2': ['1'], 'cores_per_socket': '2'}
            self.assertEqual(-1, cpu_topo.validate_cpu_cfg())

    def test_validate_cpu_cfg_2t(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "cpu:1\ntest:2\n \n", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(1, "", ""))
            cpu_topo = CpuSysCores(ssh_mock)
            subprocess.check_output = mock.Mock(return_value=0)
            cpu_topo._get_core_details = \
                mock.Mock(side_effect=[[{'Core(s) per socket': '2', 'Thread(s) per core': '1'}],
                                       [{'physical id': '2', 'processor': '1'}]])
            cpu_topo.core_map = \
                {'thread_per_core': 1, '2': ['1'], 'cores_per_socket': '2'}
            vnf_cfg = {'lb_config': 'SW', 'lb_count': 1, 'worker_config':
                       '1C/2T', 'worker_threads': 1}
            self.assertEqual(-1, cpu_topo.validate_cpu_cfg(vnf_cfg))

    def test_validate_cpu_cfg_fail(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "cpu:1\ntest:2\n \n", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(1, "", ""))
            cpu_topo = CpuSysCores(ssh_mock)
            subprocess.check_output = mock.Mock(return_value=0)
            cpu_topo._get_core_details = \
                mock.Mock(side_effect=[[{'Core(s) per socket': '2', 'Thread(s) per core': '1'}],
                                       [{'physical id': '2', 'processor': '1'}]])
            cpu_topo.core_map = \
                {'thread_per_core': 1, '2': [1], 'cores_per_socket': 2}
            vnf_cfg = {'lb_config': 'SW', 'lb_count': 1, 'worker_config':
                       '1C/1T', 'worker_threads': 1}
            self.assertEqual(-1, cpu_topo.validate_cpu_cfg(vnf_cfg))

    def test_get_cpu_layout(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(
                    return_value=(1, "# CPU,Core,Socket,Node,,L1d,L1i,L2,L3\n'"
                                     "0,0,0,0,,0,0,0,0\n"
                                     "1,1,0,0,,1,1,1,0\n", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(1, "", ""))
            cpu_topo = CpuSysCores(ssh_mock)
            subprocess.check_output = mock.Mock(return_value=0)
            self.assertEqual({'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [1, 1, 0, 0, 0, 1, 1, 1, 0]]},
                             cpu_topo.get_cpu_layout())

    def test__str2int(self):
        self.assertEqual(1, CpuSysCores._str2int("1"))

    def test__str2int_error(self):
        self.assertEqual(0, CpuSysCores._str2int("err"))

    def test_smt_enabled(self):
        self.assertEqual(False, CpuSysCores.smt_enabled(
            {'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                         [1, 1, 0, 0, 0, 1, 1, 1, 0]]}))

    def test_is_smt_enabled(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            cpu_topo = CpuSysCores(ssh_mock)
            cpu_topo.cpuinfo = {'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                                            [1, 1, 0, 0, 0, 1, 1, 1, 0]]}
            self.assertEqual(False, cpu_topo.is_smt_enabled())

    def test_cpu_list_per_node(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            cpu_topo = CpuSysCores(ssh_mock)
            cpu_topo.cpuinfo = {'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                                            [1, 1, 0, 0, 0, 1, 1, 1, 0]]}
            self.assertEqual([0, 1], cpu_topo.cpu_list_per_node(0, False))

    def test_cpu_list_per_node_error(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            cpu_topo = CpuSysCores(ssh_mock)
            cpu_topo.cpuinfo = {'err': [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                                        [1, 1, 0, 0, 0, 1, 1, 1, 0]]}
            with self.assertRaises(RuntimeError) as raised:
                cpu_topo.cpu_list_per_node(0, False)
            self.assertIn('Node cpuinfo not available.', str(raised.exception))

    def test_cpu_list_per_node_smt_error(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            cpu_topo = CpuSysCores(ssh_mock)
            cpu_topo.cpuinfo = {'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                                            [1, 1, 0, 0, 0, 1, 1, 1, 0]]}
            with self.assertRaises(RuntimeError) as raised:
                cpu_topo.cpu_list_per_node(0, True)
            self.assertIn('SMT is not enabled.', str(raised.exception))

    def test_cpu_slice_of_list_per_node(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            cpu_topo = CpuSysCores(ssh_mock)
            cpu_topo.cpuinfo = {'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                                            [1, 1, 0, 0, 0, 1, 1, 1, 0]]}
            self.assertEqual([1],
                             cpu_topo.cpu_slice_of_list_per_node(0, 1, 0,
                                                                 False))

    def test_cpu_slice_of_list_per_node_error(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            cpu_topo = CpuSysCores(ssh_mock)
            cpu_topo.cpuinfo = {'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                                            [1, 1, 0, 0, 0, 1, 1, 1, 0]]}
            with self.assertRaises(RuntimeError) as raised:
                cpu_topo.cpu_slice_of_list_per_node(1, 1, 1, False)
            self.assertIn('cpu_cnt + skip_cnt > length(cpu list).',
                          str(raised.exception))

    def test_cpu_list_per_node_str(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            cpu_topo = CpuSysCores(ssh_mock)
            cpu_topo.cpuinfo = {'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                                            [1, 1, 0, 0, 0, 1, 1, 1, 0]]}
            self.assertEqual("1",
                             cpu_topo.cpu_list_per_node_str(0, 1, 1, ',',
                                                            False))
