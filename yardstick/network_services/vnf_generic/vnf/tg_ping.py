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
""" PING acts as traffic generation and vnf definitions based on IETS Spec """

from __future__ import absolute_import
from __future__ import print_function
import logging
import multiprocessing
import re
import time
import os

from yardstick import ssh
from yardstick.network_services.vnf_generic.vnf.base import GenericTrafficGen
from yardstick.network_services.traffic_profile.fixed import FixedProfile
from yardstick.network_services.utils import provision_tool

LOG = logging.getLogger(__name__)


class PingParser(object):
    """ Class providing file-like API for talking with SSH connection """

    def __init__(self, q_out):
        self.queue = q_out
        self.closed = False

    def write(self, chunk):
        """ 64 bytes from 10.102.22.93: icmp_seq=1 ttl=64 time=0.296 ms """
        match = re.search(r"icmp_seq=(\d+).*time=([0-9.]+)", chunk)
        LOG.debug("Parser called on %s", chunk)
        if match:
            # IMPORTANT: in order for the data to be properly taken
            # in by InfluxDB, it needs to be converted to numeric types
            self.queue.put({"packets_received": float(match.group(1)),
                            "rtt": float(match.group(2))})

    def close(self):
        ''' close the ssh connection '''
        pass

    def clear(self):
        ''' clear queue till Empty '''
        while self.queue.qsize() > 0:
            self.queue.get()


class PingTrafficGen(GenericTrafficGen):
    """
    This traffic generator can ping a single IP with pingsize
    and target given in traffic profile
    """

    def __init__(self, vnfd):
        super(PingTrafficGen, self).__init__(vnfd)
        self._result = {}
        self._parser = None
        self._queue = None
        self._traffic_process = None

        mgmt_interface = vnfd["mgmt-interface"]
        ssh_port = mgmt_interface.get("ssh_port", ssh.DEFAULT_PORT)
        LOG.debug("Connecting to %s", mgmt_interface["ip"])

        self.connection = ssh.SSH(mgmt_interface["user"], mgmt_interface["ip"],
                                  password=mgmt_interface["password"],
                                  port=ssh_port)
        self.connection.wait()

    def _bind_device_kernel(self, connection):
        dpdk_nic_bind = \
            provision_tool(self.connection,
                           os.path.join(self.bin_path, "dpdk_nic_bind.py"))

        drivers = {intf["virtual-interface"]["vpci"]:
                   intf["virtual-interface"]["driver"]
                   for intf in self.vnfd["vdu"][0]["external-interface"]}

        commands = \
            ['"{0}" --force -b "{1}" "{2}"'.format(dpdk_nic_bind, value, key)
             for key, value in drivers.items()]
        for command in commands:
            connection.execute(command)

        for index, out in enumerate(self.vnfd["vdu"][0]["external-interface"]):
            vpci = out["virtual-interface"]["vpci"]
            net = "find /sys/class/net -lname '*{}*' -printf '%f'".format(vpci)
            out = connection.execute(net)[1]
            ifname = out.split('/')[-1].strip('\n')
            self.vnfd["vdu"][0]["external-interface"][index][
                "virtual-interface"]["local_iface_name"] = ifname

    def scale(self, flavor=""):
        ''' scale vnfbased on flavor input '''
        super(PingTrafficGen, self).scale(flavor)

    def instantiate(self, scenario_cfg, context_cfg):
        self._result = {"packets_received": 0, "rtt": 0}
        self._bind_device_kernel(self.connection)

    def run_traffic(self, traffic_profile):
        self._queue = multiprocessing.Queue()
        self._parser = PingParser(self._queue)
        self._traffic_process = \
            multiprocessing.Process(target=self._traffic_runner,
                                    args=(traffic_profile, self._parser))
        self._traffic_process.start()
        # Wait for traffic process to start
        time.sleep(4)
        return self._traffic_process.is_alive()

    def listen_traffic(self, traffic_profile):
        """ Not needed for ping

        :param traffic_profile:
        :return:
        """
        pass

    def _traffic_runner(self, traffic_profile, filewrapper):

        mgmt_interface = self.vnfd["mgmt-interface"]
        ssh_port = mgmt_interface.get("ssh_port", ssh.DEFAULT_PORT)
        self.connection = ssh.SSH(mgmt_interface["user"], mgmt_interface["ip"],
                                  password=mgmt_interface["password"],
                                  port=ssh_port)
        self.connection.wait()
        external_interface = self.vnfd["vdu"][0]["external-interface"]
        virtual_interface = external_interface[0]["virtual-interface"]
        target_ip = virtual_interface["dst_ip"].split('/')[0]
        local_ip = virtual_interface["local_ip"].split('/')[0]
        local_if_name = \
            virtual_interface["local_iface_name"].split('/')[0]
        packet_size = traffic_profile.params["traffic_profile"]["frame_size"]

        run_cmd = []

        run_cmd.append("ip addr flush %s" % local_if_name)
        run_cmd.append("ip addr add %s/24 dev %s" % (local_ip, local_if_name))
        run_cmd.append("ip link set %s up" % local_if_name)

        for cmd in run_cmd:
            self.connection.execute(cmd)

        ping_cmd = ("ping -s %s %s" % (packet_size, target_ip))
        self.connection.run(ping_cmd, stdout=filewrapper,
                            keep_stdin_open=True, pty=True)

    def collect_kpi(self):
        if not self._queue.empty():
            kpi = self._queue.get()
            self._result.update(kpi)
        return self._result

    def terminate(self):
        self._traffic_process.terminate()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(relativeCreated)d \
                              %(threadName)s %(message)s')
    CONSOLE = logging.StreamHandler()
    CONSOLE.setLevel(logging.DEBUG)
    SCENARIO = {}
    CONTEXT = {}
    VNFDEN = {'benchmark': {'kpi': ['rtt', 'packets_received']},
              'connection-point': [{'name': 'xe0', 'type': 'VPORT'}],
              'description': 'Sample 1-port ping generator',
              'id': 'PingTrafficGen',
              'mgmt-interface': {'ip': '1.1.1.1',
                                 'password': 'r00t',
                                 'user': 'root',
                                 'vdu-id': 'pinggen-baremetal'},
              'name': 'pinggen',
              'short-name': 'pinggen',
              'vdu': [{'description': 'Sample 1-port ping generator',
                       'external-interface': [{'name': 'xe0',
                                               'virtual-interface':
                                               {'bandwidth': '10 Gbps',
                                                'dst_ip': '1.1.1.2',
                                                'dst_mac': '00:00:00:00:00:02',
                                                'local_ip': '1.1.1.1',
                                                'local_mac':
                                                '00:00:00:00:00:01',
                                                'type': 'PCI-PASSTHROUGH',
                                                'vpci': '83:00.1'},
                                               'vnfd-connection-point-ref':
                                               'xe0'}],
                       'id': 'pinggen-baremetal',
                       'name': 'pinggen-baremetal'}]}

    MOCK_TRAFFIC_PROFILE = {
        "schema": "nsb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,  # pps
            "flow_number": 10,
            "frame_size": 64
        }
    }
    PINGVNF = PingTrafficGen(VNFDEN)
    PINGVNF.instantiate(SCENARIO, CONTEXT)
    PINGVNF.run_traffic(FixedProfile(MOCK_TRAFFIC_PROFILE))
    for i in range(10):
        print(PINGVNF.collect_kpi())
        time.sleep(1)
    PINGVNF.terminate()
