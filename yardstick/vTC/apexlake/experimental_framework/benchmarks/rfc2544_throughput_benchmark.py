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

from experimental_framework.benchmarks import benchmark_base_class
from experimental_framework.packet_generators \
    import dpdk_packet_generator as dpdk
import experimental_framework.common as common
from experimental_framework.constants import framework_parameters as fp


PACKET_SIZE = 'packet_size'
VLAN_SENDER = 'vlan_sender'
VLAN_RECEIVER = 'vlan_receiver'


class RFC2544ThroughputBenchmark(benchmark_base_class.BenchmarkBaseClass):
    """
    Calculates the throughput of the VNF under test according to the RFC2544.
    """

    def __init__(self, name, params):
        benchmark_base_class.BenchmarkBaseClass.__init__(self, name, params)
        self.base_dir = common.get_base_dir() + \
                        fp.EXPERIMENTAL_FRAMEWORK_DIR + fp.DPDK_PKTGEN_DIR
        self.results_file = self.base_dir + 'experiment.res'
        self.lua_file = self.base_dir + 'rfc2544.lua'

    def init(self):
        """
        Initialize the benchmark
        :return: None
        """
        pass

    def finalize(self):
        """
        :return: None
        """
        pass

    def get_features(self):
        """
        Returns the features associated to the benchmark
        :return:
        """
        features = dict()
        features['description'] = 'RFC 2544 Throughput calculation'
        features['parameters'] = [PACKET_SIZE, VLAN_SENDER, VLAN_RECEIVER]
        features['allowed_values'] = dict()
        features['allowed_values'][PACKET_SIZE] = ['64', '128', '256', '512',
                                                   '1024', '1280', '1514']
        features['allowed_values'][VLAN_SENDER] = map(str, range(-1, 4096))
        features['allowed_values'][VLAN_RECEIVER] = map(str, range(-1, 4096))
        features['default_values'] = dict()
        features['default_values'][PACKET_SIZE] = '1280'
        features['default_values'][VLAN_SENDER] = '1007'
        features['default_values'][VLAN_RECEIVER] = '1006'
        return features

    def run(self):
        """
        Sends and receive traffic according to the RFC methodology in order
        to measure the throughput of the workload
        :return: Results of the testcase (type: dict)
        """
        ret_val = dict()
        packet_size = self._extract_packet_size_from_params()
        ret_val[PACKET_SIZE] = packet_size

        # Packetgen management
        packetgen = dpdk.DpdkPacketGenerator()
        self._configure_lua_file()
        packetgen.init_dpdk_pktgen(dpdk_interfaces=2,
                                   pcap_file_0='packet_' +
                                               packet_size + '.pcap',
                                   pcap_file_1='igmp.pcap',
                                   lua_script='rfc2544.lua',
                                   vlan_0=self.params[VLAN_SENDER],
                                   vlan_1=self.params[VLAN_RECEIVER])
        common.LOG.debug('Start the packet generator - packet size: ' +
                         str(packet_size))
        packetgen.send_traffic()
        common.LOG.debug('Stop the packet generator')

        # Result Collection
        results = self._get_results()
        for metric_name in results.keys():
            ret_val[metric_name] = results[metric_name]
        self._reset_lua_file()
        return ret_val

    def _extract_packet_size_from_params(self):
        """
        Extracts packet sizes from parameters
        :return: packet_sizes (list)
        """
        packet_size = '1280'  # default value
        if PACKET_SIZE in self.params.keys() and \
                isinstance(self.params[PACKET_SIZE], str):
            packet_size = self.params[PACKET_SIZE]
        return packet_size

    def _configure_lua_file(self):
        """
        Configure the packet gen to write the results into the right file
        :return: None
        """
        common.replace_in_file(self.lua_file, 'local out_file = ""',
                               'local out_file = "' +
                               self.results_file + '"')

    def _reset_lua_file(self):
        """
        Sets back the configuration of the local file var to the default
        :return:
        """
        common.replace_in_file(self.lua_file, 'local out_file = "' +
                               self.results_file + '"',
                               'local out_file = ""')

    def _get_results(self):
        """
        Returns the results of the experiment
        :return: None
        """
        throughput = common.get_file_first_line(self.results_file)
        ret_val = dict()
        try:
            ret_val['throughput'] = int(throughput)
        except:
            ret_val['throughput'] = 0
        return ret_val