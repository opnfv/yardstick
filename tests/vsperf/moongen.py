# Copyright 2016 Red Hat Inc
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
#   Bill Michalowski, Red Hat Inc.
#   Andrew Theurer, Red Hat Inc.
"""
Moongen Traffic Generator Model
"""

# python imports
from collections import OrderedDict
import logging
import math
import re
import subprocess

# VSPerf imports
from conf import settings
from conf import merge_spec
from core.results.results_constants import ResultsConstants
from tools.pkt_gen.trafficgen.trafficgen import ITrafficGenerator

class Moongen(ITrafficGenerator):
    """Moongen Traffic generator wrapper."""
    _logger = logging.getLogger(__name__)

    def __init__(self):
        """Moongen class constructor."""
        super().__init__()
        self._logger.info("In moongen __init__ method")
        self._params = {}
        self._moongen_host_ip_addr = (
            settings.getValue('TRAFFICGEN_MOONGEN_HOST_IP_ADDR'))
        self._moongen_base_dir = (
            settings.getValue('TRAFFICGEN_MOONGEN_BASE_DIR'))
        self._moongen_user = settings.getValue('TRAFFICGEN_MOONGEN_USER')
        self._moongen_ports = settings.getValue('TRAFFICGEN_MOONGEN_PORTS')

        if settings.getValue('TRAFFICGEN_MOONGEN_LINE_SPEED_GBPS') == '10':
            self._moongen_line_speed = math.pow(10, 10)
        else:
            raise RuntimeError(
                'MOONGEN: Invalid line speed in configuration ' + \
                'file (today 10Gbps supported)')

    def create_moongen_cfg_file(self, traffic, duration=60,
                                acceptable_loss_pct=1, one_shot=0):
        """Create the Moongen configuration file from VSPERF's traffic profile
        :param traffic: Detailed "traffic" spec, i.e. IP address, VLAN tags
        :param duration: The length of time to generate packet throughput
        :param acceptable_loss: Maximum packet loss acceptable
        :param one_shot: No RFC 2544 binary search,
                        just packet flow at traffic specifics
        """
        logging.debug("traffic['frame_rate'] = " + \
            str(traffic['frame_rate']))

        logging.debug("traffic['multistream'] = " + \
            str(traffic['multistream']))

        logging.debug("traffic['stream_type'] = " + \
            str(traffic['stream_type']))

        logging.debug("traffic['l2']['srcmac'] = " + \
            str(traffic['l2']['srcmac']))

        logging.debug("traffic['l2']['dstmac'] = " + \
            str(traffic['l2']['dstmac']))

        logging.debug("traffic['l3']['proto'] = " + \
            str(traffic['l3']['proto']))

        logging.debug("traffic['l3']['srcip'] = " + \
            str(traffic['l3']['srcip']))

        logging.debug("traffic['l3']['dstip'] = " + \
            str(traffic['l3']['dstip']))

        logging.debug("traffic['l4']['srcport'] = " + \
            str(traffic['l4']['srcport']))

        logging.debug("traffic['l4']['dstport'] = " + \
            str(traffic['l4']['dstport']))

        logging.debug("traffic['vlan']['enabled'] = " + \
            str(traffic['vlan']['enabled']))

        logging.debug("traffic['vlan']['id'] = " + \
            str(traffic['vlan']['id']))

        logging.debug("traffic['vlan']['priority'] = " + \
            str(traffic['vlan']['priority']))

        logging.debug("traffic['vlan']['cfi'] = " + \
            str(traffic['vlan']['cfi']))

        logging.debug(traffic['l2']['framesize'])

        out_file = open("opnfv-vsperf-cfg.lua", "wt")

        out_file.write("VSPERF {\n")

        out_file.write("testType = \"throughput\",\n")

        out_file.write("runBidirec = " + \
            traffic['bidir'].lower() + ",\n")

        out_file.write("nrFlows = " + \
            str(traffic['multistream']) + ",\n")

        out_file.write("frameSize = " + \
            str(traffic['l2']['framesize']) + ",\n")

        out_file.write("srcMacs = " + \
            str(traffic['l2']['srcmac']) + ",\n")

        out_file.write("dstMacs = " + \
            str(traffic['l2']['dstmac']) + ",\n")

        out_file.write("srcIp = \"" + \
            str(traffic['l3']['srcip']) + "\",\n")

        out_file.write("dstIp = \"" + \
            str(traffic['l3']['dstip']) + "\",\n")

        if traffic['vlan']['enabled']:
            out_file.write("vlanIds = " + \
                str(traffic['vlan']['id']) + ",\n")

        out_file.write("searchRunTime = " + \
            str(duration) + ",\n")

        out_file.write("validationRunTime = " + \
            str(duration) + ",\n")

        out_file.write("acceptableLossPct = " + \
            str(acceptable_loss_pct) + ",\n")

        out_file.write("ports = " +\
            str(self._moongen_ports) +  ",\n")

        if one_shot:
            out_file.write("oneShot = true,\n")

        # Need to convert VSPERF frame_rate (percentage of line rate)
        # to Mpps for Moongen
        start_rate = str(
            (traffic['frame_rate'] / 100) * (self._moongen_line_speed / \
            (8 * (traffic['l2']['framesize'] + 20)) / math.pow(10, 6)))

        logging.debug("startRate = " + start_rate)

        out_file.write("startRate = " + \
            start_rate + "\n")

        out_file.write("}" + "\n")
        out_file.close()

        copy_moongen_cfg = "scp opnfv-vsperf-cfg.lua " + \
                            self._moongen_user + "@" + \
                            self._moongen_host_ip_addr + ":" + \
                            self._moongen_base_dir + \
                            "/. && rm opnfv-vsperf-cfg.lua"

        find_moongen = subprocess.Popen(copy_moongen_cfg,
                                        shell=True,
                                        stderr=subprocess.PIPE)

        output, error = find_moongen.communicate()

        if error:
            logging.error(output)
            logging.error(error)
            raise RuntimeError('MOONGEN: Error copying configuration file')

    def connect(self):
        """Connect to Moongen traffic generator

        Verify that Moongen is on the system indicated by
        the configuration file
        """
        self._logger.info("MOONGEN:  In Moongen connect method...")

        if self._moongen_host_ip_addr:
            cmd_ping = "ping -c1 " + self._moongen_host_ip_addr
        else:
            raise RuntimeError('MOONGEN: Moongen host not defined')

        ping = subprocess.Popen(cmd_ping, shell=True, stderr=subprocess.PIPE)
        output, error = ping.communicate()

        if ping.returncode:
            self._logger.error(error)
            self._logger.error(output)
            raise RuntimeError('MOONGEN: Cannot ping Moongen host at ' + \
                               self._moongen_host_ip_addr)

        connect_moongen = "ssh " + self._moongen_user + \
                          "@" + self._moongen_host_ip_addr

        cmd_find_moongen = connect_moongen + " ls " + \
                           self._moongen_base_dir + "/trafficgen.lua"

        find_moongen = subprocess.Popen(cmd_find_moongen,
                                        shell=True,
                                        stderr=subprocess.PIPE)

        output, error = find_moongen.communicate()

        if find_moongen.returncode:
            self._logger.error(error)
            self._logger.error(output)
            raise RuntimeError(
                'MOONGEN: Cannot locate Moongen program at %s within %s' \
                % (self._moongen_host_ip_addr, self._moongen_base_dir))

        self._logger.info("MOONGEN: Moongen host successfully found...")

    def disconnect(self):
        """Disconnect from the traffic generator.

        As with :func:`connect`, this function is optional.

        Where implemented, this function should raise an exception on
        failure.

        :returns: None
        """
        self._logger.info("MOONGEN: In moongen disconnect method")

    def send_burst_traffic(self, traffic=None, numpkts=100, duration=20):
        """Send a burst of traffic.

        Send a ``numpkts`` packets of traffic, using ``traffic``
        configuration, with a timeout of ``time``.

        :param traffic: Detailed "traffic" spec, i.e. IP address, VLAN tags
        :param numpkts: Number of packets to send
        :param duration: Time to wait to receive packets

        :returns: dictionary of strings with following data:
            - List of Tx Frames,
            - List of Rx Frames,
            - List of Tx Bytes,
            - List of List of Rx Bytes,
            - Payload Errors and Sequence Errors.
        """
        self._logger.info("In Moongen send_burst_traffic method")
        return NotImplementedError('Moongen Burst traffic not implemented')

    def send_cont_traffic(self, traffic=None, duration=20):
        """Send a continuous flow of traffic

        Send packets at ``frame rate``, using ``traffic`` configuration,
        until timeout ``time`` occurs.

        :param traffic: Detailed "traffic" spec, i.e. IP address, VLAN tags
        :param duration: Time to wait to receive packets (secs)
        :returns: dictionary of strings with following data:
            - Tx Throughput (fps),
            - Rx Throughput (fps),
            - Tx Throughput (mbps),
            - Rx Throughput (mbps),
            - Tx Throughput (% linerate),
            - Rx Throughput (% linerate),
            - Min Latency (ns),
            - Max Latency (ns),
            - Avg Latency (ns)
        """
        self._logger.info("In Moongen send_cont_traffic method")

        self._params.clear()
        self._params['traffic'] = self.traffic_defaults.copy()

        if traffic:
            self._params['traffic'] = merge_spec(self._params['traffic'],
                                                 traffic)

        Moongen.create_moongen_cfg_file(self,
                                        traffic,
                                        duration=duration,
                                        acceptable_loss_pct=100.0,
                                        one_shot=1)

        collected_results = Moongen.run_moongen_and_collect_results(self,
                                                                    test_run=1)

        results = OrderedDict()

        results[ResultsConstants.THROUGHPUT_RX_FPS] = (
            '{:.6f}'.format(
                float(collected_results[ResultsConstants.THROUGHPUT_RX_FPS])))

        results[ResultsConstants.THROUGHPUT_RX_MBPS] = (
            '{:.3f}'.format(
                float(collected_results[ResultsConstants.THROUGHPUT_RX_MBPS])))

        results[ResultsConstants.THROUGHPUT_RX_PERCENT] = (
            '{:.3f}'.format(
                float(
                    collected_results[ResultsConstants.THROUGHPUT_RX_PERCENT])))

        results[ResultsConstants.TX_RATE_FPS] = (
            '{:.3f}'.format(
                float(collected_results[ResultsConstants.TX_RATE_FPS])))

        results[ResultsConstants.TX_RATE_MBPS] = (
            '{:.3f}'.format(
                float(collected_results[ResultsConstants.TX_RATE_MBPS])))

        results[ResultsConstants.TX_RATE_PERCENT] = (
            '{:.3f}'.format(
                float(collected_results[ResultsConstants.TX_RATE_PERCENT])))

        results[ResultsConstants.MIN_LATENCY_NS] = 0

        results[ResultsConstants.MAX_LATENCY_NS] = 0

        results[ResultsConstants.AVG_LATENCY_NS] = 0

        return results

    def start_cont_traffic(self, traffic=None, duration=20):
        """ Non-blocking version of 'send_cont_traffic'.

        Start transmission and immediately return. Do not wait for
        results.
        :param traffic: Detailed "traffic" spec, i.e. IP address, VLAN tags
        :param duration: Time to wait to receive packets (secs)
        """
        self._logger.info("In Moongen start_cont_traffic method")
        return NotImplementedError('moongen continuous traffic not implemented')

    def stop_cont_traffic(self):
        # Stop continuous transmission and return results.
        self._logger.info("In Moongen stop_cont_traffic method")

    def run_moongen_and_collect_results(self, test_run=1):
        """Execute Moongen and transform results into VSPERF format
        :param test_run: The number of tests to run
        """
        # Start Moongen and create logfile of the run
        connect_moongen = "ssh " + self._moongen_user + "@" + \
            self._moongen_host_ip_addr

        cmd_moongen = " 'cd " + self._moongen_base_dir + \
            "; ./MoonGen/build/MoonGen trafficgen.lua | tee moongen_log.txt'"

        cmd_start_moongen = connect_moongen + cmd_moongen

        start_moongen = subprocess.Popen(cmd_start_moongen,
                                         shell=True, stderr=subprocess.PIPE)

        output, error = start_moongen.communicate()

        if start_moongen.returncode:
            logging.debug(error)
            logging.debug(output)
            raise RuntimeError(
                'MOONGEN: Error starting Moongen program at %s within %s' \
                % (self._moongen_host_ip_addr, self._moongen_base_dir))

        cmd_moongen = "mkdir -p /tmp/moongen/" + str(test_run)

        moongen_create_log_dir = subprocess.Popen(cmd_moongen,
                                                  shell=True,
                                                  stderr=subprocess.PIPE)

        output, error = moongen_create_log_dir.communicate()

        if moongen_create_log_dir.returncode:
            logging.debug(error)
            logging.debug(output)
            raise RuntimeError(
                'MOONGEN: Error obtaining Moongen log from %s within %s' \
                % (self._moongen_host_ip_addr, self._moongen_base_dir))

        cmd_moongen = " scp " + self._moongen_user + "@" + \
            self._moongen_host_ip_addr + ":" + \
            self._moongen_base_dir + "/moongen_log.txt /tmp/moongen/" + \
            str(test_run) + "/moongen-run.log"

        copy_moongen_log = subprocess.Popen(cmd_moongen,
                                            shell=True,
                                            stderr=subprocess.PIPE)

        output, error = copy_moongen_log.communicate()

        if copy_moongen_log.returncode:
            logging.debug(error)
            logging.debug(output)
            raise RuntimeError(
                'MOONGEN: Error obtaining Moongen log from %s within %s' \
                % (self._moongen_host_ip_addr, self._moongen_base_dir))

        log_file = "/tmp/moongen/" + str(test_run) + "/moongen-run.log"

        with open(log_file, 'r') as logfile_handle:
            mytext = logfile_handle.read()

             # REPORT results line
             # match.group(1) = Tx frames
             # match.group(2) = Rx frames
             # match.group(3) = Frame loss (count)
             # match.group(4) = Frame loss (percentage)
             # match.group(5) = Tx Mpps
             # match.group(6) = Rx Mpps
            search_pattern = re.compile(
                r'\[REPORT\]\s+total\:\s+'
                r'Tx\s+frames\:\s+(\d+)\s+'
                r'Rx\s+Frames\:\s+(\d+)\s+'
                r'frame\s+loss\:\s+(\d+)\,'
                r'\s+(\d+\.\d+|\d+)%\s+'
                r'Tx\s+Mpps\:\s+(\d+.\d+|\d+)\s+'
                r'Rx\s+Mpps\:\s+(\d+\.\d+|\d+)',
                re.IGNORECASE)

            results_match = search_pattern.search(mytext)

            if not results_match:
                logging.error('There was a problem parsing ' +\
                    'Moongen REPORT section of Moongen log file')

            moongen_results = OrderedDict()
            moongen_results[ResultsConstants.THROUGHPUT_RX_FPS] = 0
            moongen_results[ResultsConstants.THROUGHPUT_RX_MBPS] = 0
            moongen_results[ResultsConstants.THROUGHPUT_RX_PERCENT] = 0
            moongen_results[ResultsConstants.TX_RATE_FPS] = 0
            moongen_results[ResultsConstants.TX_RATE_MBPS] = 0
            moongen_results[ResultsConstants.TX_RATE_PERCENT] = 0
            moongen_results[ResultsConstants.B2B_TX_COUNT] = 0
            moongen_results[ResultsConstants.B2B_FRAMES] = 0
            moongen_results[ResultsConstants.B2B_FRAME_LOSS_FRAMES] = 0
            moongen_results[ResultsConstants.B2B_FRAME_LOSS_PERCENT] = 0

            # find PARAMETERS line
            # parameters_match.group(1) = Frame size

            search_pattern = re.compile(
                r'\[PARAMETERS\]\s+.*frameSize\:\s+(\d+)',
                flags=re.IGNORECASE)
            parameters_match = search_pattern.search(mytext)

            if parameters_match:
                frame_size = int(parameters_match.group(1))
            else:
                logging.error('There was a problem parsing Moongen ' +\
                    'PARAMETERS section of Moongen log file')
                frame_size = 0

            # Each packet stream in the MoonGen report is prefaced with the
            # words '[REPORT]Device'.  Count the instances of this string to
            # get the total aggregrate throughput.  For example:
            #
            # - If num_traffic_streams = 1, there is a single
            #                               unidirectional stream
            #
            # - If num_traffic_streams = 2, there is a bidirectional
            #                               traffic stream
            num_traffic_streams = mytext.count('[REPORT]Device')

        if results_match and parameters_match and num_traffic_streams:
            # Assume for now 10G link speed
            max_theoretical_fps = (
                num_traffic_streams * (self._moongen_line_speed / 8) / (frame_size + 20))

            moongen_results[ResultsConstants.THROUGHPUT_RX_FPS] = (
                float(results_match.group(6)) * 1000000)

            moongen_results[ResultsConstants.THROUGHPUT_RX_MBPS] = (
                float(results_match.group(6)) * (frame_size + 20) * 8)

            moongen_results[ResultsConstants.THROUGHPUT_RX_PERCENT] = (
                (100 * float(results_match.group(6)) * 1000000) / max_theoretical_fps)

            moongen_results[ResultsConstants.TX_RATE_FPS] = (
                float(results_match.group(5)) * 1000000)

            moongen_results[ResultsConstants.TX_RATE_MBPS] = (
                float(results_match.group(5)) * (frame_size + 20) * 8)

            moongen_results[ResultsConstants.TX_RATE_PERCENT] = (
                (100 * float(results_match.group(5)) * 1000000) / max_theoretical_fps)

            moongen_results[ResultsConstants.B2B_TX_COUNT] = (
                float(results_match.group(1)))

            moongen_results[ResultsConstants.B2B_FRAMES] = (
                float(results_match.group(2)))

            moongen_results[ResultsConstants.B2B_FRAME_LOSS_FRAMES] = (
                float(results_match.group(3)))

            moongen_results[ResultsConstants.B2B_FRAME_LOSS_PERCENT] = (
                float(results_match.group(4)))

        return moongen_results

    def send_rfc2544_throughput(self, traffic=None, duration=20,
                                lossrate=0.0, tests=1):
        #
        # Send traffic per RFC2544 throughput test specifications.
        #
        # Send packets at a variable rate, using ``traffic``
        # configuration, until minimum rate at which no packet loss is
        # detected is found.
        #
        # :param traffic: Detailed "traffic" spec, see design docs for details
        # :param tests: Number of tests to execute
        # :param duration: Per iteration duration
        # :param lossrate: Acceptable lossrate percentage
        # :returns: dictionary of strings with following data:
        #     - Tx Throughput (fps),
        #     - Rx Throughput (fps),
        #     - Tx Throughput (mbps),
        #     - Rx Throughput (mbps),
        #     - Tx Throughput (% linerate),
        #     - Rx Throughput (% linerate),
        #     - Min Latency (ns),
        #     - Max Latency (ns),
        #     - Avg Latency (ns)
        #
        self._logger.info("In moongen send_rfc2544_throughput method")
        self._params.clear()
        self._params['traffic'] = self.traffic_defaults.copy()

        if traffic:
            self._params['traffic'] = merge_spec(self._params['traffic'],
                                                 traffic)
        Moongen.create_moongen_cfg_file(self,
                                        traffic,
                                        duration=duration,
                                        acceptable_loss_pct=lossrate)

        # Initialize RFC 2544 throughput specific results
        results = OrderedDict()
        results[ResultsConstants.THROUGHPUT_RX_FPS] = 0
        results[ResultsConstants.THROUGHPUT_RX_MBPS] = 0
        results[ResultsConstants.THROUGHPUT_RX_PERCENT] = 0
        results[ResultsConstants.TX_RATE_FPS] = 0
        results[ResultsConstants.TX_RATE_MBPS] = 0
        results[ResultsConstants.TX_RATE_PERCENT] = 0
        results[ResultsConstants.MIN_LATENCY_NS] = 0
        results[ResultsConstants.MAX_LATENCY_NS] = 0
        results[ResultsConstants.AVG_LATENCY_NS] = 0

        for test_run in range(1, tests+1):
            collected_results = (
                Moongen.run_moongen_and_collect_results(self, test_run=test_run))

            results[ResultsConstants.THROUGHPUT_RX_FPS] += (
                float(collected_results[ResultsConstants.THROUGHPUT_RX_FPS]))

            results[ResultsConstants.THROUGHPUT_RX_MBPS] += (
                float(collected_results[ResultsConstants.THROUGHPUT_RX_MBPS]))

            results[ResultsConstants.THROUGHPUT_RX_PERCENT] += (
                float(collected_results[ResultsConstants.THROUGHPUT_RX_PERCENT]))

            results[ResultsConstants.TX_RATE_FPS] += (
                float(collected_results[ResultsConstants.TX_RATE_FPS]))

            results[ResultsConstants.TX_RATE_MBPS] += (
                float(collected_results[ResultsConstants.TX_RATE_MBPS]))

            results[ResultsConstants.TX_RATE_PERCENT] += (
                float(collected_results[ResultsConstants.TX_RATE_PERCENT]))

        results[ResultsConstants.THROUGHPUT_RX_FPS] = (
            '{:.6f}'.format(results[ResultsConstants.THROUGHPUT_RX_FPS] /
                            tests))

        results[ResultsConstants.THROUGHPUT_RX_MBPS] = (
            '{:.3f}'.format(results[ResultsConstants.THROUGHPUT_RX_MBPS] /
                            tests))

        results[ResultsConstants.THROUGHPUT_RX_PERCENT] = (
            '{:.3f}'.format(results[ResultsConstants.THROUGHPUT_RX_PERCENT] /
                            tests))

        results[ResultsConstants.TX_RATE_FPS] = (
            '{:.6f}'.format(results[ResultsConstants.TX_RATE_FPS] /
                            tests))

        results[ResultsConstants.TX_RATE_MBPS] = (
            '{:.3f}'.format(results[ResultsConstants.TX_RATE_MBPS] /
                            tests))

        results[ResultsConstants.TX_RATE_PERCENT] = (
            '{:.3f}'.format(results[ResultsConstants.TX_RATE_PERCENT] /
                            tests))

        results[ResultsConstants.MIN_LATENCY_NS] = (
            '{:.3f}'.format(results[ResultsConstants.MIN_LATENCY_NS] /
                            tests))

        results[ResultsConstants.MAX_LATENCY_NS] = (
            '{:.3f}'.format(results[ResultsConstants.MAX_LATENCY_NS] /
                            tests))

        results[ResultsConstants.AVG_LATENCY_NS] = (
            '{:.3f}'.format(results[ResultsConstants.AVG_LATENCY_NS] /
                            tests))

        return results

    def start_rfc2544_throughput(self, traffic=None, tests=1, duration=20,
                                 lossrate=0.0):
        """Non-blocking version of 'send_rfc2544_throughput'.

        Start transmission and immediately return. Do not wait for
        results.
        """
        self._logger.info(
            "MOONGEN: In moongen start_rfc2544_throughput method")

    def wait_rfc2544_throughput(self):
        """Wait for and return results of RFC2544 test.
        """
        self._logger.info('In moongen wait_rfc2544_throughput')

    def send_rfc2544_back2back(self, traffic=None, duration=60,
                               lossrate=0.0, tests=1):
        """Send traffic per RFC2544 back2back test specifications.

        Send packets at a fixed rate, using ``traffic``
        configuration, for duration seconds.

        :param traffic: Detailed "traffic" spec, see design docs for details
        :param tests: Number of tests to execute
        :param duration: Per iteration duration
        :param lossrate: Acceptable loss percentage

        :returns: Named tuple of Rx Throughput (fps), Rx Throughput (mbps),
            Tx Rate (% linerate), Rx Rate (% linerate), Tx Count (frames),
            Back to Back Count (frames), Frame Loss (frames), Frame Loss (%)
        :rtype: :class:`Back2BackResult`
        """
        self._logger.info("In moongen send_rfc2544_back2back method")
        self._params.clear()
        self._params['traffic'] = self.traffic_defaults.copy()

        if traffic:
            self._params['traffic'] = merge_spec(self._params['traffic'],
                                                 traffic)

        Moongen.create_moongen_cfg_file(self,
                                        traffic,
                                        duration=duration,
                                        acceptable_loss_pct=lossrate)

        # Initialize RFC 2544 B2B specific results
        results = OrderedDict()
        results[ResultsConstants.B2B_RX_FPS] = 0
        results[ResultsConstants.B2B_TX_FPS] = 0
        results[ResultsConstants.B2B_RX_PERCENT] = 0
        results[ResultsConstants.B2B_TX_PERCENT] = 0
        results[ResultsConstants.B2B_TX_COUNT] = 0
        results[ResultsConstants.B2B_FRAMES] = 0
        results[ResultsConstants.B2B_FRAME_LOSS_FRAMES] = 0
        results[ResultsConstants.B2B_FRAME_LOSS_PERCENT] = 0
        results[ResultsConstants.SCAL_STREAM_COUNT] = 0
        results[ResultsConstants.SCAL_STREAM_TYPE] = 0
        results[ResultsConstants.SCAL_PRE_INSTALLED_FLOWS] = 0

        for test_run in range(1, tests+1):
            collected_results = (
                Moongen.run_moongen_and_collect_results(self, test_run=test_run))

            results[ResultsConstants.B2B_RX_FPS] += (
                float(collected_results[ResultsConstants.THROUGHPUT_RX_FPS]))

            results[ResultsConstants.B2B_RX_PERCENT] += (
                float(collected_results[ResultsConstants.THROUGHPUT_RX_PERCENT]))

            results[ResultsConstants.B2B_TX_FPS] += (
                float(collected_results[ResultsConstants.TX_RATE_FPS]))

            results[ResultsConstants.B2B_TX_PERCENT] += (
                float(collected_results[ResultsConstants.TX_RATE_PERCENT]))

            results[ResultsConstants.B2B_TX_COUNT] += (
                int(collected_results[ResultsConstants.B2B_TX_COUNT]))

            results[ResultsConstants.B2B_FRAMES] += (
                int(collected_results[ResultsConstants.B2B_FRAMES]))

            results[ResultsConstants.B2B_FRAME_LOSS_FRAMES] += (
                int(collected_results[ResultsConstants.B2B_FRAME_LOSS_FRAMES]))

            results[ResultsConstants.B2B_FRAME_LOSS_PERCENT] += (
                int(collected_results[ResultsConstants.B2B_FRAME_LOSS_PERCENT]))

        # Calculate average results
        results[ResultsConstants.B2B_RX_FPS] = (
            results[ResultsConstants.B2B_RX_FPS] / tests)

        results[ResultsConstants.B2B_RX_PERCENT] = (
            results[ResultsConstants.B2B_RX_PERCENT] / tests)

        results[ResultsConstants.B2B_TX_FPS] = (
            results[ResultsConstants.B2B_TX_FPS] / tests)

        results[ResultsConstants.B2B_TX_PERCENT] = (
            results[ResultsConstants.B2B_TX_PERCENT] / tests)

        results[ResultsConstants.B2B_TX_COUNT] = (
            results[ResultsConstants.B2B_TX_COUNT] / tests)

        results[ResultsConstants.B2B_FRAMES] = (
            results[ResultsConstants.B2B_FRAMES] / tests)

        results[ResultsConstants.B2B_FRAME_LOSS_FRAMES] = (
            results[ResultsConstants.B2B_FRAME_LOSS_FRAMES] / tests)

        results[ResultsConstants.B2B_FRAME_LOSS_PERCENT] = (
            results[ResultsConstants.B2B_FRAME_LOSS_PERCENT] / tests)

        results[ResultsConstants.SCAL_STREAM_COUNT] = 0
        results[ResultsConstants.SCAL_STREAM_TYPE] = 0
        results[ResultsConstants.SCAL_PRE_INSTALLED_FLOWS] = 0

        return results

    def start_rfc2544_back2back(self, traffic=None, tests=1, duration=20,
                                lossrate=0.0):
        #
        # Non-blocking version of 'send_rfc2544_back2back'.
        #
        # Start transmission and immediately return. Do not wait for results.
        #
        self._logger.info("In Moongen start_rfc2544_back2back method")
        return NotImplementedError(
            'Moongen start back2back traffic not implemented')

    def wait_rfc2544_back2back(self):
        self._logger.info("In moongen wait_rfc2544_back2back method")
        #
        # Wait and set results of RFC2544 test.
        #
        return NotImplementedError(
            'Moongen wait back2back traffic not implemented')

if __name__ == "__main__":
    pass
