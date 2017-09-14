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
import re

from multiprocessing import Queue
from ipaddress import IPv4Interface

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import DpdkVnfSetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper

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
            self.queue.put({
                "packets_received": float(match.group(1)),
                "rtt": float(match.group(2)),
            })

    def close(self):
        """ close the ssh connection """
        self.closed = True

    def clear(self):
        """ clear queue till Empty """
        while self.queue.qsize() > 0:
            self.queue.get()


class PingSetupEnvHelper(DpdkVnfSetupEnvHelper):

    def setup_vnf_environment(self):
        for intf in self.vnfd_helper.interfaces:
            vi = intf['virtual-interface']
            vi['local_iface_name'] = self.get_local_iface_name_by_vpci(vi['vpci'])


class PingResourceHelper(ClientResourceHelper):

    def __init__(self, setup_helper):
        super(PingResourceHelper, self).__init__(setup_helper)
        self._queue = Queue()
        self._parser = PingParser(self._queue)

    def run_traffic(self, traffic_profile):
        # drop the connection in order to force a new one
        self.ssh_helper.drop_connection()

        self.client_started.value = 1
        cmd_list = [
            "sudo ip addr flush {local_if_name}",
            "sudo ip addr add {local_ip}/24 dev {local_if_name}",
            "sudo ip link set {local_if_name} up",
        ]

        self.cmd_kwargs['packet_size'] = traffic_profile.params['traffic_profile']['frame_size']

        for cmd in cmd_list:
            self.ssh_helper.execute(cmd.format(**self.cmd_kwargs))

        ping_cmd = "nohup ping -s {packet_size} {target_ip}&"
        self.ssh_helper.run(ping_cmd.format(**self.cmd_kwargs),
                            stdout=self._parser,
                            keep_stdin_open=True, pty=True)


class PingTrafficGen(SampleVNFTrafficGen):
    """
    This traffic generator can ping a single IP with pingsize
    and target given in traffic profile
    """

    TG_NAME = 'Ping'
    APP_NAME = 'Ping'
    RUN_WAIT = 4

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = PingSetupEnvHelper
        if resource_helper_type is None:
            resource_helper_type = PingResourceHelper

        super(PingTrafficGen, self).__init__(name, vnfd, setup_env_helper_type,
                                             resource_helper_type)
        self._result = {}

    def scale(self, flavor=""):
        """ scale vnf-based on flavor input """
        pass

    def _check_status(self):
        return self._tg_process.is_alive()

    def instantiate(self, scenario_cfg, context_cfg):
        self._start_server()
        self._result = {
            "packets_received": 0,
            "rtt": 0,
        }
        intf = self.vnfd_helper.interfaces[0]["virtual-interface"]
        self.resource_helper.cmd_kwargs = {
            'target_ip': IPv4Interface(intf["dst_ip"]).ip.exploded,
            'local_ip': IPv4Interface(intf["local_ip"]).ip.exploded,
            'local_if_name': intf["local_iface_name"].split('/')[0],
        }

        self.setup_helper.setup_vnf_environment()

    def wait_for_instantiate(self):
        pass

    def listen_traffic(self, traffic_profile):
        """ Not needed for ping

        :param traffic_profile:
        :return:
        """
        pass
