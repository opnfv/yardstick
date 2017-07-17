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
import mock
import os
import experimental_framework.constants.conf_file_sections as cfs
import experimental_framework.common as common
import experimental_framework.benchmarks.\
    instantiation_validation_benchmark as iv_module
from experimental_framework.benchmarks.\
    instantiation_validation_benchmark import InstantiationValidationBenchmark
from six.moves import map
from six.moves import range


kill_counter = [0, 0]
command_counter = [0, 0, 0, 0, 0]
replace_counter = [0, 0, 0]


def dummy_os_kill(pid, signal, get_counters=None):
    if get_counters:
        return kill_counter
    if pid == 1234:
        kill_counter[0] += 1
        return
    if pid == 4321:
        kill_counter[1] += 1
        return
    raise Exception(pid)


def dummy_run_command(command, get_counters=None):
    if get_counters:
        return command_counter
    if command == 'sudo smcroute -k':
        command_counter[0] += 1
        return
    elif command == 'sudo ip link delete interface.100':
        command_counter[1] += 1
        return
    elif command == 'sudo kill 1234':
        kill_counter[0] += 1
        return
    elif command == 'sudo kill 4321':
        kill_counter[1] += 1
        return
    raise Exception(command)


def dummy_run_command_2(command, get_counters=None):
    if get_counters:
        return command_counter
    if command == 'sudo ip link add link interface name interface.' \
                  '100 type vlan id 100':
        command_counter[0] += 1
        return
    elif command == 'sudo ifconfig interface.100 10.254.254.254 up' \
                    ' netmask 255.255.255.248':
        command_counter[1] += 1
        return
    elif command == "sudo echo 'mgroup from interface.100 group" \
                    " 224.192.16.1' > /etc/smcroute.conf":
        command_counter[2] += 1
        return
    elif command == "sudo smcroute -d":
        command_counter[3] += 1
        return
    elif command == "sudo test_sniff interface.100 128 &":
        command_counter[4] += 1
        return


def dummy_replace_in_file(file, str_from, str_to, get_couters=None):
    if get_couters:
        return replace_counter
    if file == 'file':
        if str_from == 'local out_file = "result_file"':
            if str_to == 'local out_file = ""':
                replace_counter[0] += 1
                return
        if str_from == 'local traffic_rate = 100':
            if str_to == 'local traffic_rate = 0':
                replace_counter[1] += 1
                return
        if str_from == 'local traffic_delay = 60':
            if str_to == 'local traffic_delay = 0':
                replace_counter[2] += 1
                return
        if str_from == 'local out_file = ""':
            if str_to == 'local out_file = "result_file"':
                replace_counter[3] += 1
                return
        if str_from == 'local traffic_rate = 0':
            if str_to == 'local traffic_rate = 100':
                replace_counter[4] += 1
                return
        if str_from == 'local traffic_delay = 0':
            if str_to == 'local traffic_delay = 60':
                replace_counter[5] += 1
                return
    raise Exception(file + ' ' + str_from + ' ' + str_to)


class DummyDpdkPacketGenerator():

    counter = 0

    def __init__(self):
        DummyDpdkPacketGenerator.counter = [0, 0]

    def init_dpdk_pktgen(self, dpdk_interfaces, lua_script, pcap_file_0,
                         pcap_file_1, vlan_0, vlan_1):
        if dpdk_interfaces == 1:
            if lua_script == 'constant_traffic.lua':
                if pcap_file_0 == 'packet_512.pcap':
                    if pcap_file_1 == 'igmp.pcap':
                        if vlan_0 == '-1':
                            if vlan_1 == '-1':
                                DummyDpdkPacketGenerator.counter[0] += 1

    def send_traffic(self):
        DummyDpdkPacketGenerator.counter[1] += 1
        return


