# Copyright 2016 Spirent Communications.
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

"""
Code to integrate Spirent TestCenter with the vsperf test framework.

Provides a model for Spirent TestCenter as a test tool for implementing
various performance tests of a virtual switch.
"""

import csv
import logging
import os
import subprocess

from yardstick.traffic_generator.conf import settings
from yardstick.traffic_generator.core.results.results_constants import ResultsConstants
from yardstick.traffic_generator.tools.pkt_gen import trafficgen


def get_stc_common_settings():
    """
    Return the common Settings
    These settings would apply to almost all the tests.
    """
    args = ["--lab_server_addr",
            settings.getValue("TRAFFICGEN_STC_LAB_SERVER_ADDR"),
            "--license_server_addr",
            settings.getValue("TRAFFICGEN_STC_LICENSE_SERVER_ADDR"),
            "--east_chassis_addr",
            settings.getValue("TRAFFICGEN_STC_EAST_CHASSIS_ADDR"),
            "--east_slot_num",
            settings.getValue("TRAFFICGEN_STC_EAST_SLOT_NUM"),
            "--east_port_num",
            settings.getValue("TRAFFICGEN_STC_EAST_PORT_NUM"),
            "--west_chassis_addr",
            settings.getValue("TRAFFICGEN_STC_WEST_CHASSIS_ADDR"),
            "--west_slot_num",
            settings.getValue("TRAFFICGEN_STC_WEST_SLOT_NUM"),
            "--west_port_num",
            settings.getValue("TRAFFICGEN_STC_WEST_PORT_NUM"),
            "--test_session_name",
            settings.getValue("TRAFFICGEN_STC_TEST_SESSION_NAME"),
            "--results_dir",
            settings.getValue("TRAFFICGEN_STC_RESULTS_DIR"),
            "--csv_results_file_prefix",
            settings.getValue("TRAFFICGEN_STC_CSV_RESULTS_FILE_PREFIX")]
    return args


def get_rfc2544_common_settings():
    """
    Retrun Generic RFC 2544 settings.
    These settings apply to all the 2544 tests
    """
    args = [settings.getValue("TRAFFICGEN_STC_PYTHON2_PATH"),
            os.path.join(
                settings.getValue("TRAFFICGEN_STC_TESTCENTER_PATH"),
                settings.getValue(
                    "TRAFFICGEN_STC_RFC2544_TPUT_TEST_FILE_NAME")),
            "--metric",
            settings.getValue("TRAFFICGEN_STC_RFC2544_METRIC"),
            "--search_mode",
            settings.getValue("TRAFFICGEN_STC_SEARCH_MODE"),
            "--learning_mode",
            settings.getValue("TRAFFICGEN_STC_LEARNING_MODE"),
            "--rate_lower_limit_pct",
            settings.getValue("TRAFFICGEN_STC_RATE_LOWER_LIMIT_PCT"),
            "--rate_upper_limit_pct",
            settings.getValue("TRAFFICGEN_STC_RATE_UPPER_LIMIT_PCT"),
            "--rate_initial_pct",
            settings.getValue("TRAFFICGEN_STC_RATE_INITIAL_PCT"),
            "--rate_step_pct",
            settings.getValue("TRAFFICGEN_STC_RATE_STEP_PCT"),
            "--resolution_pct",
            settings.getValue("TRAFFICGEN_STC_RESOLUTION_PCT"),
            "--acceptable_frame_loss_pct",
            settings.getValue("TRAFFICGEN_STC_ACCEPTABLE_FRAME_LOSS_PCT"),
            "--east_intf_addr",
            settings.getValue("TRAFFICGEN_STC_EAST_INTF_ADDR"),
            "--east_intf_gateway_addr",
            settings.getValue("TRAFFICGEN_STC_EAST_INTF_GATEWAY_ADDR"),
            "--west_intf_addr",
            settings.getValue("TRAFFICGEN_STC_WEST_INTF_ADDR"),
            "--west_intf_gateway_addr",
            settings.getValue("TRAFFICGEN_STC_WEST_INTF_GATEWAY_ADDR"),
            "--trial_duration_sec",
            settings.getValue("TRAFFICGEN_STC_TRIAL_DURATION_SEC"),
            "--traffic_pattern",
            settings.getValue("TRAFFICGEN_STC_TRAFFIC_PATTERN")]
    return args


