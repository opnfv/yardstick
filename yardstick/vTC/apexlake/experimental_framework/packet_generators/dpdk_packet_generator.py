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
import base_packet_generator
import experimental_framework.common as common
import time
from experimental_framework.constants import conf_file_sections as conf_file
from experimental_framework.constants import framework_parameters as fp


class DpdkPacketGenerator(base_packet_generator.BasePacketGenerator):

    def __init__(self):
        base_packet_generator.BasePacketGenerator.__init__(self)
        self.command = ''
        self.directory = ''
        self.program_name = ''
        self.command_options = list()
        self.dpdk_interfaces = -1

    def send_traffic(self):
        '''
        Calls the packet generator and starts to send traffic
        Blocking call
        '''
        current_dir = os.path.dirname(os.path.realpath(__file__))
        DpdkPacketGenerator._chdir(self.directory)
        dpdk_vars = common.get_dpdk_pktgen_vars()
        self._init_physical_nics(self.dpdk_interfaces, dpdk_vars)
        common.run_command(self.command)
        self._finalize_physical_nics(self.dpdk_interfaces, dpdk_vars)
        DpdkPacketGenerator._chdir(current_dir)

    def init_dpdk_pktgen(self,
                         dpdk_interfaces,
                         lua_script='generic_test.lua',
                         pcap_file_0='',
                         pcap_file_1='',
                         vlan_0='',
                         vlan_1=''):
        """
        Initializes internal parameters and configuration of the module.
        Needs to be called before the send_traffic
        :param dpdk_interfaces: Number of interfaces to be used (type: int)
        :param lua_script: Full path of the Lua script to be used (type: str)
        :param pcap_file_0: Full path of the Pcap file to be used for port 0
                            (type: str)
        :param pcap_file_1: Full path of the Pcap file to be used for port 1
                            (type: str)
        :param vlan_0: VLAN tag to be used for port 0 (type: str)
        :param vlan_1: VLAN tag to be used for port 1 (type: str)
        :return:
        """
        # Input Validation
        if pcap_file_0 and not vlan_0:
            message = 'In order to use NIC_0, the parameter vlan_0 is required'
            raise ValueError(message)
        if dpdk_interfaces > 1 and pcap_file_1 and not vlan_1:
            message = 'in order to use NIC_1, the parameter vlan_1 is required'
            raise ValueError(message)

        self.dpdk_interfaces = dpdk_interfaces
        vars = common.get_dpdk_pktgen_vars()

        lua_directory = common.get_base_dir()
        lua_directory += fp.EXPERIMENTAL_FRAMEWORK_DIR
        lua_directory += fp.DPDK_PKTGEN_DIR

        pcap_directory = common.get_base_dir()
        pcap_directory += fp.EXPERIMENTAL_FRAMEWORK_DIR
        pcap_directory += fp.PCAP_DIR

        DpdkPacketGenerator._init_input_validation(pcap_file_0,
                                                   pcap_file_1,
                                                   lua_script,
                                                   pcap_directory,
                                                   lua_directory,
                                                   vars)

        self.directory = vars[conf_file.CFSP_DPDK_PKTGEN_DIRECTORY]
        self.program_name = vars[conf_file.CFSP_DPDK_PROGRAM_NAME]

        core_nics = DpdkPacketGenerator.\
            _get_core_nics(dpdk_interfaces, vars[conf_file.CFSP_DPDK_COREMASK])
        self.command_options = ['-c ' + vars[conf_file.CFSP_DPDK_COREMASK],
                                '-n ' + vars[conf_file.
                                             CFSP_DPDK_MEMORY_CHANNEL],
                                '--proc-type auto',
                                '--file-prefix pg',
                                '-- -T',
                                '-P',
                                '-m "' + core_nics + '"',
                                '-f ' + lua_directory + lua_script,
                                '-s 0:' + pcap_directory + pcap_file_0]

        if pcap_file_1:
            self.command_options.append('-s 1:' + pcap_directory + pcap_file_1)

        # Avoid to show the output of the packet generator
        self.command_options.append('> /dev/null')
        # Prepare the command to be invoked
        self.command = self.directory + self.program_name
        for opt in self.command_options:
            self.command += (' ' + opt)
        if pcap_file_0 and vlan_0:
            DpdkPacketGenerator._change_vlan(pcap_directory, pcap_file_0,
                                             vlan_0)
        if pcap_file_1 and vlan_1:
            DpdkPacketGenerator._change_vlan(pcap_directory, pcap_file_1,
                                             vlan_1)

    @staticmethod
    def _get_core_nics(dpdk_interfaces, coremask):
        """
        Retruns the core_nics string to be used in the dpdk pktgen command
        :param dpdk_interfaces: number of interfaces to be used in the pktgen
                                (type: int)
        :param coremask: hexadecimal value representing the cores assigned to
                         the pktgen (type: str)
        :return: Returns the core nics param for pktgen (type: str)
        """
        if dpdk_interfaces == 1:
            return DpdkPacketGenerator._cores_configuration(coremask, 1, 2, 0)
        elif dpdk_interfaces == 2:
            return DpdkPacketGenerator._cores_configuration(coremask, 1, 2, 2)
        raise ValueError("This framework only supports two ports to generate "
                         "traffic")

    @staticmethod
    def _change_vlan(pcap_directory, pcap_file, vlan):
        common.LOG.info("Changing VLAN Tag on Packet: " + pcap_file +
                        ". New VLAN Tag is " + vlan)
        command = "chmod +x {}{}".format(pcap_directory, 'vlan_tag.sh')
        common.run_command(command)
        command = pcap_directory + 'vlan_tag.sh '
        command += pcap_directory + pcap_file + ' ' + vlan
        common.run_command(command)

    @staticmethod
    def _init_input_validation(pcap_file_0, pcap_file_1, lua_script,
                               pcap_directory, lua_directory, variables):
        """
        Validates the input parameters values and raises an exception if
        there is any non valid param
        :param pcap_file_0: file name of the pcap file for NIC 0
                            (it does not includes the path) (type: str)
        :param pcap_file_1: file name of the pcap file for NIC 1
                            (it does not includes the path) (type: str)
        :param lua_script: file name of the lua script to be used
                            (it does not includes the path) (type: str)
        :param pcap_directory: directory where the pcap files are located
                               (type: str)
        :param lua_directory:  directory where the lua scripts are located
                               (type: str)
        :param variables: variables for the packet gen from configuration file
                          (type: dict)
        :return: None
        """
        if not pcap_directory:
            raise ValueError("pcap_directory not provided correctly")
        if not pcap_file_0:
            raise ValueError("pcap_file_0 not provided correctly")
        if not pcap_file_1:
            raise ValueError("pcap_file_1 not provided correctly")
        if not lua_script:
            raise ValueError("lua_script not provided correctly")
        if not os.path.isfile(pcap_directory + pcap_file_0):
            raise ValueError("The file " + pcap_file_0 + " does not exist")
        if not os.path.isfile(pcap_directory + pcap_file_1):
            raise ValueError("The file " + pcap_file_1 + " does not exist")
        if not os.path.isfile(lua_directory + lua_script):
            raise ValueError("The file " + lua_script + " does not exist")
        for var in [conf_file.CFSP_DPDK_PKTGEN_DIRECTORY,
                    conf_file.CFSP_DPDK_PROGRAM_NAME,
                    conf_file.CFSP_DPDK_COREMASK,
                    conf_file.CFSP_DPDK_MEMORY_CHANNEL]:
            if var not in variables.keys() or (var in variables.keys() and
               variables[var] is ''):
                raise ValueError("The variable " + var + " does not exist")

    @staticmethod
    def _chdir(directory):
        """
        Changes the current directory
        :param directory: directory where to move (type: str)
        :return: None
        """
        os.chdir(directory)

    def _init_physical_nics(self, dpdk_interfaces, dpdk_vars):
        """
        Initializes the physical interfaces
        :param dpdk_interfaces: Number of interfaces to be used (type: int)
        :param dpdk_vars: variables from config file related to DPDK pktgen
                          (type: dict)
        :return: None
        """
        if not dpdk_interfaces == 1 and not dpdk_interfaces == 2:
            raise ValueError('The number of NICs can be 1 or 2')
        # Initialize NIC 1
        # bus_address_1 = dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_1]
        interface_1 = dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_1]
        common.run_command('ifconfig ' + interface_1 + ' down')
        common.run_command(dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] +
                           'tools/dpdk_nic_bind.py --unbind ' +
                           dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_1])
        common.run_command(dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] +
                           'tools/dpdk_nic_bind.py --bind=igb_uio ' +
                           dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_1])
        if dpdk_interfaces == 2:
            # Initialize NIC 2
            # bus_address_2 = dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_2]
            interface_2 = dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_2]
            common.run_command('ifconfig ' + interface_2 + ' down')
            common.run_command(dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] +
                               'tools/dpdk_nic_bind.py --unbind ' +
                               dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_2])
            common.run_command(dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] +
                               'tools/dpdk_nic_bind.py --bind=igb_uio ' +
                               dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_2])

    def _finalize_physical_nics(self, dpdk_interfaces, dpdk_vars):
        """
        Finalizes the physical interfaces
        :param dpdk_interfaces: Number of interfaces to be used (type: int)
        :param dpdk_vars: variables from config file related to DPDK pktgen
                          (type: dict)
        :return: None
        """
        if not dpdk_interfaces == 1 and not dpdk_interfaces == 2:
            raise ValueError('No interfaces have been indicated for packet '
                             'generation usage. Please specify one or two '
                             'NICs')
        # Initialize NIC 1
        common.run_command(dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] +
                           'tools/dpdk_nic_bind.py --unbind ' +
                           dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_1])
        time.sleep(5)
        common.run_command(dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] +
                           'tools/dpdk_nic_bind.py --bind=ixgbe ' +
                           dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_1])
        common.run_command('ifconfig ' +
                           dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_1] +
                           ' up')
        if dpdk_interfaces == 2:
            # Initialize NIC 2
            common.run_command(dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] +
                               'tools/dpdk_nic_bind.py --unbind ' +
                               dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_2])
            time.sleep(5)
            common.run_command(dpdk_vars[conf_file.CFSP_DPDK_DPDK_DIRECTORY] +
                               'tools/dpdk_nic_bind.py --bind=ixgbe ' +
                               dpdk_vars[conf_file.CFSP_DPDK_BUS_SLOT_NIC_2])
            common.run_command('ifconfig ' +
                               dpdk_vars[conf_file.CFSP_DPDK_NAME_IF_2] +
                               ' up')

    @staticmethod
    def _cores_configuration(coremask, pktgen_cores=1, nic_1_cores=2,
                             nic_2_cores=2):
        """
        Calculation of the core_nics parameter which is necessary for the
        packet generator to run

        :param coremask: Hexadecimal value indicating the cores to be assigned
                         to the whole dpdk pktgen software (included the
                         ones to receive and send packets from NICs)
                         (type: str)
        :param pktgen_cores: number of cores to be assigned to main thread of
                             the pktgen directly
        :param nic_1_cores: number of cores to be assigned to the first NIC
        :param nic_2_nics: number of cores to be assigned to the second NIC
        :return: returns the core_nics parameter (type: str)
        """
        required_cores = pktgen_cores + nic_1_cores + nic_2_cores
        bin_coremask = bin(int(coremask, 16))[2:]
        index = len(bin_coremask)
        cores = []
        while index >= 0:
            index -= 1
            if bin_coremask[index] == '1':
                core = index
                cores.append(core)
        if len(cores) < required_cores:
            raise ValueError('The provided coremask does not provide'
                             ' enough cores for the DPDK packet generator')
        # ret_pktgen_cores = []
        ret_nic_1_cores = []
        ret_nic_2_cores = []
        current_core = 0

        if nic_2_cores > 0:
            ret_nic_2_cores.append(cores[current_core])
            current_core += 1
        if nic_2_cores > 1:
            ret_nic_2_cores.append(cores[current_core])
            current_core += 1

        if nic_1_cores > 0:
            ret_nic_1_cores.append(cores[current_core])
            current_core += 1
        if nic_1_cores > 1:
            ret_nic_1_cores.append(cores[current_core])
            current_core += 1

        # for n in range(0, pktgen_cores):
        #     ret_pktgen_cores.append(cores[n])
        # for n in range(0, nic_1_cores):
        #     ret_nic_1_cores.append(cores[pktgen_cores + n])
        # for n in range(0, nic_2_cores):
        #     ret_nic_2_cores.append(cores[pktgen_cores + nic_1_cores + n])

        corenics = ''
        if nic_1_cores > 0:
            if nic_1_cores < 2:
                corenics += str(ret_nic_1_cores[0]) + '.0'
            if nic_1_cores == 2:
                corenics += '[' + str(ret_nic_1_cores[0])
                corenics += ':' + str(ret_nic_1_cores[1])
                corenics += '].0'
        if nic_2_cores > 0:
            corenics += ','
            if nic_2_cores < 2:
                corenics += str(ret_nic_2_cores[0]) + '.1'
            if nic_2_cores == 2:
                corenics += '[' + str(ret_nic_2_cores[0])
                corenics += ':' + str(ret_nic_2_cores[1])
                corenics += '].1'
        return corenics
