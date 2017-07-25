# Copyright 2016 Red Hat Inc & Xena Networks.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Contributors:
#   Rick Alongi, Red Hat Inc.
#   Amit Supugade, Red Hat Inc.
#   Dan Amzulescu, Xena Networks
#   Christian Trautman, Red Hat Inc.

"""
Xena Traffic Generator Model
"""

# python imports
from __future__ import print_function
import binascii
import logging
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from time import sleep

import scapy.layers.inet as inet

from yardstick.traffic_generator.conf import merge_spec
from yardstick.traffic_generator.conf import settings
from yardstick.traffic_generator.core.results.results_constants import ResultsConstants
from yardstick.traffic_generator.tools.pkt_gen.trafficgen.trafficgen import ITrafficGenerator
from yardstick.traffic_generator.tools.pkt_gen.xena.XenaDriver import (
    aggregate_stats,
    line_percentage,
    XenaSocketDriver,
    XenaManager,
    )
from yardstick.traffic_generator.tools.pkt_gen.xena.json.xena_json_mesh import XenaJSONMesh
from yardstick.traffic_generator.tools.pkt_gen.xena.json.xena_json_blocks import XenaJSONBlocks
from yardstick.traffic_generator.tools.pkt_gen.xena.json.xena_json_pairs import XenaJSONPairs

_CURR_DIR = os.path.dirname(os.path.realpath(__file__))