def get_rfc2544_custom_settings(framesize, custom_tr, tests):
    """
    Return RFC2544 Custom Settings
    """
    args = ["--frame_size_list",
            str(framesize),
            "--traffic_custom",
            str(custom_tr),
            "--num_trials",
            str(tests)]
    return args


def get_rfc2889_common_settings(framesize, tests, metric):
    """
    Return RFC2889 common Settings
    """
    new_metric = metric.replace('rfc2889_', '')
    args = [settings.getValue("TRAFFICGEN_STC_PYTHON2_PATH"),
            os.path.join(
                settings.getValue("TRAFFICGEN_STC_TESTCENTER_PATH"),
                settings.getValue(
                    "TRAFFICGEN_STC_RFC2889_TEST_FILE_NAME")),
            "--lab_server_addr",
            settings.getValue("TRAFFICGEN_STC_LAB_SERVER_ADDR"),
            "--license_server_addr",
            settings.getValue("TRAFFICGEN_STC_LICENSE_SERVER_ADDR"),
            "--location_list",
            settings.getValue("TRAFFICGEN_STC_RFC2889_LOCATIONS"),
            "--test_session_name",
            settings.getValue("TRAFFICGEN_STC_TEST_SESSION_NAME"),
            "--results_dir",
            settings.getValue("TRAFFICGEN_STC_RESULTS_DIR"),
            "--csv_results_file_prefix",
            settings.getValue("TRAFFICGEN_STC_CSV_RESULTS_FILE_PREFIX"),
            "--frame_size_list",
            str(framesize),
            "--metric",
            str(new_metric),
            "--num_trials",
            str(tests)]

    return args


def get_rfc2889_custom_settings():
    """
    Return RFC2889 Custom Settings
    """
    args = ["--min_learning_rate",
            settings.getValue("TRAFFICGEN_STC_RFC2889_MIN_LR"),
            "--max_learning_rate",
            settings.getValue("TRAFFICGEN_STC_RFC2889_MAX_LR"),
            "--min_num_addrs",
            settings.getValue("TRAFFICGEN_STC_RFC2889_MIN_ADDRS"),
            "--max_num_addrs",
            settings.getValue("TRAFFICGEN_STC_RFC2889_MAX_ADDRS"),
            "--ac_learning_rate",
            settings.getValue("TRAFFICGEN_STC_RFC2889_AC_LR")]
    return args


