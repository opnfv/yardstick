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
import multiprocessing
import os
import time

from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper
from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxResourceHelper
from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxDpdkVnfSetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF

LOG = logging.getLogger(__name__)


class ProxApproxVnf(SampleVNF):

    APP_NAME = 'PROX'
    APP_WORD = 'PROX'
    PROX_MODE = "Workload"
    VNF_PROMPT = "PROX started"
    LUA_PARAMETER_NAME = "sut"

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = ProxDpdkVnfSetupEnvHelper

        if resource_helper_type is None:
            resource_helper_type = ProxResourceHelper

        super(ProxApproxVnf, self).__init__(name, vnfd, setup_env_helper_type,
                                            resource_helper_type)
        self._result = {}
        self._sut = None
        self._terminated = multiprocessing.Value('i', 0)
        self._queue = multiprocessing.Value('i', 0)

    def instantiate(self, scenario_cfg, context_cfg):
        LOG.info("printing .........prox instantiate ")

        self.scenario_helper.scenario_cfg = scenario_cfg

        # this won't work we need 1GB hugepages at boot
        self.setup_helper.setup_vnf_environment()

        # self.connection.run("cat /proc/cpuinfo")

        prox_args, prox_path, remote_path = self.resource_helper.get_process_args()

        self.q_in = multiprocessing.Queue()
        self.q_out = multiprocessing.Queue()
        self.queue_wrapper = QueueFileWrapper(self.q_in, self.q_out, "PROX started")
        self._vnf_process = multiprocessing.Process(target=self._run_prox,
                                                    args=(remote_path, prox_path, prox_args))
        self._vnf_process.start()

    def _vnf_up_post(self):
        self.resource_helper.up_post()

    def _run_prox(self, file_wrapper, config_path, prox_path, prox_args):
        # This runs in a different process and should not share an SSH connection
        # with the rest of the object
        self.ssh_helper.drop_connection()

        time.sleep(self.WAIT_TIME)

        args = " ".join(" ".join([k, v if v else ""]) for k, v in prox_args.items())

        cmd_template = "sudo bash -c 'cd {}; {} -o cli {} -f {} '"
        prox_cmd = cmd_template.format(os.path.dirname(prox_path), prox_path, args, config_path)

        LOG.debug(prox_cmd)
        self.ssh_helper.run(prox_cmd, stdin=file_wrapper, stdout=file_wrapper,
                            keep_stdin_open=True, pty=False)

    def vnf_execute(self, cmd, wait_time=2):
        # try to execute with socket commands
        self.resource_helper.execute(cmd)

    def collect_kpi(self):
        if self._sut is None:
            result = {
                "packets_in": 0,
                "packets_out": 0,
                "packets_fwd": 0,
                "collect_stats": {"core": {}},
            }
            return result

        if len(self.vnfd_helper.interfaces) not in {2, 4}:
            raise Exception("Failed ..Invalid no of ports .. "
                            "2 or 4 ports only supported at this time")

        port_stats = self._sut.port_stats(self.vnfd_helper.interfaces)
        rx_total = port_stats[6]
        tx_total = port_stats[7]
        result = {
            "packets_in": tx_total,
            "packets_dropped": (tx_total - rx_total),
            "packets_fwd": rx_total,
            "collect_stats": self.resource_helper.collect_kpi(),
        }
        return result

    def _tear_down(self):
        self.setup_helper.rebind_drivers()


def manual_test():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(relativeCreated)6d %(threadName)s %(message)s')

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    LOG.setLevel(logging.DEBUG)

    scenario = {}
    context = {}
    test_vnfd = {
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
        'id': 'ProxApproxVnf',
        'mgmt-interface': {
            'ip': '10.223.197.218',
            'password': 'intel@123',
            'user': 'root',
            'host': '10.223.197.218',
            'vdu-id': 'trexgen-baremetal'
        },
        'name': 'trexgen',
        'short-name': 'trexgen',
        'vdu': [
            {
                'description': 'TRex stateless tg for RFC2544 tests',
                'external-interface': [
                    {
                        'name': 'xe0',
                        'virtual-interface': {
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.100.19',
                            'dst_mac': '3c:fd:fe:9c:87:72',
                            'local_ip': '152.16.100.20',
                            'netmask': '255.255.255.0',
                            'local_mac': '3c:fd:fe:9e:66:5a',
                            'type': 'PCI-PASSTHROUGH',
                            'vpci': '0000:81:00.0'
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

    s = ProxApproxVnf("vnf_1", test_vnfd)
    s.instantiate(scenario, context)
    print("completed instantiate")
    for _ in range(10):
        kpi = s.collect_kpi()
        print(kpi)
        if s.done:
            break
        time.sleep(35)
    s.terminate()

if __name__ == '__main__':
    manual_test()
