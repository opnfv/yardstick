# Copyright (c) 2017 Intel Corporation
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

from __future__ import print_function, absolute_import

import logging
import multiprocessing
import re
import time

import yaml

from yardstick.network_services.traffic_profile.rfc2544 import RFC2544Profile
from yardstick.network_services.vnf_generic.vnf.base import \
    GenericTrafficGen
from yardstick.network_services.vnf_generic.vnf.prox import ProxBase, \
    line_rate_to_pps

LOG = logging.getLogger(__name__)

PROX_CORE_GEN_MODE = "gen"
PROX_CORE_LAT_MODE = "lat"


class ProxTrafficGen(ProxBase, GenericTrafficGen):

    PROX_MODE = "Traffic Gen"
    LUA_PARAMETER_NAME = "gen"

    def __init__(self, name, vnfd):
        super(ProxTrafficGen, self).__init__(name, vnfd)
        self._result = {}
        # for some reason
        self._sort_vpci(vnfd)

    def listen_traffic(self, traffic_profile):
        pass

    def run_traffic(self, traffic_profile):
        client_started = multiprocessing.Value('i', 0)
        self._queue = multiprocessing.Queue()

        self._traffic_process = \
            multiprocessing.Process(target=self._traffic_runner,
                                    args=(traffic_profile, self._queue,
                                          client_started, self._terminated))
        self._traffic_process.start()
        # Wait for traffic process to start
        while client_started.value == 0:
            time.sleep(1)

        return self._traffic_process.is_alive()

    def _sort_vpci(self, vnfd):
        """

        :param vnfd: vnfd.yaml
        :return: trex_cfg.yaml file
        """

        ext_intf = vnfd["vdu"][0]["external-interface"]
        self.vpci_if_name_ascending = sorted(
            (interface["virtual-interface"]["vpci"], interface["name"]) for
            interface in ext_intf)

    def run_test(self, pkt_size, duration, value, tolerated_loss=0.0):

        self.tester.stop_all()
        self.tester.reset_stats()
        self.tester.set_pkt_size(self._test_cores, pkt_size)
        self.tester.set_speed(self._test_cores, value)
        self.tester.start_all()

        # Getting statistics to calculate PPS at right speed....
        tsc_hz = self.tester.hz()
        time.sleep(2)
        rx_start, tx_start, tsc_start = self.tester.tot_stats()
        time.sleep(duration)
        # Get stats before stopping the cores. Stopping cores takes some time
        # and might skew results otherwise.
        rx_stop, tx_stop, tsc_stop = self.tester.tot_stats()
        latency = self.get_latency()

        self.tester.stop_all()

        if len(self.interfaces) not in {2, 4}:
            raise Exception(
                "Failed ..Invalid no of ports .. 2 or 4 ports only supported at this time")

        port_stats = self.tester.port_stats(list(range(len(self.interfaces))))

        rx_total = port_stats[6]
        tx_total = port_stats[7]

        can_be_lost = int(tx_total * float(tolerated_loss) / 100.0)
        LOG.debug("RX: %d; TX: %d; dropped: %d (tolerated: %d)", rx_total,
                  tx_total, tx_total - rx_total, can_be_lost)

        # calculate the effective throughput in Mpps
        tx = tx_stop - tx_start
        tsc = tsc_stop - tsc_start
        mpps = tx / (tsc / float(tsc_hz)) / 1000000

        pps = (value / 100.0) * line_rate_to_pps(pkt_size, len(self.interfaces))
        LOG.debug("Mpps configured: %f; Mpps effective %f",
                  (pps / 1000000.0), mpps)

        try:
            pkt_loss = 100.0 * (tx_total - rx_total) / float(tx_total)
        except ZeroDivisionError:
            pkt_loss = 100.0
        res = ((tx_total - rx_total <= can_be_lost),
               mpps, pkt_loss, rx_total, tx_total, pps, mpps, latency)
        # TODO handle ZeroDivisionError
        return res

    CORE_RE = re.compile(r"core\s+(\d+)(?:s(\d+))?(h)?")

    def get_core_socket(self, core_line):
        core, socket, hyperthread = self.CORE_RE.search(core_line).groups()
        return int(
            core), int(socket) if socket is not None else 0, hyperthread == "h"

    def get_cores_of_mode(self, mode):
        cores = []
        for section in self.prox_config_dict:
            if section.startswith("core"):
                for index, item in enumerate(self.prox_config_dict[section]):
                    if item[0] == "mode" and item[1] == mode:
                        core = self.get_cpu_id(self._tester_cpu_map,
                                               *self.get_core_socket(section))
                        cores.append(core)
        return cores

    def get_tg_cores(self):
        return self.get_cores_of_mode(PROX_CORE_GEN_MODE)

    def get_latency_cores(self):
        return self.get_cores_of_mode(PROX_CORE_LAT_MODE)

    def _traffic_runner(self, traffic_profile, queue, client_started,
                        terminated):

        LOG.info("Starting Prox %s", self.PROX_MODE)
        self.tester = self._get_socket()
        self.lower = 0.0
        self.upper = 100.0
        self._test_cores = self.get_tg_cores()
        self._latency_cores = self.get_latency_cores()

        traffic_profile.init(queue)
        # this frees up the run_traffic loop
        client_started.value = 1

        while not terminated.value:
            # move it all to traffic_profile
            traffic_profile.execute(self)
            if traffic_profile.done:
                queue.put({'done': True})
                LOG.debug("tg_prox done")
                terminated.value = 1
                break
        # close socket so we can reconnect
        self.tester.get_socket().close()

    def collect_kpi(self):
        if not self._queue.empty():
            r = self._queue.get()
            # if r is {} then update will do nothing
            self._result.update(r)
        LOG.info("Collecting PROX stats")
        LOG.info("PROX collect Kpis %s", self._result)
        return self._result

    def terminate(self):
        super(ProxTrafficGen, self).terminate()
        self._terminated.value = 1
        if self._traffic_process:
            self._traffic_process.terminate()
        self.connection.execute("pkill prox")
        self.rebind_drivers()

    def get_latency(self):
        """
        :return: return lat_min, lat_max, lat_avg
        :rtype: list
        """
        if self._latency_cores:
            return self.tester.lat_stats(self._latency_cores)
        return []