class TestCenter(trafficgen.ITrafficGenerator):
    """
    Spirent TestCenter
    """
    _logger = logging.getLogger(__name__)

    def connect(self):
        """
        Do nothing.
        """
        return self

    def disconnect(self):
        """
        Do nothing.
        """
        pass

    def send_burst_traffic(self, traffic=None, numpkts=100, duration=20):
        """
        Do nothing.
        """
        return None

    def get_rfc2889_addr_learning_results(self, filename):
        """
        Reads the CSV file and return the results
        """
        result = {}
        with open(filename, "r") as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                self._logger.info("Row: %s", row)
                learn_rate = float(row["OptimalLearningRate"])
                result[ResultsConstants.OPTIMAL_LEARNING_RATE_FPS] = learn_rate
        return result

    def get_rfc2889_addr_caching_results(self, filename):
        """
        Reads the CSV file and return the results
        """
        result = {}
        with open(filename, "r") as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                self._logger.info("Row: %s", row)
                caching_cap = float(row["RxFrameCount"])
                learn_per = (100.0 - (float(row["PercentFrameLoss(%)"])))
                result[ResultsConstants.CACHING_CAPACITY_ADDRS] = caching_cap
                result[ResultsConstants.ADDR_LEARNED_PERCENT] = learn_per
        return result

    def get_rfc2889_forwarding_results(self, filename):
        """
        Reads the CSV file and return the results
        """
        result = {}
        with open(filename, "r") as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                self._logger.info("Row: %s", row)
                duration = int((float(row["TxSignatureFrameCount"])) /
                               (float(row["OfferedLoad(fps)"])))
                tx_fps = (float(row["OfferedLoad(fps)"]))
                rx_fps = float((float(row["RxFrameCount"])) /
                               float(duration))
                tx_mbps = ((tx_fps * float(row["FrameSize"])) /
                           (1000000.0))
                rx_mbps = ((rx_fps * float(row["FrameSize"])) /
                           (1000000.0))
                result[ResultsConstants.TX_RATE_FPS] = tx_fps
                result[ResultsConstants.THROUGHPUT_RX_FPS] = rx_fps
                result[ResultsConstants.TX_RATE_MBPS] = tx_mbps
                result[ResultsConstants.THROUGHPUT_RX_MBPS] = rx_mbps
                result[ResultsConstants.TX_RATE_PERCENT] = float(
                    row["OfferedLoad(%)"])
                result[ResultsConstants.FRAME_LOSS_PERCENT] = float(
                    row["PercentFrameLoss(%)"])
                result[ResultsConstants.FORWARDING_RATE_FPS] = float(
                    row["ForwardingRate(fps)"])
        return result

    # pylint: disable=unused-argument
    def send_rfc2889_forwarding(self, traffic=None, tests=1, duration=20):
        """
        Send traffic per RFC2889 Forwarding test specifications.
        """
        framesize = settings.getValue("TRAFFICGEN_STC_FRAME_SIZE")
        if traffic and 'l2' in traffic:
            if 'framesize' in traffic['l2']:
                framesize = traffic['l2']['framesize']
        args = get_rfc2889_common_settings(framesize, tests,
                                           traffic['traffic_type'])
        if settings.getValue("TRAFFICGEN_STC_VERBOSE") is "True":
            args.append("--verbose")
            verbose = True
            self._logger.debug("Arguments used to call test: %s", args)
        subprocess.check_call(args)

        filec = os.path.join(settings.getValue("TRAFFICGEN_STC_RESULTS_DIR"),
                             settings.getValue(
                                 "TRAFFICGEN_STC_CSV_RESULTS_FILE_PREFIX") +
                             ".csv")

        if verbose:
            self._logger.info("file: %s", filec)

        return self.get_rfc2889_forwarding_results(filec)

    def send_rfc2889_caching(self, traffic=None, tests=1, duration=20):
        """
        Send as per RFC2889 Addr-Caching test specifications.
        """
        framesize = settings.getValue("TRAFFICGEN_STC_FRAME_SIZE")
        if traffic and 'l2' in traffic:
            if 'framesize' in traffic['l2']:
                framesize = traffic['l2']['framesize']
        common_args = get_rfc2889_common_settings(framesize, tests,
                                                  traffic['traffic_type'])
        custom_args = get_rfc2889_custom_settings()
        args = common_args + custom_args

        if settings.getValue("TRAFFICGEN_STC_VERBOSE") is "True":
            args.append("--verbose")
            verbose = True
            self._logger.debug("Arguments used to call test: %s", args)
        subprocess.check_call(args)

        filec = os.path.join(settings.getValue("TRAFFICGEN_STC_RESULTS_DIR"),
                             settings.getValue(
                                 "TRAFFICGEN_STC_CSV_RESULTS_FILE_PREFIX") +
                             ".csv")

        if verbose:
            self._logger.info("file: %s", filec)

        return self.get_rfc2889_addr_caching_results(filec)

    def send_rfc2889_learning(self, traffic=None, tests=1, duration=20):
        """
        Send traffic per RFC2889 Addr-Learning test specifications.
        """
        framesize = settings.getValue("TRAFFICGEN_STC_FRAME_SIZE")
        if traffic and 'l2' in traffic:
            if 'framesize' in traffic['l2']:
                framesize = traffic['l2']['framesize']
        common_args = get_rfc2889_common_settings(framesize, tests,
                                                  traffic['traffic_type'])
        custom_args = get_rfc2889_custom_settings()
        args = common_args + custom_args

        if settings.getValue("TRAFFICGEN_STC_VERBOSE") is "True":
            args.append("--verbose")
            verbose = True
            self._logger.debug("Arguments used to call test: %s", args)
        subprocess.check_call(args)

        filec = os.path.join(settings.getValue("TRAFFICGEN_STC_RESULTS_DIR"),
                             settings.getValue(
                                 "TRAFFICGEN_STC_CSV_RESULTS_FILE_PREFIX") +
                             ".csv")

        if verbose:
            self._logger.info("file: %s", filec)

        return self.get_rfc2889_addr_learning_results(filec)

    def get_rfc2544_results(self, filename):
        """
        Reads the CSV file and return the results
        """
        result = {}
        with open(filename, "r") as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                self._logger.info("Row: %s", row)
                tx_fps = ((float(row["TxFrameCount"])) /
                          (float(row["Duration(sec)"])))
                rx_fps = ((float(row["RxFrameCount"])) /
                          (float(row["Duration(sec)"])))
                tx_mbps = ((float(row["TxFrameCount"]) *
                            float(row["ConfiguredFrameSize"])) /
                           (float(row["Duration(sec)"]) * 1000000.0))
                rx_mbps = ((float(row["RxFrameCount"]) *
                            float(row["ConfiguredFrameSize"])) /
                           (float(row["Duration(sec)"]) * 1000000.0))
                result[ResultsConstants.TX_RATE_FPS] = tx_fps
                result[ResultsConstants.THROUGHPUT_RX_FPS] = rx_fps
                result[ResultsConstants.TX_RATE_MBPS] = tx_mbps
                result[ResultsConstants.THROUGHPUT_RX_MBPS] = rx_mbps
                result[ResultsConstants.TX_RATE_PERCENT] = float(
                    row["OfferedLoad(%)"])
                result[ResultsConstants.THROUGHPUT_RX_PERCENT] = float(
                    row["Throughput(%)"])
                result[ResultsConstants.MIN_LATENCY_NS] = float(
                    row["MinimumLatency(us)"]) * 1000
                result[ResultsConstants.MAX_LATENCY_NS] = float(
                    row["MaximumLatency(us)"]) * 1000
                result[ResultsConstants.AVG_LATENCY_NS] = float(
                    row["AverageLatency(us)"]) * 1000
                result[ResultsConstants.FRAME_LOSS_PERCENT] = float(
                    row["PercentLoss"])
        return result

    def send_cont_traffic(self, traffic=None, duration=30):
        """
        Send Custom - Continuous Test traffic
        Reuse RFC2544 throughput test specifications along with
        'custom' configuration
        """
        verbose = False
        custom = "cont"
        framesize = settings.getValue("TRAFFICGEN_STC_FRAME_SIZE")
        if traffic and 'l2' in traffic:
            if 'framesize' in traffic['l2']:
                framesize = traffic['l2']['framesize']

        stc_common_args = get_stc_common_settings()
        rfc2544_common_args = get_rfc2544_common_settings()
        rfc2544_custom_args = get_rfc2544_custom_settings(framesize,
                                                          custom, 1)
        args = rfc2544_common_args + stc_common_args + rfc2544_custom_args

        if settings.getValue("TRAFFICGEN_STC_VERBOSE") is "True":
            args.append("--verbose")
            verbose = True
            self._logger.debug("Arguments used to call test: %s", args)
        subprocess.check_call(args)

        filec = os.path.join(settings.getValue("TRAFFICGEN_STC_RESULTS_DIR"),
                             settings.getValue(
                                 "TRAFFICGEN_STC_CSV_RESULTS_FILE_PREFIX") +
                             ".csv")

        if verbose:
            self._logger.info("file: %s", filec)

        return self.get_rfc2544_results(filec)

    def send_rfc2544_throughput(self, traffic=None, tests=1, duration=20,
                                lossrate=0.0):
        """
        Send traffic per RFC2544 throughput test specifications.
        """
        verbose = False
        framesize = settings.getValue("TRAFFICGEN_STC_FRAME_SIZE")
        if traffic and 'l2' in traffic:
            if 'framesize' in traffic['l2']:
                framesize = traffic['l2']['framesize']

        stc_common_args = get_stc_common_settings()
        rfc2544_common_args = get_rfc2544_common_settings()
        rfc2544_custom_args = get_rfc2544_custom_settings(framesize, '',
                                                          tests)
        args = rfc2544_common_args + stc_common_args + rfc2544_custom_args

        if settings.getValue("TRAFFICGEN_STC_VERBOSE") is "True":
            args.append("--verbose")
            verbose = True
            self._logger.debug("Arguments used to call test: %s", args)
        subprocess.check_call(args)

        filec = os.path.join(settings.getValue("TRAFFICGEN_STC_RESULTS_DIR"),
                             settings.getValue(
                                 "TRAFFICGEN_STC_CSV_RESULTS_FILE_PREFIX") +
                             ".csv")

        if verbose:
            self._logger.info("file: %s", filec)

        return self.get_rfc2544_results(filec)

    def send_rfc2544_back2back(self, traffic=None, tests=1, duration=20,
                               lossrate=0.0):
        """
        Send traffic per RFC2544 BacktoBack test specifications.
        """
        verbose = False
        framesize = settings.getValue("TRAFFICGEN_STC_FRAME_SIZE")
        if traffic and 'l2' in traffic:
            if 'framesize' in traffic['l2']:
                framesize = traffic['l2']['framesize']

        stc_common_args = get_stc_common_settings()
        rfc2544_common_args = get_rfc2544_common_settings()
        rfc2544_custom_args = get_rfc2544_custom_settings(framesize, '',
                                                          tests)
        args = rfc2544_common_args + stc_common_args + rfc2544_custom_args

        if settings.getValue("TRAFFICGEN_STC_VERBOSE") is "True":
            args.append("--verbose")
            verbose = True
            self._logger.info("Arguments used to call test: %s", args)
        subprocess.check_call(args)

        filecs = os.path.join(settings.getValue("TRAFFICGEN_STC_RESULTS_DIR"),
                              settings.getValue(
                                  "TRAFFICGEN_STC_CSV_RESULTS_FILE_PREFIX") +
                              ".csv")
        if verbose:
            self._logger.debug("file: %s", filecs)

        return self.get_rfc2544_results(filecs)

    def start_cont_traffic(self, traffic=None, duration=30):
        raise NotImplementedError('TestCenter start_cont_traffic not implement.')

    def stop_cont_traffic(self):
        raise NotImplementedError('TestCenter stop_cont_traffic not implement.')

    def start_rfc2544_back2back(self, traffic=None, tests=1, duration=20,
                                lossrate=0.0):
        raise NotImplementedError('TestCenter start_rfc2544_back2back not implement.')

    def wait_rfc2544_back2back(self):
        raise NotImplementedError('TestCenter wait_rfc2544_back2back not implement.')

    def start_rfc2544_throughput(self, traffic=None, tests=1, duration=20,
                                 lossrate=0.0):
        raise NotImplementedError('TestCenter start_rfc2544_throughput not implement.')

    def wait_rfc2544_throughput(self):
        raise NotImplementedError('TestCenter wait_rfc2544_throughput not implement.')

if __name__ == '__main__':
    TRAFFIC = {
        'l3': {
            'proto': 'tcp',
            'srcip': '1.1.1.1',
            'dstip': '90.90.90.90',
        },
    }
    with TestCenter() as dev:
        print(dev.send_rfc2544_throughput(traffic=TRAFFIC))
        print(dev.send_rfc2544_backtoback(traffic=TRAFFIC))
