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
import time

import yaml

from yardstick.network_services.traffic_profile.rfc2544 import RFC2544Profile
from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxDpdkVnfSetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen

LOG = logging.getLogger(__name__)


class ProxTrafficGen(SampleVNFTrafficGen):

    PROX_MODE = "Traffic Gen"
    LUA_PARAMETER_NAME = "gen"

    @staticmethod
    def _sort_vpci(vnfd):
        """

        :param vnfd: vnfd.yaml
        :return: trex_cfg.yaml file
        """

        def key_func(interface):
            return interface["virtual-interface"]["vpci"], interface["name"]

        ext_intf = vnfd["vdu"][0]["external-interface"]
        return sorted(ext_intf, key=key_func)

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = ProxDpdkVnfSetupEnvHelper

        if resource_helper_type is None:
            resource_helper_type = ProxResourceHelper

        super(ProxTrafficGen, self).__init__(name, vnfd, setup_env_helper_type,
                                             resource_helper_type)
        self._result = {}
        # for some reason
        self.vpci_if_name_ascending = self._sort_vpci(vnfd)
        self._traffic_process = None

    def listen_traffic(self, traffic_profile):
        pass

    def terminate(self):
        super(ProxTrafficGen, self).terminate()
        self.resource_helper.terminate()
        if self._traffic_process:
            self._traffic_process.terminate()
        self.ssh_helper.execute("pkill prox")
        self.resource_helper.rebind_drivers()


def manual_test():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(relativeCreated)6d %(threadName)s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    LOG.setLevel(logging.DEBUG)

    scenario = {}
    context = {}
    vnfd = {
        'benchmark': {
            'kpi': [
                'rx_throughput_fps',
                'tx_throughput_fps',
                'tx_throughput_mbps',
                'rx_throughput_mbps',
                'in_packets',
                'out_packets',
                'tx_throughput_pc_linerate',
                'rx_throughput_pc_linerate',
                'min_latency',
                'max_latency',
                'avg_latency',
            ],
        },
        'connection-point': [
            {'name': 'xe0', 'type': 'VPORT'},
            {'name': 'xe1', 'type': 'VPORT'},
        ],
        'description': 'TRex stateless traffic generator for RFC2544 test',
        'id': 'TrexTrafficGenRFC',
        'mgmt-interface': {
            'ip': '10.223.197.137',
            'password': 'intel@123',
            'user': 'root',
            'vdu-id': 'trexgen-baremetal',
        },
        'name': 'trexgen',
        'short-name': 'trexgen',
        'vdu': [
            {
                'description': 'TRex stateless tg for RFC2544 tests',
                'external-interface': [
                    {
                        'name': 'xe0',
                        'virtual-interface':
                            {
                                'bandwidth': '10 Gbps',
                                'dst_ip': '152.16.100.19',
                                'dst_mac': '3c:fd:fe:9c:87:72',
                                'local_ip': '152.16.100.20',
                                'netmask': '255.255.255.0',
                                'local_mac': '3c:fd:fe:9e:66:5a',
                                'type': 'PCI-PASSTHROUGH',
                                'vpci': '0000:81:00.0',
                            },
                        'vnfd-connection-point-ref': 'xe0',
                    },
                    {
                        'name': 'xe1',
                        'virtual-interface': {
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.21',
                            'dst_mac': '3c:fd:fe:9c:87:73',
                            'local_ip': '152.16.100.19',
                            'netmask': '255.255.255.0',
                            'local_mac': '3c:fd:fe:9e:66:5b',
                            'type': 'PCI-PASSTHROUGH',
                            'vpci': '0000:81:00.1',
                        },
                        'vnfd-connection-point-ref': 'xe1',
                    },
                ],
                'id': 'trexgen-baremetal',
                'name': 'trexgen-baremetal',
            },
        ],
    }

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
