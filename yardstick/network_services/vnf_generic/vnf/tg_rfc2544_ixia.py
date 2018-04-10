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

from __future__ import absolute_import

import time
import os
import logging
import sys

from yardstick.common import utils
from yardstick import error
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import Rfc2544ResourceHelper

LOG = logging.getLogger(__name__)

WAIT_AFTER_CFG_LOAD = 10
WAIT_FOR_TRAFFIC = 30
IXIA_LIB = os.path.dirname(os.path.realpath(__file__))
IXNET_LIB = os.path.join(IXIA_LIB, "../../libs/ixia_libs/IxNet")
sys.path.append(IXNET_LIB)

try:
    from IxNet import IxNextgen
except ImportError:
    IxNextgen = error.ErrorClass


class IxiaRfc2544Helper(Rfc2544ResourceHelper):

    def is_done(self):
        return self.latency and self.iteration.value > 10


class IxiaResourceHelper(ClientResourceHelper):

    LATENCY_TIME_SLEEP = 120

    def __init__(self, setup_helper, rfc_helper_type=None):
        super(IxiaResourceHelper, self).__init__(setup_helper)
        self.scenario_helper = setup_helper.scenario_helper

        self.client = IxNextgen()

        if rfc_helper_type is None:
            rfc_helper_type = IxiaRfc2544Helper

        self.rfc_helper = rfc_helper_type(self.scenario_helper)
        self.uplink_ports = None
        self.downlink_ports = None
        self._connect()

    def _connect(self, client=None):
        self.client.connect(self.vnfd_helper)

    def get_stats(self, *args, **kwargs):
        return self.client.get_statistics()

    def stop_collect(self):
        self._terminated.value = 1
        if self.client:
            self.client.ix_stop_traffic()

    def generate_samples(self, ports, key=None, default=None):
        stats = self.get_stats()

        samples = {}
        # this is not DPDK port num, but this is whatever number we gave
        # when we selected ports and programmed the profile
        for port_num in ports:
            try:
                # reverse lookup port name from port_num so the stats dict is descriptive
                intf = self.vnfd_helper.find_interface_by_port(port_num)
                port_name = intf["name"]
                samples[port_name] = {
                    "rx_throughput_kps": float(stats["Rx_Rate_Kbps"][port_num]),
                    "tx_throughput_kps": float(stats["Tx_Rate_Kbps"][port_num]),
                    "rx_throughput_mbps": float(stats["Rx_Rate_Mbps"][port_num]),
                    "tx_throughput_mbps": float(stats["Tx_Rate_Mbps"][port_num]),
                    "in_packets": int(stats["Valid_Frames_Rx"][port_num]),
                    "out_packets": int(stats["Frames_Tx"][port_num]),
                    # NOTE(ralonsoh): we need to make the traffic injection
                    # time variable.
                    "RxThroughput": int(stats["Valid_Frames_Rx"][port_num]) / 30,
                    "TxThroughput": int(stats["Frames_Tx"][port_num]) / 30,
                }
                if key:
                    avg_latency = stats["Store-Forward_Avg_latency_ns"][port_num]
                    min_latency = stats["Store-Forward_Min_latency_ns"][port_num]
                    max_latency = stats["Store-Forward_Max_latency_ns"][port_num]
                    samples[port_name][key] = \
                        {"Store-Forward_Avg_latency_ns": avg_latency,
                         "Store-Forward_Min_latency_ns": min_latency,
                         "Store-Forward_Max_latency_ns": max_latency}
            except IndexError:
                pass

        return samples

    def _initialize_client(self):
        """Initialize the IXIA IxNetwork client and configure the server"""
        self.client.clear_config()
        self.client.assign_ports()
        self.client.create_traffic_item()

    def run_traffic(self, traffic_profile):
        if self._terminated.value:
            return

        min_tol = self.rfc_helper.tolerance_low
        max_tol = self.rfc_helper.tolerance_high
        default = "00:00:00:00:00:00"

        self._build_ports()
        self._initialize_client()

        mac = {}
        for port_name in self.vnfd_helper.port_pairs.all_ports:
            intf = self.vnfd_helper.find_interface(name=port_name)
            virt_intf = intf["virtual-interface"]
            # we only know static traffic id by reading the json
            # this is used by _get_ixia_trafficrofile
            port_num = self.vnfd_helper.port_num(intf)
            mac["src_mac_{}".format(port_num)] = virt_intf.get("local_mac", default)
            mac["dst_mac_{}".format(port_num)] = virt_intf.get("dst_mac", default)

        samples = {}
        # Generate ixia traffic config...
        try:
            while not self._terminated.value:
                traffic_profile.execute_traffic(self, self.client, mac)
                self.client_started.value = 1
                time.sleep(45)
                self.client.ix_stop_traffic()
                samples = self.generate_samples(traffic_profile.ports)
                self._queue.put(samples)
                status, samples = traffic_profile.get_drop_percentage(samples, min_tol,
                                                                      max_tol, self.client, mac)

                current = samples['CurrentDropPercentage']
                if min_tol <= current <= max_tol or status == 'Completed':
                    self._terminated.value = 1

            self.client.ix_stop_traffic()
            self._queue.put(samples)

            if not self.rfc_helper.is_done():
                self._terminated.value = 1
                return

            traffic_profile.execute_traffic(self, self.client, mac)
            for _ in range(5):
                time.sleep(self.LATENCY_TIME_SLEEP)
                self.client.ix_stop_traffic()
                samples = self.generate_samples(traffic_profile.ports, 'latency', {})
                self._queue.put(samples)
                traffic_profile.start_ixia_latency(self, self.client, mac)
                if self._terminated.value:
                    break

            self.client.ix_stop_traffic()
        except Exception:  # pylint: disable=broad-except
            LOG.exception("Run Traffic terminated")

        self._terminated.value = 1

    def collect_kpi(self):
        self.rfc_helper.iteration.value += 1
        return super(IxiaResourceHelper, self).collect_kpi()


class IxiaTrafficGen(SampleVNFTrafficGen):

    APP_NAME = 'Ixia'

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = IxiaResourceHelper

        super(IxiaTrafficGen, self).__init__(name, vnfd, setup_env_helper_type,
                                             resource_helper_type)
        self._ixia_traffic_gen = None
        self.ixia_file_name = ''
        self.vnf_port_pairs = []

    def _check_status(self):
        pass

    def terminate(self):
        self.resource_helper.stop_collect()
        super(IxiaTrafficGen, self).terminate()
