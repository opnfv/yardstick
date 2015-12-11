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
import commands
import signal
import time
from experimental_framework.benchmarks import benchmark_base_class as base
from experimental_framework.constants import framework_parameters as fp
from experimental_framework.constants import conf_file_sections as cfs
from experimental_framework.packet_generators import dpdk_packet_generator \
    as dpdk
import experimental_framework.common as common


THROUGHPUT = 'throughput'
VLAN_SENDER = 'vlan_sender'
VLAN_RECEIVER = 'vlan_receiver'
PACKETS_FILE_NAME = 'packets.res'
PACKET_CHECKER_PROGRAM_NAME = 'test_sniff'
MULTICAST_GROUP = '224.192.16.1'


class InstantiationValidationBenchmark(base.BenchmarkBaseClass):

    def __init__(self, name, params):
        base.BenchmarkBaseClass.__init__(self, name, params)
        self.base_dir = common.get_base_dir() + \
            fp.EXPERIMENTAL_FRAMEWORK_DIR + fp.DPDK_PKTGEN_DIR
        self.results_file = self.base_dir + PACKETS_FILE_NAME
        self.lua_file = self.base_dir + 'constant_traffic.lua'
        self.res_dir = ''
        self.interface_name = ''

        # Set the packet checker command
        self.pkt_checker_command = common.get_base_dir()
        self.pkt_checker_command += 'experimental_framework/libraries/'
        self.pkt_checker_command += 'packet_checker/'
        self.pkt_checker_command += PACKET_CHECKER_PROGRAM_NAME + ' '

    def init(self):
        """
        Initialize the benchmark
        :return: None
        """
        pass

    def finalize(self):
        """
        Finalizes the benchmark
        :return: None
        """
        pass

    def get_features(self):
        features = dict()
        features['description'] = 'Instantiation Validation Benchmark'
        features['parameters'] = [THROUGHPUT, VLAN_SENDER, VLAN_RECEIVER]
        features['allowed_values'] = dict()
        features['allowed_values'][THROUGHPUT] = map(str, range(0, 100))
        features['allowed_values'][VLAN_SENDER] = map(str, range(-1, 4096))
        features['allowed_values'][VLAN_RECEIVER] = map(str, range(-1, 4096))
        features['default_values'] = dict()
        features['default_values'][THROUGHPUT] = '1'
        features['default_values'][VLAN_SENDER] = '-1'
        features['default_values'][VLAN_RECEIVER] = '-1'
        return features

    def run(self):
        # Setup packet generator
        traffic_time = '10'
        packet_size = '512'
        traffic_rate_percentage = self.params[THROUGHPUT]

        dpdk_pktgen_vars = common.get_dpdk_pktgen_vars()
        #bus_address = dpdk_pktgen_vars[cfs.CFSP_DPDK_BUS_SLOT_NIC_2]
        self.interface_name = dpdk_pktgen_vars[cfs.CFSP_DPDK_NAME_IF_2]
        packetgen = dpdk.DpdkPacketGenerator()
        self._configure_lua_file(traffic_rate_percentage, traffic_time)
        packetgen.init_dpdk_pktgen(dpdk_interfaces=1,
                                   pcap_file_0='packet_' + packet_size +
                                               '.pcap',
                                   pcap_file_1='igmp.pcap',
                                   lua_script='constant_traffic.lua',
                                   vlan_0=self.params[VLAN_SENDER],
                                   vlan_1=self.params[VLAN_RECEIVER])

        self._init_packet_checker()
        # Send constant traffic at a specified rate
        common.LOG.debug('Start the packet generator')
        packetgen.send_traffic()
        common.LOG.debug('Stop the packet generator')
        time.sleep(5)
        self._finalize_packet_checker()
        self._reset_lua_file(traffic_rate_percentage, traffic_time)
        return self._get_results()

    def _configure_lua_file(self, traffic_rate_percentage, traffic_time):
        """
        Configure the packet gen to write the results into the right file
        :return: None
        """
        common.replace_in_file(self.lua_file, 'local out_file = ""',
                               'local out_file = "' +
                               self.results_file + '"')
        common.replace_in_file(self.lua_file, 'local traffic_rate = 0',
                               'local traffic_rate = ' +
                               traffic_rate_percentage)
        common.replace_in_file(self.lua_file, 'local traffic_delay = 0',
                               'local traffic_delay = ' + traffic_time)

    def _reset_lua_file(self, traffic_rate_percentage, traffic_time):
        """
        Configure the packet gen to write the results into the right file
        :param traffic_rate_percentage:
        :param traffic_time:
        :return: None
        """

        common.replace_in_file(self.lua_file, 'local out_file = "' +
                               self.results_file + '"',
                               'local out_file = ""')
        common.replace_in_file(self.lua_file, 'local traffic_rate = ' +
                               traffic_rate_percentage,
                               'local traffic_rate = 0')
        common.replace_in_file(self.lua_file, 'local traffic_delay = ' +
                               traffic_time, 'local traffic_delay = 0')

    def _get_results(self):
        ret_val = dict()
        packet_checker_res = 0
        if self.res_dir:
            packet_checker_res = \
                int(common.get_file_first_line(self.res_dir +
                                               '/packet_checker.res'))
        pkt_gen_res = int(common.get_file_first_line(self.results_file))
        if pkt_gen_res <= packet_checker_res or \
           (float(pkt_gen_res - packet_checker_res) / pkt_gen_res) <= 0.1:
            ret_val['failure'] = '0'
        else:
            ret_val['failure'] = '1'
        return ret_val

    def _init_packet_checker(self):
        """
        Sets up the multicast and starts the packet checker
        :return:
        """
        # Kill any other process running from previous failed execution
        self.res_dir = os.getcwd()
        pids = self._get_pids()
        for pid in pids:
            os.kill(pid, signal.SIGTERM)

        # initialization of the VLAN interface
        command = "ip link add link "
        command += self.interface_name
        command += " name "
        command += self.interface_name + '.' + self.params[VLAN_RECEIVER]
        command += " type vlan id " + self.params[VLAN_RECEIVER]
        common.run_command(command)

        # set up the new
        command = 'ifconfig ' + self.interface_name + '.' + \
                  self.params[VLAN_RECEIVER]
        # An IP address is required for the interface to receive a multicast
        # flow. The specific address is not important
        command += ' 10.254.254.254 up'
        common.run_command(command)

        # configure smcroute
        command = "echo 'mgroup from "
        command += self.interface_name + '.' + self.params[VLAN_RECEIVER]
        command += " group "
        command += MULTICAST_GROUP
        command += "' > /etc/smcroute.conf"
        common.run_command(command)

        # run smcroute on the interface
        command = 'smcroute -d'
        common.run_command(command)

        # Start the packet checker
        command = self.pkt_checker_command
        command += self.interface_name + '.' + self.params[VLAN_RECEIVER]
        command += ' 128'
        command += ' &'
        common.run_command(command)

    def _finalize_packet_checker(self):
        """
        Obtains the PID of the packet checker and sends an alarm to
        terminate it
        :return: None
        """
        pids = self._get_pids()
        for pid in pids:
            os.kill(pid, signal.SIGTERM)

        # stop smcroute on the interface
        command = 'smcroute -k'
        common.run_command(command)

        # finalization of the VLAN interface
        command = "ip link delete "
        command += self.interface_name + '.' + self.params[VLAN_RECEIVER]
        common.run_command(command)

    def _get_pids(self):
        """
        Returns a list of integers containing the pid or the pids of the
        processes currently running on the host
        :return: type: list of int
        """
        output = commands.getoutput("ps -ef |pgrep " +
                                    PACKET_CHECKER_PROGRAM_NAME)
        if not output:
            pids = []
        else:
            pids = map(int, output.split('\n'))
        return pids