def manual_test():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(relativeCreated)6d %(threadName)s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    LOG.setLevel(logging.DEBUG)

    scenario = {}
    context = {}
    vnfd = {'benchmark': {'kpi': ['rx_throughput_fps',
                                  'tx_throughput_fps',
                                  'tx_throughput_mbps',
                                  'rx_throughput_mbps',
                                  'in_packets',
                                  'out_packets',
                                  'tx_throughput_pc_linerate',
                                  'rx_throughput_pc_linerate',
                                  'min_latency',
                                  'max_latency',
                                  'avg_latency']},
            'connection-point': [{'name': 'xe0', 'type': 'VPORT'},
                                 {'name': 'xe1', 'type': 'VPORT'}],
            'description': 'TRex stateless traffic generator for RFC2544 test',
            'id': 'TrexTrafficGenRFC',
            'mgmt-interface': {'ip': '10.223.197.137',
                               'password': 'intel@123',
                               'user': 'root',
                               'vdu-id': 'trexgen-baremetal'},
            'name': 'trexgen',
            'short-name': 'trexgen',
            'vdu': [{'description': 'TRex stateless tg for RFC2544 tests',
                     'external-interface': [{'name': 'xe0',
                                             'virtual-interface':
                                                 {'bandwidth': '10 Gbps',
                                                  'dst_ip': '152.16.100.19',
                                                  'dst_mac':
                                                      '3c:fd:fe:9c:87:72',
                                                  'local_ip': '152.16.100.20',
                                                  'netmask': '255.255.255.0',
                                                  'local_mac':
                                                      '3c:fd:fe:9e:66:5a',
                                                  'type': 'PCI-PASSTHROUGH',
                                                  'vpci': '0000:81:00.0'},
                                             'vnfd-connection-point-ref':
                                                 'xe0'},
                                            {'name': 'xe1',
                                             'virtual-interface':
                                                 {'bandwidth': '10 Gbps',
                                                  'dst_ip': '152.16.40.21',
                                                  'dst_mac':
                                                      '3c:fd:fe:9c:87:73',
                                                  'local_ip': '152.16.100.19',
                                                  'netmask': '255.255.255.0',
                                                  'local_mac':
                                                      '3c:fd:fe:9e:66:5b',
                                                  'type': 'PCI-PASSTHROUGH',
                                                  'vpci': '0000:81:00.1'},
                                             'vnfd-connection-point-ref':
                                                 'xe1'}],
                     'id': 'trexgen-baremetal',
                     'name': 'trexgen-baremetal'}]}
    yaml_file = 'fixed.yaml'
    data = yaml.safe_load(open(yaml_file).read())
    name = "tg_1"
    s = ProxTrafficGen(name, vnfd)
    s.instantiate(scenario, context)
    s.run_traffic(RFC2544Profile(data))
    for _ in range(10):
        kpi = s.collect_kpi()
        print(kpi)
        if s.done:
            break
        time.sleep(35)
    s.terminate()


if __name__ == '__main__':
    manual_test()