class Xena(ITrafficGenerator):
    """
    Xena Traffic generator wrapper class
    """
    _logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()
        self.mono_pipe = None
        self.xmanager = None
        self._params = {}
        self._xsocket = None
        self._duration = None
        self.tx_stats = None
        self.rx_stats = None
        self._log_handle = None

        user_home = os.path.expanduser('~')
        self._log_path = '{}/Xena/Xena2544-2G/Logs/xena2544.log'.format(
            user_home)

        # make the folder and log file if they doesn't exist
        if not os.path.exists(self._log_path):
            os.makedirs(os.path.dirname(self._log_path))

        # empty the file contents
        open(self._log_path, 'w').close()

    @staticmethod
    def _create_throughput_result(root):
        """
        Create the results based off the output xml file from the Xena2544.exe
        execution
        :param root: root dictionary from xml import
        :return: Results Ordered dictionary based off ResultsConstants
        """
        # get the test type from the report file
        test_type = root[0][1].get('TestType')
        # set the version from the report file
        settings.setValue('XENA_VERSION', root[0][0][1].get('GeneratedBy'))

        if test_type == 'Throughput':
            results = OrderedDict()
            results[ResultsConstants.THROUGHPUT_RX_FPS] = float(
                root[0][1][0][0].get('PortRxPps')) + float(
                    root[0][1][0][1].get('PortRxPps'))
            results[ResultsConstants.THROUGHPUT_RX_MBPS] = (float(
                root[0][1][0][0].get('PortRxBpsL1')) + float(
                    root[0][1][0][1].get('PortRxBpsL1')))/ 1000000
            results[ResultsConstants.THROUGHPUT_RX_PERCENT] = (
                100 - float(root[0][1][0].get('TotalLossRatioPcnt'))) * float(
                    root[0][1][0].get('TotalTxRatePcnt'))/100
            results[ResultsConstants.TX_RATE_FPS] = root[0][1][0].get(
                'TotalTxRateFps')
            results[ResultsConstants.TX_RATE_MBPS] = float(
                root[0][1][0].get('TotalTxRateBpsL1')) / 1000000
            results[ResultsConstants.TX_RATE_PERCENT] = root[0][1][0].get(
                'TotalTxRatePcnt')
            try:
                results[ResultsConstants.MIN_LATENCY_NS] = float(
                    root[0][1][0][0].get('MinLatency')) * 1000
            except ValueError:
                # Stats for latency returned as N/A so just post them
                results[ResultsConstants.MIN_LATENCY_NS] = root[0][1][0][0].get(
                    'MinLatency')
            try:
                results[ResultsConstants.MAX_LATENCY_NS] = float(
                    root[0][1][0][0].get('MaxLatency')) * 1000
            except ValueError:
                # Stats for latency returned as N/A so just post them
                results[ResultsConstants.MAX_LATENCY_NS] = root[0][1][0][0].get(
                    'MaxLatency')
            try:
                results[ResultsConstants.AVG_LATENCY_NS] = float(
                    root[0][1][0][0].get('AvgLatency')) * 1000
            except ValueError:
                # Stats for latency returned as N/A so just post them
                results[ResultsConstants.AVG_LATENCY_NS] = root[0][1][0][0].get(
                    'AvgLatency')
        elif test_type == 'Back2Back':
            results = OrderedDict()

            # Just mimic what Ixia does and only return the b2b frame count.
            # This may change later once its decided the common results stats
            # to be returned should be.
            results[ResultsConstants.B2B_FRAMES] = root[0][1][0][0].get(
                'TotalTxBurstFrames')
        else:
            raise NotImplementedError('Unknown test type in report file.')

        return results

    def _build_packet_header(self, reverse=False):
        """
        Build a packet header based on traffic profile using scapy external
        libraries.
        :param reverse: Swap source and destination info when building header
        :return: packet header in hex
        """
        srcmac = self._params['traffic']['l2'][
            'srcmac'] if not reverse else self._params['traffic']['l2'][
                'dstmac']
        dstmac = self._params['traffic']['l2'][
            'dstmac'] if not reverse else self._params['traffic']['l2'][
                'srcmac']
        srcip = self._params['traffic']['l3'][
            'srcip'] if not reverse else self._params['traffic']['l3']['dstip']
        dstip = self._params['traffic']['l3'][
            'dstip'] if not reverse else self._params['traffic']['l3']['srcip']
        layer2 = inet.Ether(src=srcmac, dst=dstmac)
        layer3 = inet.IP(src=srcip, dst=dstip,
                         proto=self._params['traffic']['l3']['proto'])
        layer4 = inet.UDP(sport=self._params['traffic']['l4']['srcport'],
                          dport=self._params['traffic']['l4']['dstport'])
        if self._params['traffic']['vlan']['enabled']:
            vlan = inet.Dot1Q(vlan=self._params['traffic']['vlan']['id'],
                              prio=self._params['traffic']['vlan']['priority'],
                              id=self._params['traffic']['vlan']['cfi'])
        else:
            vlan = None
        packet = layer2/vlan/layer3/layer4 if vlan else layer2/layer3/layer4
        packet_bytes = bytes(packet)
        packet_hex = '0x' + binascii.hexlify(packet_bytes).decode('utf-8')
        return packet_hex

    def _create_api_result(self):
        """
        Create result dictionary per trafficgen specifications from socket API
        stats. If stats are not available return values of 0.
        :return: ResultsConstants as dictionary
        """
        # Handle each case of statistics based on if the data is available.
        # This prevents uncaught exceptions when the stats aren't available.
        result_dict = OrderedDict()
        if self.tx_stats.data.get(self.tx_stats.pt_stream_keys[0]):
            result_dict[ResultsConstants.TX_FRAMES] = self.tx_stats.data[
                self.tx_stats.pt_stream_keys[0]]['packets']
            result_dict[ResultsConstants.TX_RATE_FPS] = self.tx_stats.data[
                self.tx_stats.pt_stream_keys[0]]['packets'] / self._duration
            result_dict[ResultsConstants.TX_RATE_MBPS] = ((
                self.tx_stats.data[self.tx_stats.pt_stream_keys[0]]['bytes']
                * 8) / 1000000) / self._duration
            result_dict[ResultsConstants.TX_BYTES] = self.tx_stats.data[
                self.tx_stats.pt_stream_keys[0]]['bytes']
            # tx rate percent may need to be halved if bi directional
            result_dict[ResultsConstants.TX_RATE_PERCENT] = line_percentage(
                self.xmanager.ports[0], self.tx_stats, self._duration,
                self._params['traffic']['l2']['framesize']) if \
                self._params['traffic']['bidir'] == 'False' else\
                line_percentage(
                    self.xmanager.ports[0], self.tx_stats, self._duration,
                    self._params['traffic']['l2']['framesize']) / 2
        else:
            self._logger.error('Transmit stats not available.')
            result_dict[ResultsConstants.TX_FRAMES] = 0
            result_dict[ResultsConstants.TX_RATE_FPS] = 0
            result_dict[ResultsConstants.TX_RATE_MBPS] = 0
            result_dict[ResultsConstants.TX_BYTES] = 0
            result_dict[ResultsConstants.TX_RATE_PERCENT] = 0

        if self.rx_stats.data.get('pr_tpldstraffic'):
            result_dict[ResultsConstants.RX_FRAMES] = self.rx_stats.data[
                'pr_tpldstraffic']['0']['packets']
            result_dict[
                ResultsConstants.THROUGHPUT_RX_FPS] = self.rx_stats.data[
                    'pr_tpldstraffic']['0']['packets'] / self._duration
            result_dict[
                ResultsConstants.THROUGHPUT_RX_MBPS] = ((
                    self.rx_stats.data['pr_tpldstraffic']['0']['bytes']
                    *8) / 1000000) / self._duration
            result_dict[ResultsConstants.RX_BYTES] = self.rx_stats.data[
                'pr_tpldstraffic']['0']['bytes']
            # throughput percent may need to be halved if bi directional
            result_dict[
                ResultsConstants.THROUGHPUT_RX_PERCENT] = line_percentage(
                    self.xmanager.ports[1], self.rx_stats, self._duration,
                    self._params['traffic']['l2']['framesize']) if \
                self._params['traffic']['bidir'] == 'False' else \
                line_percentage(
                    self.xmanager.ports[1], self.rx_stats, self._duration,
                    self._params['traffic']['l2']['framesize']) / 2

        else:
            self._logger.error('Receive stats not available.')
            result_dict[ResultsConstants.RX_FRAMES] = 0
            result_dict[ResultsConstants.THROUGHPUT_RX_FPS] = 0
            result_dict[ResultsConstants.THROUGHPUT_RX_MBPS] = 0
            result_dict[ResultsConstants.RX_BYTES] = 0
            result_dict[ResultsConstants.THROUGHPUT_RX_PERCENT] = 0

        if self.rx_stats.data.get('pr_tplderrors'):
            result_dict[ResultsConstants.PAYLOAD_ERR] = self.rx_stats.data[
                'pr_tplderrors']['0']['pld']
            result_dict[ResultsConstants.SEQ_ERR] = self.rx_stats.data[
                'pr_tplderrors']['0']['seq']
        else:
            result_dict[ResultsConstants.PAYLOAD_ERR] = 0
            result_dict[ResultsConstants.SEQ_ERR] = 0

        if self.rx_stats.data.get('pr_tpldlatency'):
            result_dict[ResultsConstants.MIN_LATENCY_NS] = self.rx_stats.data[
                'pr_tpldlatency']['0']['min']
            result_dict[ResultsConstants.MAX_LATENCY_NS] = self.rx_stats.data[
                'pr_tpldlatency']['0']['max']
            result_dict[ResultsConstants.AVG_LATENCY_NS] = self.rx_stats.data[
                'pr_tpldlatency']['0']['avg']
        else:
            result_dict[ResultsConstants.MIN_LATENCY_NS] = 0
            result_dict[ResultsConstants.MAX_LATENCY_NS] = 0
            result_dict[ResultsConstants.AVG_LATENCY_NS] = 0

        return result_dict

    def _setup_json_config(self, tests, loss_rate, testtype=None,
                           bonding_test=False):
        """
        Create a 2bUsed json file that will be used for xena2544.exe execution.
        :param tests: Number of tests
        :param loss_rate: The acceptable loss rate as float
        :param testtype: Either '2544_b2b' or '2544_throughput' as string
        :param bonding_test: Specify if the test is a bonding test which will
        enable the pairs topology
        :return: None
        """
        try:
            # set duplex mode, this code is valid, pylint complaining with a
            # warning that many have complained about online.
            # pylint: disable=redefined-variable-type
            if self._params['traffic']['bidir'] == "True":
                j_file = XenaJSONMesh()
            elif self._params['traffic']['bidir'] == "False":
                j_file = XenaJSONBlocks()
            elif bonding_test:
                j_file = XenaJSONPairs()

            j_file.set_chassis_info(
                settings.getValue('TRAFFICGEN_XENA_IP'),
                settings.getValue('TRAFFICGEN_XENA_PASSWORD')
            )
            j_file.set_port(0, settings.getValue('TRAFFICGEN_XENA_MODULE1'),
                            settings.getValue('TRAFFICGEN_XENA_PORT1'))
            j_file.set_port(1, settings.getValue('TRAFFICGEN_XENA_MODULE2'),
                            settings.getValue('TRAFFICGEN_XENA_PORT2'))
            j_file.set_port_ip_v4(
                0, settings.getValue("TRAFFICGEN_XENA_PORT0_IP"),
                settings.getValue("TRAFFICGEN_XENA_PORT0_CIDR"),
                settings.getValue("TRAFFICGEN_XENA_PORT0_GATEWAY"))
            j_file.set_port_ip_v4(
                1, settings.getValue("TRAFFICGEN_XENA_PORT1_IP"),
                settings.getValue("TRAFFICGEN_XENA_PORT1_CIDR"),
                settings.getValue("TRAFFICGEN_XENA_PORT1_GATEWAY"))

            if testtype == '2544_throughput':
                j_file.set_test_options_tput(
                    packet_sizes=self._params['traffic']['l2']['framesize'],
                    iterations=tests, loss_rate=loss_rate,
                    duration=self._duration, micro_tpld=True if self._params[
                        'traffic']['l2']['framesize'] == 64 else False)
                j_file.enable_throughput_test()
                j_file.modify_2544_tput_options(
                    settings.getValue('TRAFFICGEN_XENA_2544_TPUT_INIT_VALUE'),
                    settings.getValue('TRAFFICGEN_XENA_2544_TPUT_MIN_VALUE'),
                    settings.getValue('TRAFFICGEN_XENA_2544_TPUT_MAX_VALUE'),
                    settings.getValue(
                        'TRAFFICGEN_XENA_2544_TPUT_VALUE_RESOLUTION'),
                    settings.getValue(
                        'TRAFFICGEN_XENA_2544_TPUT_USEPASS_THRESHHOLD'),
                    settings.getValue(
                        'TRAFFICGEN_XENA_2544_TPUT_PASS_THRESHHOLD')
                )

            elif testtype == '2544_b2b':
                j_file.set_test_options_back2back(
                    packet_sizes=self._params['traffic']['l2']['framesize'],
                    iterations=tests, duration=self._duration,
                    startvalue=self._params['traffic']['frame_rate'],
                    endvalue=self._params['traffic']['frame_rate'],
                    micro_tpld=True if self._params[
                        'traffic']['l2']['framesize'] == 64 else False)
                j_file.enable_back2back_test()

            j_file.set_header_layer2(
                dst_mac=self._params['traffic']['l2']['dstmac'],
                src_mac=self._params['traffic']['l2']['srcmac'])
            j_file.set_header_layer3(
                src_ip=self._params['traffic']['l3']['srcip'],
                dst_ip=self._params['traffic']['l3']['dstip'],
                protocol=self._params['traffic']['l3']['proto'])
            j_file.set_header_layer4_udp(
                source_port=self._params['traffic']['l4']['srcport'],
                destination_port=self._params['traffic']['l4']['dstport'])
            if self._params['traffic']['vlan']['enabled']:
                j_file.set_header_vlan(
                    vlan_id=self._params['traffic']['vlan']['id'],
                    id=self._params['traffic']['vlan']['cfi'],
                    prio=self._params['traffic']['vlan']['priority'])
            j_file.add_header_segments(
                flows=self._params['traffic']['multistream'],
                multistream_layer=self._params['traffic']['stream_type'])

            j_file.write_config(os.path.join(
                _CURR_DIR, 'profiles/2bUsed.x2544'))
        except Exception as exc:
            self._logger.exception("Error during Xena JSON setup: %s", exc)
            raise

    def _start_traffic_api(self, packet_limit):
        """
        Start the Xena traffic using the socket API driver
        :param packet_limit: packet limit for stream, set to -1 for no limit
        :return: None
        """
        if not self.xmanager:
            self._xsocket = XenaSocketDriver(
                settings.getValue('TRAFFICGEN_XENA_IP'))
            self.xmanager = XenaManager(
                self._xsocket, settings.getValue('TRAFFICGEN_XENA_USER'),
                settings.getValue('TRAFFICGEN_XENA_PASSWORD'))

        # for the report file version info ask the chassis directly for its
        # software versions
        settings.setValue('XENA_VERSION', 'XENA Socket API - {}'.format(
            self.xmanager.get_version()))

        if not self.xmanager.ports:
            self.xmanager.ports[0] = self.xmanager.add_module_port(
                settings.getValue('TRAFFICGEN_XENA_MODULE1'),
                settings.getValue('TRAFFICGEN_XENA_PORT1'))
            if not self.xmanager.ports[0].reserve_port():
                self._logger.error(
                    'Unable to reserve port 0. Please release Xena Port')

        if len(self.xmanager.ports) < 2:
            self.xmanager.ports[1] = self.xmanager.add_module_port(
                settings.getValue('TRAFFICGEN_XENA_MODULE2'),
                settings.getValue('TRAFFICGEN_XENA_PORT2'))
            if not self.xmanager.ports[1].reserve_port():
                self._logger.error(
                    'Unable to reserve port 1. Please release Xena Port')

        # Clear port configuration for a clean start
        self.xmanager.ports[0].reset_port()
        self.xmanager.ports[1].reset_port()
        if settings.getValue('TRAFFICGEN_XENA_CONT_PORT_LEARNING_ENABLED'):
            # turn on port learning
            self.xmanager.ports[0].set_port_learning(1)
            self.xmanager.ports[1].set_port_learning(1)
            sleep(settings.getValue('TRAFFICGEN_XENA_CONT_PORT_LEARNING_DURATION'))
            # turn off port learning
            self.xmanager.ports[0].set_port_learning(0)
            self.xmanager.ports[1].set_port_learning(0)
            sleep(1)
        self.xmanager.ports[0].clear_stats()
        self.xmanager.ports[1].clear_stats()

        # set the port IP from the conf file
        self.xmanager.ports[0].set_port_ip(
            settings.getValue('TRAFFICGEN_XENA_PORT0_IP'),
            settings.getValue('TRAFFICGEN_XENA_PORT0_CIDR'),
            settings.getValue('TRAFFICGEN_XENA_PORT0_GATEWAY'))
        self.xmanager.ports[1].set_port_ip(
            settings.getValue('TRAFFICGEN_XENA_PORT1_IP'),
            settings.getValue('TRAFFICGEN_XENA_PORT1_CIDR'),
            settings.getValue('TRAFFICGEN_XENA_PORT1_GATEWAY'))
        self.xmanager.ports[0].set_port_time_limit(self._duration)
        self.xmanager.ports[1].set_port_time_limit(self._duration)

        def setup_stream(stream, port, payload_id, flip_addr=False):
            """
            Helper function to configure streams.
            :param stream: Stream object from XenaDriver module
            :param port: Port object from XenaDriver module
            :param payload_id: payload ID as int
            :param flip_addr: Boolean if the source and destination addresses
            should be flipped.
            :return: None
            """
            stream.set_on()
            if packet_limit != -1:
                stream.set_packet_limit(packet_limit)

            port.set_port_arp_reply(is_on=True)
            port.set_port_arp_reply(is_on=True, ipv6=True)
            port.set_port_ping_reply(is_on=True)
            port.set_port_ping_reply(is_on=True, ipv6=True)

            stream.set_rate_fraction(int(
                10000 * self._params['traffic']['frame_rate']))
            stream.set_packet_header(self._build_packet_header(
                reverse=flip_addr))
            stream.set_header_protocol(
                'ETHERNET VLAN IP UDP' if self._params['traffic']['vlan'][
                    'enabled'] else 'ETHERNET IP UDP')
            stream.set_packet_length(
                'fixed', self._params['traffic']['l2']['framesize'],
                self._params['traffic']['l2']['framesize'])
            stream.set_packet_payload('incrementing', '0x00')
            stream.set_payload_id(payload_id)
            port.set_port_time_limit(self._duration * 1000000)

            if self._params['traffic']['l2']['framesize'] == 64:
                # set micro tpld
                port.micro_tpld_enable()

            if self._params['traffic']['multistream']:
                stream.enable_multistream(
                    flows=self._params['traffic']['multistream'],
                    layer=self._params['traffic']['stream_type'])

        s1_p0 = self.xmanager.ports[0].add_stream()
        setup_stream(s1_p0, self.xmanager.ports[0], 0)

        if self._params['traffic']['bidir'] == 'True':
            s1_p1 = self.xmanager.ports[1].add_stream()
            setup_stream(s1_p1, self.xmanager.ports[1], 1, flip_addr=True)

        if not self.xmanager.ports[0].traffic_on():
            self._logger.error(
                "Failure to start port 0. Check settings and retry.")
        if self._params['traffic']['bidir'] == 'True':
            if not self.xmanager.ports[1].traffic_on():
                self._logger.error(
                    "Failure to start port 1. Check settings and retry.")
        sleep(self._duration + 5) # the extra 5 seconds is to allow packets in flight to complete
        # getting results
        if self._params['traffic']['bidir'] == 'True':
            # need to aggregate out both ports stats and assign that data
            self.rx_stats = self.xmanager.ports[1].get_rx_stats()
            self.tx_stats = self.xmanager.ports[0].get_tx_stats()
            self.tx_stats.data = aggregate_stats(
                self.tx_stats.data,
                self.xmanager.ports[1].get_tx_stats().data)
            self.rx_stats.data = aggregate_stats(
                self.rx_stats.data,
                self.xmanager.ports[0].get_rx_stats().data)
        else:
            # no need to aggregate, just grab the appropriate port stats
            self.tx_stats = self.xmanager.ports[0].get_tx_stats()
            self.rx_stats = self.xmanager.ports[1].get_rx_stats()
        sleep(1)

    def _start_xena_2544(self):
        """
        Start the xena2544 exe.
        :return: None
        """
        args = ["mono", os.path.join(_CURR_DIR, "Xena2544.exe"), "-c",
                os.path.join(_CURR_DIR, "profiles/2bUsed.x2544"), "-e", "-r",
                _CURR_DIR, "-u",
                settings.getValue('TRAFFICGEN_XENA_USER')]
        # Sometimes Xena2544.exe completes, but mono holds the process without
        # releasing it, this can cause a deadlock of the main thread. Use the
        # xena log file as a way to detect this.
        self._log_handle = open(self._log_path, 'r')
        # read the contents of the log before we start so the next read in the
        # wait method are only looking at the text from this test instance
        self._log_handle.read()
        self.mono_pipe = subprocess.Popen(args, stdout=sys.stdout)

    def _wait_xena_2544_complete(self):
        """
        Wait for Xena2544.exe completion.
        :return: None
        """
        data = ''
        while True:
            try:
                self.mono_pipe.wait(60)
                self._log_handle.close()
                break
            except subprocess.TimeoutExpired:
                # check the log to see if Xena2544 has completed and mono is
                # deadlocked.
                data += self._log_handle.read()
                if 'TestCompletedSuccessfully' in data:
                    self._log_handle.close()
                    self.mono_pipe.terminate()
                    break

    def _stop_api_traffic(self):
        """
        Stop traffic through the socket API
        :return: Return results from _create_api_result method
        """
        self.xmanager.ports[0].traffic_off()
        if self._params['traffic']['bidir'] == 'True':
            self.xmanager.ports[1].traffic_off()
        sleep(5)

        stat = self._create_api_result()
        self.disconnect()
        return stat

    def connect(self):
        self._logger.debug('Connect')
        return self

    def disconnect(self):
        """Disconnect from the traffic generator.

        As with :func:`connect`, this function is optional.


        Where implemented, this function should raise an exception on
        failure.

        :returns: None
        """
        self._logger.debug('disconnect')
        if self.xmanager:
            self.xmanager.disconnect()
            self.xmanager = None

        if self._xsocket:
            self._xsocket.disconnect()
            self._xsocket = None

    def send_burst_traffic(self, traffic=None, numpkts=100, duration=20):
        """Send a burst of traffic.

        See ITrafficGenerator for description
        """
        self._duration = duration
        self._params.clear()
        self._params['traffic'] = self.traffic_defaults.copy()
        if traffic:
            self._params['traffic'] = merge_spec(self._params['traffic'],
                                                 traffic)
        self._start_traffic_api(numpkts)
        return self._stop_api_traffic()

    def send_cont_traffic(self, traffic=None, duration=20):
        """Send a continuous flow of traffic.

        See ITrafficGenerator for description
        """
        self._duration = duration

        self._params.clear()
        self._params['traffic'] = self.traffic_defaults.copy()
        if traffic:
            self._params['traffic'] = merge_spec(self._params['traffic'],
                                                 traffic)
        self._start_traffic_api(-1)
        return self._stop_api_traffic()

    def start_cont_traffic(self, traffic=None, duration=20):
        """Non-blocking version of 'send_cont_traffic'.

        See ITrafficGenerator for description
        """
        self._duration = duration

        self._params.clear()
        self._params['traffic'] = self.traffic_defaults.copy()
        if traffic:
            self._params['traffic'] = merge_spec(self._params['traffic'],
                                                 traffic)
        self._start_traffic_api(-1)

    def stop_cont_traffic(self):
        """Stop continuous transmission and return results.
        """
        return self._stop_api_traffic()

    def send_rfc2544_throughput(self, traffic=None, tests=1, duration=20,
                                lossrate=0.0):
        """Send traffic per RFC2544 throughput test specifications.

        See ITrafficGenerator for description
        """
        self._duration = duration

        self._params.clear()
        self._params['traffic'] = self.traffic_defaults.copy()
        if traffic:
            self._params['traffic'] = merge_spec(self._params['traffic'],
                                                 traffic)
        self._setup_json_config(tests, lossrate, '2544_throughput')
        self._start_xena_2544()
        self._wait_xena_2544_complete()

        root = ET.parse(os.path.join(_CURR_DIR, "xena2544-report.xml")).getroot()

        if settings.getValue('TRAFFICGEN_XENA_RFC2544_VERIFY'):
            # record the previous settings so we can revert to them if needed to
            # run the binary search again if the verify fails.
            old_tests = tests
            old_duration = self._duration
            old_min = settings.getValue('TRAFFICGEN_XENA_2544_TPUT_MIN_VALUE')

            for attempt in range(
                    1, settings.getValue(
                        'TRAFFICGEN_XENA_RFC2544_MAXIMUM_VERIFY_ATTEMPTS')+1):
                self._logger.info('Running verify attempt %s', attempt)
                # get the last pass tx rate from the binary search
                pass_rate = float(root[0][1][0].get('TotalTxRatePcnt'))
                # run a one pass rfc2544 with the pass rate to see if it passes
                # the verify duration
                settings.setValue(
                    'TRAFFICGEN_XENA_2544_TPUT_INIT_VALUE', pass_rate)
                settings.setValue(
                    'TRAFFICGEN_XENA_2544_TPUT_MIN_VALUE', pass_rate)
                settings.setValue(
                    'TRAFFICGEN_XENA_2544_TPUT_MAX_VALUE', pass_rate)
                self.start_rfc2544_throughput(
                    traffic, 1, settings.getValue(
                        'TRAFFICGEN_XENA_RFC2544_VERIFY_DURATION'), lossrate)
                self.wait_rfc2544_throughput()
                root = ET.parse(
                    os.path.join(_CURR_DIR, "xena2544-report.xml")).getroot()

                # If it passed, report the number of lost frames and exit the
                # loop
                if root[0][1][0].get('TestState') == "PASS":
                    self._logger.info('Verify passed, packets lost = %s',
                                      root[0][1][0].get('TotalLossFrames'))
                    break
                elif attempt < settings.getValue(
                        'TRAFFICGEN_XENA_RFC2544_MAXIMUM_VERIFY_ATTEMPTS'):
                    self._logger.info(
                        'Verify failed, resuming binary search, packets lost = %s',
                        root[0][1][0].get('TotalLossFrames'))
                    settings.setValue(
                        'TRAFFICGEN_XENA_2544_TPUT_MAX_VALUE',
                        pass_rate - float(settings.getValue(
                            'TRAFFICGEN_XENA_2544_TPUT_VALUE_RESOLUTION')))
                    if settings.getValue(
                            'TRAFFICGEN_XENA_RFC2544_BINARY_RESTART_SMART_SEARCH'):
                        settings.setValue(
                            'TRAFFICGEN_XENA_2544_TPUT_INIT_VALUE',
                            (pass_rate - float(old_min)) / 2)
                    else:
                        settings.setValue(
                            'TRAFFICGEN_XENA_2544_TPUT_INIT_VALUE',
                            pass_rate - float(settings.getValue(
                                'TRAFFICGEN_XENA_2544_TPUT_VALUE_RESOLUTION')))
                    settings.setValue(
                        'TRAFFICGEN_XENA_2544_TPUT_MIN_VALUE', old_min)
                    self._logger.debug(
                        'RFC2544 Initial rate: %s',
                        settings.getValue('TRAFFICGEN_XENA_2544_TPUT_INIT_VALUE'))
                    self._logger.debug(
                        'RFC2544 Maximum rate: %s',
                        settings.getValue('TRAFFICGEN_XENA_2544_TPUT_MAX_VALUE'))
                    self._logger.debug(
                        'RFC2544 Minimum rate: %s',
                        settings.getValue('TRAFFICGEN_XENA_2544_TPUT_MIN_VALUE'))
                    self._duration = old_duration
                    self.start_rfc2544_throughput(
                        traffic, old_tests, self._duration, lossrate)
                    self.wait_rfc2544_throughput()
                    root = ET.parse(
                        os.path.join(_CURR_DIR, "xena2544-report.xml")).getroot()
                else:
                    self._logger.error(
                        'Maximum number of verify attempts reached. Reporting last result')

        return Xena._create_throughput_result(root)

    def start_rfc2544_throughput(self, traffic=None, tests=1, duration=20,
                                 lossrate=0.0):
        """Non-blocking version of 'send_rfc2544_throughput'.

        See ITrafficGenerator for description
        """
        self._duration = duration
        self._params.clear()
        self._params['traffic'] = self.traffic_defaults.copy()
        if traffic:
            self._params['traffic'] = merge_spec(self._params['traffic'],
                                                 traffic)
        self._setup_json_config(tests, lossrate, '2544_throughput')
        self._start_xena_2544()

    def wait_rfc2544_throughput(self):
        """Wait for and return results of RFC2544 test.

        See ITrafficGenerator for description
        """
        self._wait_xena_2544_complete()
        root = ET.parse(os.path.join(_CURR_DIR, "xena2544-report.xml")).getroot()
        return Xena._create_throughput_result(root)

    def send_rfc2544_back2back(self, traffic=None, tests=1, duration=20,
                               lossrate=0.0):
        """Send traffic per RFC2544 back2back test specifications.

        See ITrafficGenerator for description
        """
        self._duration = duration

        self._params.clear()
        self._params['traffic'] = self.traffic_defaults.copy()
        if traffic:
            self._params['traffic'] = merge_spec(self._params['traffic'],
                                                 traffic)
        self._setup_json_config(tests, lossrate, '2544_b2b')
        self._start_xena_2544()
        self._wait_xena_2544_complete()
        root = ET.parse(os.path.join(_CURR_DIR, "xena2544-report.xml")).getroot()
        return Xena._create_throughput_result(root)

    def start_rfc2544_back2back(self, traffic=None, tests=1, duration=20,
                                lossrate=0.0):
        """Non-blocking version of 'send_rfc2544_back2back'.

        See ITrafficGenerator for description
        """
        self._duration = duration
        self._params.clear()
        self._params['traffic'] = self.traffic_defaults.copy()
        if traffic:
            self._params['traffic'] = merge_spec(self._params['traffic'],
                                                 traffic)
        self._setup_json_config(tests, lossrate, '2544_b2b')
        self._start_xena_2544()

    def wait_rfc2544_back2back(self):
        """Wait and set results of RFC2544 test.
        """
        self._wait_xena_2544_complete()
        root = ET.parse(os.path.join(_CURR_DIR, "xena2544-report.xml")).getroot()
        return Xena._create_throughput_result(root)


if __name__ == "__main__":
    pass
