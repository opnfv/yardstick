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

import logging
import time

from yardstick.network_services.vnf_generic.vnf.prox import ProxBase

LOG = logging.getLogger(__name__)


class ProxApproxVnf(ProxBase):

    APP_NAME = 'PROX'
    APP_WORD = 'PROX'
    PROX_MODE = "Workload"
    LUA_PARAMETER_NAME = "sut"

    def __init__(self, name, vnfd):
        super(ProxApproxVnf, self).__init__(name, vnfd)
        self._result = {}
        self._sut = None

    def collect_kpi(self):
        if self._sut is not None:

            if len(self.interfaces) not in {2, 4}:
                raise Exception(
                    "Failed ..Invalid no of ports .. 2 or 4 ports only supported at this time")

            port_stats = self._sut.port_stats(list(range(len(self.interfaces))))
            rx_total = port_stats[6]
            tx_total = port_stats[7]
            result = {
                "packets_in": tx_total,
                "packets_dropped": (tx_total - rx_total),
                "packets_fwd": rx_total,
                "collect_stats": (self.resource_helper.collect_kpi()),
            }
        else:
            result = {
                "packets_in": 0,
                "packets_out": 0,
                "packets_fwd": 0,
                "collect_stats": {"core": {}},
            }
        return result

    def terminate(self):
        super(ProxApproxVnf, self).terminate()
        if self._vnf_process:
            self._vnf_process.terminate()
        self.ssh_helper.execute("sudo pkill %s" % self.APP_NAME)
        self.rebind_drivers()
        self._tear_down()
        self.resource_helper.stop_collect()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(relativeCreated)6d %(threadName)s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    LOG.setLevel(logging.DEBUG)

    scenario = {}
    context = {}
    test_vnfd = {'benchmark': {'kpi': ['rx_throughput_fps',
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
                 'id': 'ProxApproxVnf',
                 'mgmt-interface': {'ip': '10.223.197.218',
                                    'password': 'intel@123',
                                    'user': 'root',
                                    'host': '10.223.197.218',
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
    s = ProxApproxVnf("vnf_1", test_vnfd)
    s.instantiate(scenario, context)
    print()
    "completed instantiate"
    for i in range(10):
        kpi = s.collect_kpi()
        print(kpi)
        if s.done:
            break
        time.sleep(35)
    s.terminate()