class DummyInstantiaionValidationBenchmark(InstantiationValidationBenchmark):

    counter = [0, 0, 0, 0, 0]

    def _configure_lua_file(self, traffic_rate_percentage, traffic_time):
        DummyInstantiaionValidationBenchmark.counter[0] += 1

    def _init_packet_checker(self):
        DummyInstantiaionValidationBenchmark.counter[1] += 1

    def _finalize_packet_checker(self):
        DummyInstantiaionValidationBenchmark.counter[2] += 1

    def _reset_lua_file(self, traffic_rate_percentage, traffic_time):
        if traffic_rate_percentage == '1' and traffic_time == '10':
            DummyInstantiaionValidationBenchmark.counter[3] += 1

    def _get_results(self):
        DummyInstantiaionValidationBenchmark.counter[4] += 1
        res = {'test': 'result'}
        return res


class InstantiationValidationInitTest(unittest.TestCase):

    def setUp(self):
        common.BASE_DIR = os.getcwd()
        self.iv = InstantiationValidationBenchmark('InstantiationValidation',
                                                   dict())

    def tearDown(self):
        common.BASE_DIR = None

    @mock.patch('experimental_framework.common.get_base_dir')
    def test___init___for_success(self, mock_base_dir):
        mock_base_dir.return_value = 'base_dir/'
        iv = InstantiationValidationBenchmark('InstantiationValidation',
                                              dict())
        self.assertEqual(iv.base_dir,
                         'base_dir/experimental_framework/'
                         'packet_generators/dpdk_pktgen/')
        self.assertEqual(iv.results_file,
                         'base_dir/experimental_framework/'
                         'packet_generators/dpdk_pktgen/packets.res')
        self.assertEqual(iv.lua_file,
                         'base_dir/experimental_framework/'
                         'packet_generators/dpdk_pktgen/constant_traffic.lua')
        self.assertEqual(iv.pkt_checker_command,
                         'base_dir/experimental_framework/'
                         'libraries/packet_checker/test_sniff ')
        self.assertEqual(iv.res_dir, '')
        self.assertEqual(iv.interface_name, '')

    def test_init_for_success(self):
        self.iv.init()

    def test_finalize_for_success(self):
        self.iv.finalize()

    def test_get_features_for_success(self):

        expected = dict()
        expected['description'] = 'Instantiation Validation Benchmark'
        expected['parameters'] = [
            iv_module.THROUGHPUT,
            iv_module.VLAN_SENDER,
            iv_module.VLAN_RECEIVER
        ]
        expected['allowed_values'] = dict()
        expected['allowed_values'][iv_module.THROUGHPUT] = \
            list(map(str, list(range(0, 100))))
        expected['allowed_values'][iv_module.VLAN_SENDER] = \
            list(map(str, list(range(-1, 4096))))
        expected['allowed_values'][iv_module.VLAN_RECEIVER] = \
            list(map(str, list(range(-1, 4096))))
        expected['default_values'] = dict()
        expected['default_values'][iv_module.THROUGHPUT] = '1'
        expected['default_values'][iv_module.VLAN_SENDER] = '-1'
        expected['default_values'][iv_module.VLAN_RECEIVER] = '-1'
        output = self.iv.get_features()
        self.assertEqual(expected, output)

    @mock.patch('subprocess.check_output')
    def test__get_pids_for_success(self, mock_getoutput):
        expected = [1234]
        mock_getoutput.return_value = '1234'
        output = self.iv._get_pids()
        self.assertEqual(expected, output)

        expected = [1234, 4321]
        mock_getoutput.return_value = '1234\n4321'
        output = self.iv._get_pids()
        self.assertEqual(expected, output)

        expected = []
        mock_getoutput.return_value = None
        output = self.iv._get_pids()
        self.assertEqual(expected, output)

    @mock.patch('experimental_framework.common.run_command',
                side_effect=dummy_run_command)
    @mock.patch('os.kill', side_effect=dummy_os_kill)
    @mock.patch('experimental_framework.benchmarks.'
                'instantiation_validation_benchmark.'
                'InstantiationValidationBenchmark._get_pids')
    def test__finalize_packet_checker_for_success(self,
                                                  mock_pids,
                                                  mock_os_kill,
                                                  mock_run_command):
        global command_counter
        global kill_counter
        command_counter = [0, 0, 0, 0, 0]
        kill_counter = [0, 0]
        mock_pids.return_value = [1234, 4321]
        self.iv.interface_name = 'interface'
        self.iv.params[iv_module.VLAN_RECEIVER] = '100'
        self.iv._finalize_packet_checker()
        self.assertEqual(dummy_os_kill('', '', True), [1, 1])
        self.assertEqual(dummy_run_command('', True), [1, 1, 0, 0, 0])

    @mock.patch('experimental_framework.benchmarks.instantiation_validation_benchmark.time')
    @mock.patch('os.chdir')
    @mock.patch('experimental_framework.common.run_command',
                side_effect=dummy_run_command_2)
    @mock.patch('experimental_framework.benchmarks.'
                'instantiation_validation_benchmark.'
                'InstantiationValidationBenchmark._get_pids')
    @mock.patch('os.kill', side_effect=dummy_os_kill)
    def test__init_packet_checker_for_success(self, mock_kill, mock_pids,
                                              mock_run_command, mock_chdir, mock_time):
        global command_counter
        command_counter = [0, 0, 0, 0, 0]
        mock_pids.return_value = [1234, 4321]
        self.iv.pkt_checker_command = 'test_sniff '
        self.iv.interface_name = 'interface'
        self.iv.params[iv_module.VLAN_RECEIVER] = '100'
        self.iv._init_packet_checker()
        self.assertEqual(dummy_run_command('', True), [1, 1, 1, 1, 1])

    @mock.patch('experimental_framework.common.get_file_first_line')
    def test__get_results_for_success(self, mock_get_file):
        self.iv.res_dir = 'directory'
        mock_get_file.side_effect = ['100', '50']
        expected = {'failure': '0'}
        output = self.iv._get_results()
        self.assertEqual(expected, output)

        mock_get_file.side_effect = ['10', '50']
        expected = {'failure': '1'}
        output = self.iv._get_results()
        self.assertEqual(expected, output)

    @mock.patch('experimental_framework.common.replace_in_file',
                side_effect=dummy_replace_in_file)
    def test__reset_lua_file_for_success(self, mock_replace):
        global replace_counter
        replace_counter = [0, 0, 0, 0, 0, 0]
        traffic_rate_percentage = '100'
        traffic_time = '60'
        self.iv.lua_file = 'file'
        self.iv.results_file = 'result_file'
        self.iv._reset_lua_file(traffic_rate_percentage, traffic_time)
        self.assertEqual(dummy_replace_in_file('', '', '', True),
                         [1, 1, 1, 0, 0, 0])

    @mock.patch('experimental_framework.common.replace_in_file',
                side_effect=dummy_replace_in_file)
    def test__configure_lua_file_for_success(self, mock_replace):
        global replace_counter
        replace_counter = [0, 0, 0, 0, 0, 0]
        traffic_rate_percentage = '100'
        traffic_time = '60'
        self.iv.lua_file = 'file'
        self.iv.results_file = 'result_file'
        self.iv._configure_lua_file(traffic_rate_percentage, traffic_time)
        self.assertEqual(dummy_replace_in_file('', '', '', True),
                         [0, 0, 0, 1, 1, 1])

    @mock.patch('experimental_framework.benchmarks.instantiation_validation_benchmark.time')
    @mock.patch('experimental_framework.common.LOG')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator',
                side_effect=DummyDpdkPacketGenerator)
    @mock.patch('experimental_framework.common.get_dpdk_pktgen_vars')
    def test_run_for_success(self, mock_common_get_vars, mock_pktgen,
                             mock_log, mock_time):
        rval = dict()
        rval[cfs.CFSP_DPDK_BUS_SLOT_NIC_2] = 'bus_2'
        rval[cfs.CFSP_DPDK_NAME_IF_2] = 'if_2'
        mock_common_get_vars.return_value = rval
        expected = {'test': 'result'}
        iv = DummyInstantiaionValidationBenchmark('InstantiationValidation',
                                                  dict())
        iv.params[iv_module.THROUGHPUT] = '1'
        output = iv.run()
        self.assertEqual(expected, output)
        self.assertEqual(DummyDpdkPacketGenerator.counter,
                         [1, 1])
        self.assertEqual(DummyInstantiaionValidationBenchmark.counter,
                         [1, 1, 1, 1, 1])
