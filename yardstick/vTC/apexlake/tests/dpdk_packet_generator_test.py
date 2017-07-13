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
from experimental_framework.constants import conf_file_sections as conf_file


from experimental_framework.packet_generators \
    import dpdk_packet_generator as mut


def dummy_get_dpdk_pktgen_vars():
    vars = dict()
    vars[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'pktgen_dir/'
    vars[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program'
    vars[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
    vars[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memchannel'
    return vars


def dummy_get_base_dir():
    return 'base_dir/'


def dummy_dirname(dir):
    if dir == 'pktgen_dir_test':
        return 'pktgen_dir'
    return 'test_directory'


class MockChangeVlan():

    ret_val = [False, False]

    @staticmethod
    def mock_change_vlan(pcap_dir=None, pcap_file=None, vlan=None):
        if not pcap_file and not vlan:
            return MockChangeVlan.ret_val

        if pcap_dir == 'base_dir/experimental_framework/packet_generators/' \
                       'pcap_files/' and \
                       pcap_file == 'pcap_file_1' and vlan == 'vlan0':
            MockChangeVlan.ret_val[0] = True
        if pcap_dir == 'base_dir/experimental_framework/packet_generators/' \
                       'pcap_files/' and \
                       pcap_file == 'pcap_file_2' and vlan == 'vlan1':
            MockChangeVlan.ret_val[1] = True
        return False


class TestDpdkPacketGenConstructor(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_constructor(self):
        obj = mut.DpdkPacketGenerator()
        self.assertEqual(obj.command, '')
        self.assertEqual(obj.directory, '')
        self.assertEqual(obj.dpdk_interfaces, -1)


class TestDpdkPacketGenInitialization(unittest.TestCase):

    def setUp(self):
        self.mut = mut.DpdkPacketGenerator()
        pass

    def tearDown(self):
        pass

    @mock.patch('os.path')
    @mock.patch('experimental_framework.common.get_dpdk_pktgen_vars',
                side_effect=dummy_get_dpdk_pktgen_vars)
    @mock.patch('experimental_framework.common.get_base_dir',
                side_effect=dummy_get_base_dir)
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator._get_core_nics')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_init_input_validation')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator._change_vlan')
    def test_init_dpdk_pktgen_for_success(self, m_change_vlan,
                                          mock_init_input_validation,
                                          mock_get_core_nics,
                                          common_get_base_dir,
                                          common_get_dpdk_vars,
                                          mock_path):
        """
        Tests the initialization of the packet generator
        """
        mock_init_input_validation.return_value = None
        mock_get_core_nics.return_value = "{corenics}"
        mock_path.isfile.return_value = True
        expected = 'sudo pktgen_dir/program -c coremask -n memchannel ' \
                   '--proc-type auto --file-prefix pg -- -T -P -m ' \
                   '"{corenics}" -f base_dir/experimental_framework/' \
                   'packet_generators/dpdk_pktgen/lua_file ' \
                   '-s 0:base_dir/experimental_framework/packet_generators' \
                   '/pcap_files/pcap_file > /dev/null'
        self.mut.init_dpdk_pktgen(dpdk_interfaces=1, lua_script='lua_file',
                                  pcap_file_0='pcap_file', vlan_0='vlan0')
        self.assertEqual(expected, self.mut.command)
        m_change_vlan.assert_called_once_with('base_dir/'
                                              'experimental_framework/'
                                              'packet_generators/pcap_files/',
                                              'pcap_file', 'vlan0')

    @mock.patch('os.path')
    @mock.patch('experimental_framework.common.get_dpdk_pktgen_vars',
                side_effect=dummy_get_dpdk_pktgen_vars)
    @mock.patch('experimental_framework.common.get_base_dir',
                side_effect=dummy_get_base_dir)
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator._get_core_nics')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_init_input_validation')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_change_vlan', side_effect=MockChangeVlan.mock_change_vlan)
    def test_init_dpdk_pktgen_2_for_success(self, m_change_vlan,
                                            mock_init_input_validation,
                                            mock_get_core_nics,
                                            common_get_base_dir,
                                            common_get_dpdk_vars, mock_path):
        """
        Tests the initialization of the packet generator
        :param common_get_base_dir: mock obj
        :param common_get_dpdk_vars: mock obj
        :param mock_path: mock obj
        :return: None
        """
        mock_init_input_validation.return_value = None
        mock_get_core_nics.return_value = "{corenics}"
        mock_path.isfile.return_value = True
        expected = 'sudo pktgen_dir/program -c coremask -n memchannel ' \
                   '--proc-type auto --file-prefix pg -- -T -P -m ' \
                   '"{corenics}" -f base_dir/experimental_framework/' \
                   'packet_generators/dpdk_pktgen/lua_file ' \
                   '-s 0:base_dir/experimental_framework/packet_generators/' \
                   'pcap_files/pcap_file_1 ' \
                   '-s 1:base_dir/experimental_framework/packet_generators/' \
                   'pcap_files/pcap_file_2 ' \
                   '> /dev/null'
        self.mut.init_dpdk_pktgen(dpdk_interfaces=1, lua_script='lua_file',
                                  pcap_file_0='pcap_file_1',
                                  pcap_file_1='pcap_file_2', vlan_0='vlan0',
                                  vlan_1='vlan1')
        self.assertEqual(expected, self.mut.command)
        self.assertEqual(MockChangeVlan.mock_change_vlan(), [True, True])

    @mock.patch('os.path')
    @mock.patch('experimental_framework.common.get_dpdk_pktgen_vars',
                side_effect=dummy_get_dpdk_pktgen_vars)
    @mock.patch('experimental_framework.common.get_base_dir',
                side_effect=dummy_get_base_dir)
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator._get_core_nics')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_init_input_validation')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator._change_vlan')
    def test_init_dpdk_pktgen_for_failure(self, m_change_vlan,
                                          mock_init_input_validation,
                                          mock_get_core_nics,
                                          common_get_base_dir,
                                          common_get_dpdk_vars,
                                          mock_path):
        """
        Tests the initialization of the packet generator
        :param common_get_base_dir: mock obj
        :param common_get_dpdk_vars: mock obj
        :param mock_path: mock obj
        :return: None
        """
        mock_init_input_validation.return_value = None
        mock_get_core_nics.return_value = "{corenics}"
        self.assertRaises(ValueError, self.mut.init_dpdk_pktgen, 1,
                          'lua_file', 'pcap_file')

    @mock.patch('os.path')
    @mock.patch('experimental_framework.common.get_dpdk_pktgen_vars',
                side_effect=dummy_get_dpdk_pktgen_vars)
    @mock.patch('experimental_framework.common.get_base_dir',
                side_effect=dummy_get_base_dir)
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_get_core_nics')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_init_input_validation')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_change_vlan')
    def test_init_dpdk_pktgen_for_failure_2(self, m_change_vlan,
                                            mock_init_input_validation,
                                            mock_get_core_nics,
                                            common_get_base_dir,
                                            common_get_dpdk_vars,
                                            mock_path):
        """
        Tests the initialization of the packet generator
        :param common_get_base_dir: mock obj
        :param common_get_dpdk_vars: mock obj
        :param mock_path: mock obj
        :return: None
        """
        mock_init_input_validation.return_value = None
        mock_get_core_nics.return_value = "{corenics}"
        self.assertRaises(ValueError, self.mut.init_dpdk_pktgen, 2,
                          'lua_file_1', 'pcap_file_1', 'pcap_file_2',
                          'vlan_0')


class DpdkPacketGeneratorDummy(mut.DpdkPacketGenerator):

    def __init__(self):
        self.directory = 'self_directory'
        self.dpdk_interfaces = 1
        self.command = 'command'
        self._count = 0

    chdir_test = [False, False]

    @staticmethod
    def _chdir(directory=None):
        if not directory:
            return DpdkPacketGeneratorDummy.chdir_test
        if directory == 'current_directory':
            DpdkPacketGeneratorDummy.chdir_test[0] = True
            # self._count += 1
        if directory == 'self_directory':
            DpdkPacketGeneratorDummy.chdir_test[1] = True
            # self._count += 1
        return DpdkPacketGeneratorDummy.chdir_test


class TestDpdkPacketGenSendTraffic(unittest.TestCase):

    def setUp(self):
        self.mut = DpdkPacketGeneratorDummy()

    @mock.patch('os.system')
    @mock.patch('os.path')
    @mock.patch('os.path.dirname', side_effect=dummy_dirname)
    @mock.patch('experimental_framework.common.get_dpdk_pktgen_vars',
                side_effect=dummy_get_dpdk_pktgen_vars)
    @mock.patch('experimental_framework.common.get_base_dir',
                side_effect=dummy_get_base_dir)
    @mock.patch('experimental_framework.common.run_command')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator._get_core_nics')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_init_physical_nics')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_finalize_physical_nics')
    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator._chdir',
                side_effect=DpdkPacketGeneratorDummy._chdir)
    def test_send_traffic_for_success(self, mock_ch_dir,
                                      mock_finalize_physical_nics,
                                      mock_init_physical_nics,
                                      mock_get_core_nics,
                                      common_run_command,
                                      common_get_base_dir,
                                      common_get_dpdk_vars,
                                      mock_dir_name,
                                      mock_os_path,
                                      mock_os_system):
        """
        Calls the packet generator and starts to send traffic
        Blocking call
        """
        mock_get_core_nics.return_value = "{corenics}"
        mock_os_path.realpath.return_value = 'pktgen_dir_test'
        mock_os_path.dirname.return_value = 'current_directory'
        self.mut.send_traffic()

        self.assertEqual(DpdkPacketGeneratorDummy._chdir(), [True, True])
        mock_init_physical_nics.\
            assert_called_once_with(1, {'coremask': 'coremask',
                                        'program_name': 'program',
                                        'memory_channels': 'memchannel',
                                        'pktgen_directory': 'pktgen_dir/'})
        mock_finalize_physical_nics.\
            assert_called_once_with(1, {'coremask': 'coremask',
                                        'program_name': 'program',
                                        'memory_channels': 'memchannel',
                                        'pktgen_directory': 'pktgen_dir/'})
        common_run_command.assert_called_once_with('command')


