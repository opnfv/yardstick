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

import logging

from yardstick.common import utils
from yardstick.network_services.libs.ixia_libs.ixnet import ixnet_api
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import Rfc2544ResourceHelper


LOG = logging.getLogger(__name__)

WAIT_AFTER_CFG_LOAD = 10
WAIT_FOR_TRAFFIC = 30


class IxiaRfc2544Helper(Rfc2544ResourceHelper):

    def is_done(self):
        return self.latency and self.iteration.value > 10


class IxiaResourceHelper(ClientResourceHelper):

    LATENCY_TIME_SLEEP = 120

    def __init__(self, setup_helper, rfc_helper_type=None):
        super(IxiaResourceHelper, self).__init__(setup_helper)
        self.scenario_helper = setup_helper.scenario_helper

        self.client = ixnet_api.IxNextgen()

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

    def generate_samples(self, ports, duration):
        stats = self.get_stats()

        samples = {}
        # this is not DPDK port num, but this is whatever number we gave
        # when we selected ports and programmed the profile
        for port_num in ports:
            try:
                # reverse lookup port name from port_num so the stats dict is descriptive
                intf = self.vnfd_helper.find_interface_by_port(port_num)
                port_name = intf['name']
                avg_latency = stats['Store-Forward_Avg_latency_ns'][port_num]
                min_latency = stats['Store-Forward_Min_latency_ns'][port_num]
                max_latency = stats['Store-Forward_Max_latency_ns'][port_num]
                samples[port_name] = {
                    'rx_throughput_kps': float(stats['Rx_Rate_Kbps'][port_num]),
                    'tx_throughput_kps': float(stats['Tx_Rate_Kbps'][port_num]),
                    'rx_throughput_mbps': float(stats['Rx_Rate_Mbps'][port_num]),
                    'tx_throughput_mbps': float(stats['Tx_Rate_Mbps'][port_num]),
                    'in_packets': int(stats['Valid_Frames_Rx'][port_num]),
                    'out_packets': int(stats['Frames_Tx'][port_num]),
                    'RxThroughput': float(stats['Valid_Frames_Rx'][port_num]) / duration,
                    'TxThroughput': float(stats['Frames_Tx'][port_num]) / duration,
                    'Store-Forward_Avg_latency_ns': utils.safe_cast(avg_latency, int, 0),
                    'Store-Forward_Min_latency_ns': utils.safe_cast(min_latency, int, 0),
                    'Store-Forward_Max_latency_ns': utils.safe_cast(max_latency, int, 0)
                }
            except IndexError:
                pass

        return samples

    def _initialize_client(self):
        """Initialize the IXIA IxNetwork client and configure the server"""
        self.client.clear_config()
        self.client.assign_ports()
        self.client.create_traffic_model()

    def run_traffic(self, traffic_profile, *args):
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

        try:
            while not self._terminated.value:
                first_run = traffic_profile.execute_traffic(
                    self, self.client, mac)
                self.client_started.value = 1
                # pylint: disable=unnecessary-lambda
                utils.wait_until_true(lambda: self.client.is_traffic_stopped(),
                                      timeout=traffic_profile.config.duration * 2)
                samples = self.generate_samples(traffic_profile.ports,
                                                traffic_profile.config.duration)

                completed, samples = traffic_profile.get_drop_percentage(
                    samples, min_tol, max_tol, first_run=first_run)
                self._queue.put(samples)

                if completed:
                    self._terminated.value = 1

        except Exception:  # pylint: disable=broad-except
            LOG.exception('Run Traffic terminated')

        self._terminated.value = 1

    def collect_kpi(self):
        self.rfc_helper.iteration.value += 1
        return super(IxiaResourceHelper, self).collect_kpi()


class IxiaTrafficGen(SampleVNFTrafficGen):

    APP_NAME = 'Ixia'

    def __init__(self, name, vnfd, task_id, setup_env_helper_type=None,
                 resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = IxiaResourceHelper
        super(IxiaTrafficGen, self).__init__(
            name, vnfd, task_id, setup_env_helper_type, resource_helper_type)
        self._ixia_traffic_gen = None
        self.ixia_file_name = ''
        self.vnf_port_pairs = []

    def _check_status(self):
        pass

    def terminate(self):
        self.resource_helper.stop_collect()
        super(IxiaTrafficGen, self).terminate()
