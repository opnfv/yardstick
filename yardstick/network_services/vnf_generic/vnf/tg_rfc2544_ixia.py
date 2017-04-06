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
import multiprocessing
import time
import os
import logging
import yaml
import sys

from yardstick.network_services.vnf_generic.vnf.base import GenericTrafficGen

LOG = logging.getLogger(__name__)

WAIT_AFTER_CFG_LOAD = 10
WAIT_FOR_TRAFFIC = 30
IXIA_LIB = os.path.dirname(os.path.realpath(__file__))
IXNET_LIB = os.path.join(IXIA_LIB, "../../libs/ixia_libs/IxNet")
sys.path.append(IXNET_LIB)


class IXIATrafficGen(GenericTrafficGen):
    def __init__(self, vnfd):
        super(IXIATrafficGen, self).__init__(vnfd)
        self._terminated = multiprocessing.Value('i', 0)
        self.client_started = multiprocessing.Value('i', 0)
        self._queue = multiprocessing.Queue()
        self._result = {}
        self._IxiaTrafficGen = None
        self.done = False
        self.ixia_file_name = ''
        self.tg_port_pairs = []
        self.vnf_port_pairs = []

    def _get_rfc_tolerance(self):
        tolerance = '0.0001 - 0.0001'
        tolerance = \
            self.options['rfc2544'].get('allowed_drop_rate', '0.0001 - 0.0001')

        tolerance = tolerance.split('-')
        min_tol = float(tolerance[0])
        if len(tolerance) == 2:
            max_tol = float(tolerance[1])
        else:
            max_tol = float(tolerance[0])

        return [min_tol, max_tol]

    def _traffic_runner(self, traffic_profile, queue,
                        client_started, terminated):

        tolerance = self._get_rfc_tolerance()
        min_tol = float(tolerance[0])
        max_tol = \
            float(tolerance[1]) if len(tolerance) == 2 else float(tolerance[0])
        self.generate_port_pairs(self.topology)
        self.priv_ports = [int(x[0][-1]) for x in self.tg_port_pairs]
        self.pub_ports = [int(x[1][-1]) for x in self.tg_port_pairs]
        self.my_ports = list(set(self.priv_ports).union(set(self.pub_ports)))
        interfaces = self.vnfd["vdu"][0]['external-interface']
        ixia_obj = self._IxiaTrafficGen
        ixia_obj.ix_load_config(self.ixia_file_name)
        time.sleep(WAIT_AFTER_CFG_LOAD)
        ixia_obj.ix_assign_ports()
        mac = {}
        for index, interface in enumerate(interfaces):
            key = "src_mac_{}".format(str(index + 1))
            mac[key] = interface["virtual-interface"]["local_mac"]
            key = "dst_mac_{}".format(str(index + 1))
            mac[key] = interface["virtual-interface"]["dst_mac"]

        xfile = os.path.join(os.getcwd(), "ixia_traffic.cfg")
        # Generate ixia traffic config...
        while not terminated.value:
            traffic_profile.execute(self, ixia_obj, mac, xfile)
            client_started.value = 1
            time.sleep(WAIT_FOR_TRAFFIC)
            last_stats = ixia_obj.ix_get_statistics()
            last_res = last_stats[1]
            self._IxiaTrafficGen.ix_stop_traffic()
            samples = {}
            for vpci_idx, interface in enumerate(interfaces):
                name = "xe{0}".format(vpci_idx)
                samples[name] = \
                    {"rx_throughput_kps":
                     float(last_res["Rx_Rate_Kbps"][vpci_idx]),
                     "tx_throughput_kps":
                     float(last_res["Tx_Rate_Kbps"][vpci_idx]),
                     "rx_throughput_mbps":
                     float(last_res["Rx_Rate_Mbps"][vpci_idx]),
                     "tx_throughput_mbps":
                     float(last_res["Tx_Rate_Mbps"][vpci_idx]),
                     "in_packets": int(last_res["Valid_Frames_Rx"][vpci_idx]),
                     "out_packets": int(last_res["Frames_Tx"][vpci_idx]),
                     "RxThroughput":
                     int(last_res["Valid_Frames_Rx"][vpci_idx]) / 30,
                     "TxThroughput": int(last_res["Frames_Tx"][vpci_idx]) / 30}
            status, samples = \
                traffic_profile.get_drop_percentage(self, samples, min_tol,
                                                    max_tol, ixia_obj, mac,
                                                    xfile)
            queue.put(samples)
            if min_tol <= samples['CurrentDropPercentage'] <= max_tol or \
               status == 'Completed':
                terminated.value = 1
                break
        self._IxiaTrafficGen.ix_stop_traffic()
        queue.put(samples)

    def run_traffic(self, traffic_profile):
        self._traffic_process = \
            multiprocessing.Process(target=self._traffic_runner,
                                    args=(traffic_profile, self._queue,
                                          self.client_started,
                                          self._terminated))
        self._traffic_process.start()
        # Wait for traffic process to start
        while self.client_started.value == 0:
            time.sleep(1)

        return self._traffic_process.is_alive()

    def listen_traffic(self, traffic_profile):
        pass

    def get_ixobj(self):
        from IxNet import IxNextgen
        return IxNextgen()

    def instantiate(self, node_name, scenario_cfg, context_cfg):
        self.options = scenario_cfg['options']
        self.node_name = node_name
        self.topology = scenario_cfg['topology']
        self._IxiaTrafficGen = self.get_ixobj()
        self.done = False
        self.ixia_file_name = '{0}'.format(scenario_cfg['ixia_profile'])

        # connect to ixia
        self._IxiaTrafficGen._connect(self.vnfd)

    def terminate(self):
        self._terminated.value = 0
        self._IxiaTrafficGen.ix_stop_traffic()
        self._traffic_process.terminate()

    def collect_kpi(self):
        if not self._queue.empty():
            r = self._queue.get()
            self._result.update(r)
        LOG.debug("ixia collect Kpis {0}".format(self._result))
        return self._result