class MockRunCommand:

    ret_val = [False, False, False, False, False, False]
    ret_val_finalization = [False, False, False, False, False, False]

    @staticmethod
    def mock_run_command(command=None):
        if command == 'sudo ifconfig interface_1 down':
            MockRunCommand.ret_val[0] = True
        if command == 'sudo dpdk_directory/tools/dpdk_nic_bind.py ' \
                      '--unbind 1:00.0':
            MockRunCommand.ret_val[1] = True
        if command == 'sudo dpdk_directory/tools/dpdk_nic_bind.py ' \
                      '--bind=igb_uio 1:00.0':
            MockRunCommand.ret_val[2] = True
        if command == 'sudo ifconfig interface_2 down':
            MockRunCommand.ret_val[3] = True
        if command == 'sudo dpdk_directory/tools/dpdk_nic_bind.py ' \
                      '--unbind 1:00.1':
            MockRunCommand.ret_val[4] = True
        if command == 'sudo dpdk_directory/tools/dpdk_nic_bind.py ' \
                      '--bind=igb_uio 1:00.1':
            MockRunCommand.ret_val[5] = True
        else:
            return MockRunCommand.ret_val

    @staticmethod
    def mock_run_command_finalization(command=None):
        if command == 'sudo dpdk_directory/tools/dpdk_nic_bind.py ' \
                      '--unbind 1:00.0':
            MockRunCommand.ret_val_finalization[0] = True
        if command == 'sudo dpdk_directory/tools/dpdk_nic_bind.py ' \
                      '--bind=ixgbe 1:00.0':
            MockRunCommand.ret_val_finalization[1] = True
        if command == 'sudo ifconfig interface_1 up':
            MockRunCommand.ret_val_finalization[2] = True
        if command == 'sudo dpdk_directory/tools/dpdk_nic_bind.py ' \
                      '--unbind 1:00.1':
            MockRunCommand.ret_val_finalization[3] = True
        if command == 'sudo dpdk_directory/tools/dpdk_nic_bind.py ' \
                      '--bind=ixgbe 1:00.1':
            MockRunCommand.ret_val_finalization[4] = True
        if command == 'sudo ifconfig interface_2 up':
            MockRunCommand.ret_val_finalization[5] = True
        else:
            return MockRunCommand.ret_val_finalization


