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

from yardstick.common.utils import ErrorClass
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import Rfc2544ResourceHelper
from yardstick.benchmark.scenarios.networking.vnf_generic import find_relative_file

LOG = logging.getLogger(__name__)

WAIT_AFTER_CFG_LOAD = 10
WAIT_FOR_TRAFFIC = 30
IXIA_LIB = os.path.dirname(os.path.realpath(__file__))
IXNET_LIB = os.path.join(IXIA_LIB, "../../libs/ixia_libs/IxNet")
sys.path.append(IXNET_LIB)

try:
    from IxNet import IxNextgen
except ImportError:
    IxNextgen = ErrorClass


class IxiaRfc2544Helper(Rfc2544ResourceHelper):

    pass


class IxiaResourceHelper(ClientResourceHelper):

    def __init__(self, setup_helper, rfc_helper_type=None):
        super(IxiaResourceHelper, self).__init__(setup_helper)
        self.scenario_helper = setup_helper.scenario_helper

        self.client = IxNextgen()

        if rfc_helper_type is None:
            rfc_helper_type = IxiaRfc2544Helper

        self.rfc_helper = rfc_helper_type(self.scenario_helper)
        self.tg_port_pairs = []
        self.priv_ports = None
        self.pub_ports = None

    def _connect(self, client=None):
        self.client._connect(self.vnfd_helper)

    def _build_ports(self):
        # self.generate_port_pairs(self.topology)
        self.priv_ports = [int(x[0][2:]) for x in self.tg_port_pairs]
        self.pub_ports = [int(x[1][2:]) for x in self.tg_port_pairs]
        self.my_ports = list(set(self.priv_ports).union(set(self.pub_ports)))

    def get_stats(self, *args, **kwargs):
        return self.client.ix_get_statistics()[1]

    def stop_collect(self):
        self._terminated.value = 0
        if self.client and self.client.ixnet:
            self.client.ix_stop_traffic()

    def generate_samples(self, key=None, default=None):
        last_result = self.get_stats()

        samples = {}
        for vpci_idx, interface in enumerate(self.vnfd_helper.interfaces):
            name = "xe{0}".format(vpci_idx)
            samples[name] = {
                "rx_throughput_kps": float(last_result["Rx_Rate_Kbps"][vpci_idx]),
                "tx_throughput_kps": float(last_result["Tx_Rate_Kbps"][vpci_idx]),
                "rx_throughput_mbps": float(last_result["Rx_Rate_Mbps"][vpci_idx]),
                "tx_throughput_mbps": float(last_result["Tx_Rate_Mbps"][vpci_idx]),
                "in_packets": int(last_result["Valid_Frames_Rx"][vpci_idx]),
                "out_packets": int(last_result["Frames_Tx"][vpci_idx]),
                "RxThroughput": int(last_result["Valid_Frames_Rx"][vpci_idx]) / 30,
                "TxThroughput": int(last_result["Frames_Tx"][vpci_idx]) / 30,
            }

        return samples

    def run_traffic(self, traffic_profile):
        min_tol = self.rfc_helper.tolerance_low
        max_tol = self.rfc_helper.tolerance_high

        self._build_ports()
        self._connect()

        # we don't know client_file_name until runtime as instantiate
        client_file_name = \
            find_relative_file(self.scenario_helper.scenario_cfg['ixia_profile'],
                               self.scenario_helper.scenario_cfg["task_path"])
        self.client.ix_load_config(client_file_name)
        time.sleep(WAIT_AFTER_CFG_LOAD)

        self.client.ix_assign_ports()

        mac = {}
        for index, interface in enumerate(self.vnfd_helper.interfaces, 1):
            virt_intf = interface["virtual-interface"]
            mac.update({
                "src_mac_{}".format(index): virt_intf["local_mac"],
                "dst_mac_{}".format(index): virt_intf["dst_mac"],
            })

        samples = {}

        ixia_file = find_relative_file("ixia_traffic.cfg",
                                       self.scenario_helper.scenario_cfg["task_path"])
        # Generate ixia traffic config...
        while not self._terminated.value:
            traffic_profile.execute(self, self.client, mac, ixia_file)
            self.client_started.value = 1
            time.sleep(WAIT_FOR_TRAFFIC)
            self.client.ix_stop_traffic()
            samples = self.generate_samples()
            self._queue.put(samples)
            status, samples = traffic_profile.get_drop_percentage(self, samples, min_tol,
                                                                  max_tol, self.client, mac,
                                                                  ixia_file)

            current = samples['CurrentDropPercentage']
            if min_tol <= current <= max_tol or status == 'Completed':
                self._terminated.value = 1

        self.client.ix_stop_traffic()
        self._queue.put(samples)


class IxiaTrafficGen(SampleVNFTrafficGen):

    APP_NAME = 'Ixia'

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = IxiaResourceHelper

        super(IxiaTrafficGen, self).__init__(name, vnfd, setup_env_helper_type,
                                             resource_helper_type)
        self._ixia_traffic_gen = None
        self.ixia_file_name = ''
        self.tg_port_pairs = []
        self.vnf_port_pairs = []

    def _check_status(self):
        pass

    def scale(self, flavor=""):
        pass

    def listen_traffic(self, traffic_profile):
        pass

    def terminate(self):
        self.resource_helper.stop_collect()
        super(IxiaTrafficGen, self).terminate()

    def wait_for_instantiate(self):
        # not needed for IxNet
        pass
