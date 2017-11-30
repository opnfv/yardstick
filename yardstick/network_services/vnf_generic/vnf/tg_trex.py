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
""" Trex acts as traffic generation and vnf definitions based on IETS Spec """

from __future__ import absolute_import
import logging
import io
import os

import yaml

from yardstick.common.utils import mac_address_to_hex_list, try_int, SocketTopology
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import DpdkVnfSetupEnvHelper

LOG = logging.getLogger(__name__)


class TrexDpdkVnfSetupEnvHelper(DpdkVnfSetupEnvHelper):
    APP_NAME = "t-rex-64"
    CFG_CONFIG = ""
    CFG_SCRIPT = ""
    PIPELINE_COMMAND = ""
    VNF_TYPE = "TG"


class TrexResourceHelper(ClientResourceHelper):

    CONF_FILE = '/tmp/trex_cfg.yaml'
    QUEUE_WAIT_TIME = 1
    RESOURCE_WORD = 'trex'
    RUN_DURATION = 0

    ASYNC_PORT = 4500
    SYNC_PORT = 4501
    MASTER_THREAD = 0
    LATENCY_THREAD = 1
    RESERVED_THREADS = {MASTER_THREAD, LATENCY_THREAD}

    def __init__(self, setup_helper):
        super(TrexResourceHelper, self).__init__(setup_helper)
        self.port_map = {}
        self.dpdk_to_trex_port_map = {}
        self.index_socket_map = {}

    def _get_threads(self, topo, socket):
        return sorted(proc for procs in topo[socket].values() for proc in procs if
                      proc not in self.RESERVED_THREADS)

    def _set_platform_socket_threads(self):
        stdout = io.BytesIO()
        self.ssh_helper.get_file_obj("/proc/cpuinfo", stdout)
        cpu_topology = SocketTopology.parse_cpuinfo(stdout.getvalue().decode('utf-8'))
        if not cpu_topology:
            LOG.warning("Cannont find socket topology, unable to assign threads")
            return {}
        dual_if = []
        for socket in sorted(self.index_socket_map.values()):
            dual_if.append({
                "socket": socket,
                "threads": self._get_threads(cpu_topology, socket)
            })
        return {
            "master_thread_id": self.MASTER_THREAD,
            "latency_thread_id": self.LATENCY_THREAD,
            "dual_if": dual_if,
        }

    def generate_cfg(self):
        port_names = self.vnfd_helper.port_pairs.all_ports
        vpci_list = []
        port_list = []
        self.port_map = {}
        self.dpdk_to_trex_port_map = {}

        sorted_ports = sorted((self.vnfd_helper.port_num(port_name), port_name) for port_name in
                              port_names)
        for index, (port_num, port_name) in enumerate(sorted_ports):
            interface = self.vnfd_helper.find_interface(name=port_name)
            virtual_interface = interface['virtual-interface']
            dst_mac = virtual_interface["dst_mac"]

            # this is to check for unused ports, all ports in the topology
            # will always have dst_mac
            if not dst_mac:
                continue
            # TRex ports are in logical order roughly based on DPDK port number sorting
            vpci_list.append(virtual_interface["vpci"])
            local_mac = virtual_interface["local_mac"]
            port_list.append({
                "src_mac": mac_address_to_hex_list(local_mac),
                "dest_mac": mac_address_to_hex_list(dst_mac),
            })
            self.port_map[port_name] = index
            self.dpdk_to_trex_port_map[port_num] = index
            self.index_socket_map[index] = try_int(virtual_interface["socket"])

        trex_cfg = {
            'interfaces': vpci_list,
            'port_info': port_list,
            "port_limit": len(port_names),
            "version": '2',
            "platform": self._set_platform_socket_threads(),
        }
        cfg_file = [trex_cfg]

        cfg_str = yaml.safe_dump(cfg_file, default_flow_style=False, explicit_start=True)
        self.ssh_helper.upload_config_file(os.path.basename(self.CONF_FILE), cfg_str)

    def _build_ports(self):
        super(TrexResourceHelper, self)._build_ports()
        # override with TRex logic port number
        self.uplink_ports = [self.dpdk_to_trex_port_map[p] for p in self.uplink_ports]
        self.downlink_ports = [self.dpdk_to_trex_port_map[p] for p in self.downlink_ports]
        self.all_ports = [self.dpdk_to_trex_port_map[p] for p in self.all_ports]

    def port_num(self, intf):
        # return logical TRex port
        return self.port_map[intf]

    def check_status(self):
        status, _, _ = self.ssh_helper.execute("sudo lsof -i:%s" % self.SYNC_PORT)
        return status

    def start(self, ports=None, *args, **kwargs):
        # pylint: disable=keyword-arg-before-vararg
        # NOTE(ralonsoh): defining keyworded arguments before variable
        # positional arguments is a bug. This function definition doesn't work
        # in Python 2, although it works in Python 3. Reference:
        # https://www.python.org/dev/peps/pep-3102/
        cmd = "sudo fuser -n tcp {0.SYNC_PORT} {0.ASYNC_PORT} -k > /dev/null 2>&1"
        self.ssh_helper.execute(cmd.format(self))

        self.ssh_helper.execute("sudo pkill -9 rex > /dev/null 2>&1")

        # We MUST default to 1 because TRex won't work on single-queue devices with
        # more than one core per port
        # We really should be trying to find the number of queues in the driver,
        # but there doesn't seem to be a way to do this
        # TRex Error: the number of cores should be 1 when the driver
        # support only one tx queue and one rx queue. Please use -c 1
        threads_per_port = try_int(self.scenario_helper.options.get("queues_per_port"), 1)

        trex_path = self.ssh_helper.join_bin_path("trex", "scripts")
        path = get_nsb_option("trex_path", trex_path)

        cmd = "./t-rex-64 --no-scapy-server -i -c {} --cfg '{}'".format(threads_per_port,
                                                                        self.CONF_FILE)

        if self.scenario_helper.options.get("trex_server_debug"):
            # if there are errors we want to see them
            redir = ""
        else:
            redir = ">/dev/null"
        # we have to sudo cd because the path might be owned by root
        trex_cmd = """sudo bash -c "cd '{}' ; {}" {}""".format(path, cmd, redir)
        LOG.debug(trex_cmd)
        self.ssh_helper.execute(trex_cmd)

    def terminate(self):
        super(TrexResourceHelper, self).terminate()
        cmd = "sudo fuser -n tcp %s %s -k > /dev/null 2>&1"
        self.ssh_helper.execute(cmd % (self.SYNC_PORT, self.ASYNC_PORT))


class TrexTrafficGen(SampleVNFTrafficGen):
    """
    This class handles mapping traffic profile and generating
    traffic for given testcase
    """

    APP_NAME = 'TRex'

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = TrexResourceHelper

        if setup_env_helper_type is None:
            setup_env_helper_type = TrexDpdkVnfSetupEnvHelper

        super(TrexTrafficGen, self).__init__(name, vnfd, setup_env_helper_type,
                                             resource_helper_type)

    def _check_status(self):
        return self.resource_helper.check_status()

    def _start_server(self):
        super(TrexTrafficGen, self)._start_server()
        self.resource_helper.start()

    def terminate(self):
        self.resource_helper.terminate()

    def wait_for_instantiate(self):
        return self._wait_for_process()