@mock.patch('experimental_framework.packet_generators.dpdk_packet_generator.time')
class TestDpdkPacketGenOthers(unittest.TestCase):

    def setUp(self):
        self.mut = mut.DpdkPacketGenerator()

    def tearDown(self):
        pass

    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_cores_configuration')
    def test__get_core_nics_for_failure(self, mock_cores_configuration, mock_time):
        mock_cores_configuration.return_value = None
        self.assertRaises(ValueError, mut.DpdkPacketGenerator._get_core_nics,
                          '', '')

    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_cores_configuration')
    def test__get_core_nics_one_nic_for_success(self,
                                                mock_cores_configuration, mock_time):
        mock_cores_configuration.return_value = 'ret_val'
        expected = 'ret_val'
        output = mut.DpdkPacketGenerator._get_core_nics(1, 'coremask')
        self.assertEqual(expected, output)
        mock_cores_configuration.assert_called_once_with('coremask', 1, 2, 0)

    @mock.patch('experimental_framework.packet_generators.'
                'dpdk_packet_generator.DpdkPacketGenerator.'
                '_cores_configuration')
    def test__get_core_nics_two_nics_for_success(self,
                                                 mock_cores_configuration, mock_time):
        mock_cores_configuration.return_value = 'ret_val'
        expected = 'ret_val'
        output = mut.DpdkPacketGenerator._get_core_nics(2, 'coremask')
        self.assertEqual(expected, output)
        mock_cores_configuration.assert_called_once_with('coremask', 1, 2, 2)

    @mock.patch('os.path.isfile')
    def test__init_input_validation_for_success(self, mock_is_file, mock_time):
        mock_is_file.return_value = True

        pcap_file_0 = 'pcap_file_0'
        pcap_file_1 = 'pcap_file_1'
        lua_script = 'lua_script'
        pcap_directory = 'pcap_directory'
        lua_directory = 'lua_directory'

        variables = dict()
        variables[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'directory'
        variables[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        variables[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        variables[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'

        self.assertEqual(mut.DpdkPacketGenerator._init_input_validation(
            pcap_file_0, pcap_file_1,
            lua_script, pcap_directory, lua_directory,
            variables), None)

    @mock.patch('os.path.isfile')
    def test__init_input_validation_for_failure(self, mock_is_file, mock_time):
        mock_is_file.return_value = True

        pcap_file_0 = 'pcap_file_0'
        pcap_file_1 = 'pcap_file_1'
        lua_script = 'lua_script'
        pcap_directory = 'pcap_directory'
        lua_directory = 'lua_directory'

        variables = dict()
        variables[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'directory'
        variables[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        variables[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        # variables[common.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'

        self.assertRaises(ValueError,
                          mut.DpdkPacketGenerator.
                          _init_input_validation, pcap_file_0, pcap_file_1,
                          lua_script, pcap_directory, lua_directory, variables)

    @mock.patch('os.path.isfile')
    def test__init_input_validation_for_failure_2(self, mock_is_file, mock_time):
        mock_is_file.return_value = True

        pcap_directory = None
        pcap_file_0 = 'pcap_file_0'
        pcap_file_1 = 'pcap_file_1'
        lua_script = 'lua_script'
        lua_directory = 'lua_directory'

        variables = dict()
        variables[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'directory'
        variables[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        variables[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        variables[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'

        self.assertRaises(ValueError,
                          mut.DpdkPacketGenerator.
                          _init_input_validation, pcap_file_0, pcap_file_1,
                          lua_script, pcap_directory, lua_directory, variables)

    @mock.patch('os.path.isfile')
    def test__init_input_validation_for_failure_3(self, mock_is_file, mock_time):
        mock_is_file.return_value = True

        pcap_directory = 'directory'
        pcap_file_0 = None
        pcap_file_1 = 'pcap_file_1'
        lua_script = 'lua_script'
        lua_directory = 'lua_directory'

        variables = dict()
        variables[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'directory'
        variables[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        variables[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        variables[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'

        self.assertRaises(ValueError,
                          mut.DpdkPacketGenerator.
                          _init_input_validation, pcap_file_0, pcap_file_1,
                          lua_script, pcap_directory, lua_directory, variables)

    @mock.patch('os.path.isfile')
    def test__init_input_validation_for_failure_4(self, mock_is_file, mock_time):
        mock_is_file.return_value = True

        pcap_directory = 'directory'
        pcap_file_0 = 'pcap_file_0'
        pcap_file_1 = None
        lua_script = 'lua_script'
        lua_directory = 'lua_directory'

        variables = dict()
        variables[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'directory'
        variables[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        variables[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        variables[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'

        self.assertRaises(ValueError,
                          mut.DpdkPacketGenerator.
                          _init_input_validation, pcap_file_0, pcap_file_1,
                          lua_script, pcap_directory, lua_directory, variables)

    @mock.patch('os.path.isfile')
    def test__init_input_validation_for_failure_5(self, mock_is_file, mock_time):
        mock_is_file.return_value = True

        pcap_directory = 'directory'
        pcap_file_0 = 'pcap_file_0'
        pcap_file_1 = 'pcap_file_1'
        lua_script = None
        lua_directory = 'lua_directory'

        variables = dict()
        variables[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'directory'
        variables[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        variables[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        variables[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'

        self.assertRaises(ValueError,
                          mut.DpdkPacketGenerator.
                          _init_input_validation, pcap_file_0, pcap_file_1,
                          lua_script, pcap_directory, lua_directory, variables)

    @mock.patch('os.path.isfile', side_effect=[False])
    def test__init_input_validation_for_failure_6(self, mock_is_file, mock_time):
        # mock_is_file.return_value = False

        pcap_directory = 'directory'
        pcap_file_0 = 'pcap_file_0'
        pcap_file_1 = 'pcap_file_1'
        lua_script = 'lua_script'
        lua_directory = 'lua_directory'

        variables = dict()
        variables[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'directory'
        variables[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        variables[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        variables[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'

        self.assertRaises(ValueError,
                          mut.DpdkPacketGenerator.
                          _init_input_validation, pcap_file_0, pcap_file_1,
                          lua_script, pcap_directory, lua_directory, variables)

    @mock.patch('os.path.isfile', side_effect=[True, False])
    def test__init_input_validation_for_failure_7(self, mock_is_file, mock_time):
        pcap_directory = 'directory'
        pcap_file_0 = 'pcap_file_0'
        pcap_file_1 = 'pcap_file_1'
        lua_script = 'lua_script'
        lua_directory = 'lua_directory'

        variables = dict()
        variables[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'directory'
        variables[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        variables[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        variables[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'

        self.assertRaises(ValueError,
                          mut.DpdkPacketGenerator.
                          _init_input_validation, pcap_file_0, pcap_file_1,
                          lua_script, pcap_directory, lua_directory, variables)

    @mock.patch('os.path.isfile', side_effect=[True, True, False])
    def test__init_input_validation_for_failure_8(self, mock_is_file, mock_time):
        pcap_directory = 'directory'
        pcap_file_0 = 'pcap_file_0'
        pcap_file_1 = 'pcap_file_1'
        lua_script = 'lua_script'
        lua_directory = 'lua_directory'

        variables = dict()
        variables[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'directory'
        variables[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        variables[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        variables[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'

        self.assertRaises(ValueError,
                          mut.DpdkPacketGenerator.
                          _init_input_validation, pcap_file_0, pcap_file_1,
                          lua_script, pcap_directory, lua_directory, variables)

    @mock.patch('os.chdir')
    def test__chdir_for_success(self, mock_os_chdir, mock_time):
        mut.DpdkPacketGenerator._chdir('directory')
        mock_os_chdir.assert_called_once_with('directory')

    @mock.patch('experimental_framework.common.run_command',
                side_effect=MockRunCommand.mock_run_command)
    def test__init_physical_nics_for_success(self, mock_run_command, mock_time):
        dpdk_interfaces = 1
        dpdk_vars = dict()

        dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] = 'dpdk_directory/'
        dpdk_vars[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'pktgen_directory/'
        dpdk_vars[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        dpdk_vars[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        dpdk_vars[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'
        dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_1] = '1:00.0'
        dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_2] = '1:00.1'
        dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_1] = 'interface_1'
        dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_2] = 'interface_2'
        self.mut._init_physical_nics(dpdk_interfaces, dpdk_vars)
        self.assertEqual(MockRunCommand.mock_run_command(),
                         [True, True, True, False, False, False])

    @mock.patch('experimental_framework.common.run_command',
                side_effect=MockRunCommand.mock_run_command)
    def test__init_physical_nics_for_success_2(self, mock_run_command, mock_time):
        dpdk_interfaces = 2
        dpdk_vars = dict()

        dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] = 'dpdk_directory/'
        dpdk_vars[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'pktgen_directory/'
        dpdk_vars[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        dpdk_vars[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        dpdk_vars[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'
        dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_1] = '1:00.0'
        dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_2] = '1:00.1'
        dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_1] = 'interface_1'
        dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_2] = 'interface_2'
        self.mut._init_physical_nics(dpdk_interfaces, dpdk_vars)
        self.assertEqual(MockRunCommand.mock_run_command(),
                         [True, True, True, True, True, True])

    @mock.patch('experimental_framework.common.run_command')
    def test__init_physical_nics_for_failure(self, mock_run_command, mock_time):
        dpdk_interfaces = 3
        dpdk_vars = dict()
        self.assertRaises(ValueError, self.mut._init_physical_nics,
                          dpdk_interfaces, dpdk_vars)

    @mock.patch('experimental_framework.common.run_command',
                side_effect=MockRunCommand.mock_run_command_finalization)
    def test__finalize_physical_nics_for_success(self, mock_run_command, mock_time):
        dpdk_interfaces = 1
        dpdk_vars = dict()
        dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] = 'dpdk_directory/'
        dpdk_vars[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'pktgen_directory/'
        dpdk_vars[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        dpdk_vars[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        dpdk_vars[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'
        dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_1] = '1:00.0'
        dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_2] = '1:00.1'
        dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_1] = 'interface_1'
        dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_2] = 'interface_2'
        self.mut._finalize_physical_nics(dpdk_interfaces, dpdk_vars)
        self.assertEqual(MockRunCommand.mock_run_command_finalization(),
                         [True, True, True, False, False, False])

    @mock.patch('experimental_framework.common.run_command',
                side_effect=MockRunCommand.mock_run_command_finalization)
    def test__finalize_physical_nics_for_success_2(self, mock_run_command, mock_time):
        dpdk_interfaces = 2
        dpdk_vars = dict()
        dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] = 'dpdk_directory/'
        dpdk_vars[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY] = 'pktgen_directory/'
        dpdk_vars[conf_file.CFSP_DPDK_PROGRAM_NAME] = 'program_name'
        dpdk_vars[conf_file.CFSP_DPDK_COREMASK] = 'coremask'
        dpdk_vars[conf_file.CFSP_DPDK_MEMORY_CHANNEL] = 'memory_channels'
        dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_1] = '1:00.0'
        dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_2] = '1:00.1'
        dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_1] = 'interface_1'
        dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_2] = 'interface_2'
        self.mut._finalize_physical_nics(dpdk_interfaces, dpdk_vars)
        self.assertEqual(MockRunCommand.mock_run_command_finalization(),
                         [True, True, True, True, True, True])

    def test__finalize_physical_nics_for_failure(self, mock_time):
        dpdk_interfaces = 0
        dpdk_vars = dict()
        self.assertRaises(ValueError, self.mut._finalize_physical_nics,
                          dpdk_interfaces, dpdk_vars)

    def test__cores_configuration_for_success(self, mock_time):
        coremask = '1f'
        expected = '[2:1].0,[4:3].1'
        output = mut.DpdkPacketGenerator._cores_configuration(coremask,
                                                              1, 2, 2)
        self.assertEqual(expected, output)

    def test__cores_configuration_for_success_2(self, mock_time):
        coremask = '1f'
        expected = '2.0,[4:3].1'
        output = mut.DpdkPacketGenerator._cores_configuration(coremask,
                                                              1, 1, 2)
        self.assertEqual(expected, output)

    def test__cores_configuration_for_success_3(self, mock_time):
        coremask = '1f'
        expected = '[3:2].0,4.1'
        output = mut.DpdkPacketGenerator._cores_configuration(coremask,
                                                              1, 2, 1)
        self.assertEqual(expected, output)

    def test__cores_configuration_for_failure(self, mock_time):
        coremask = '1'
        self.assertRaises(ValueError,
                          mut.DpdkPacketGenerator._cores_configuration,
                          coremask, 1, 2, 2)

    @mock.patch('experimental_framework.common.LOG')
    @mock.patch('experimental_framework.common.run_command')
    def test__change_vlan_for_success(self, mock_run_command, mock_log, mock_time):
        mut.DpdkPacketGenerator._change_vlan('/directory/', 'pcap_file', '10')
        expected_param = '/directory/vlan_tag.sh /directory/pcap_file 10'
        mock_run_command.assert_called_with(expected_param)
