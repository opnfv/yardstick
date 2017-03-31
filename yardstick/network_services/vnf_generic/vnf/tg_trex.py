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
from __future__ import print_function
import multiprocessing
import time
import logging
import os
import yaml
from six.moves import range

from yardstick import ssh
from yardstick.network_services.vnf_generic.vnf.base import GenericTrafficGen
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.utils import provision_tool
from stl.trex_stl_lib.trex_stl_client import STLClient
from stl.trex_stl_lib.trex_stl_client import LoggerApi
from stl.trex_stl_lib.trex_stl_exceptions import STLError

LOG = logging.getLogger(__name__)
DURATION = 30
WAIT_QUEUE = 1
TREX_SYNC_PORT = 4500
TREX_ASYNC_PORT = 4501


class TrexTrafficGen(GenericTrafficGen):
    """
    This class handles mapping traffic profile and generating
    traffic for given testcase
    """

    def __init__(self, vnfd):
        super(TrexTrafficGen, self).__init__(vnfd)
        self._result = {}
        self._queue = multiprocessing.Queue()
        self._terminated = multiprocessing.Value('i', 0)
        self._traffic_process = None
        self._vpci_ascending = None
        self.client = None
        self.my_ports = None
        self._tg_process = None
        self.client_started = multiprocessing.Value('i', 0)

        mgmt_interface = vnfd["mgmt-interface"]

        self.connection = ssh.SSH.from_node(mgmt_interface)
        self.connection.wait()

    @classmethod
    def _split_mac_address_into_list(cls, mac):
        octets = mac.split(':')
        for i, elem in enumerate(octets):
            octets[i] = "0x" + str(elem)
        return octets

    def _generate_trex_cfg(self, vnfd):
        """

        :param vnfd: vnfd.yaml
        :return: trex_cfg.yaml file
        """
        trex_cfg = dict(
            port_limit=0,
            version='2',
            interfaces=[],
            port_info=list(dict(
            ))
        )
        trex_cfg["port_limit"] = len(vnfd["vdu"][0]["external-interface"])
        trex_cfg["version"] = '2'

        cfg_file = []
        vpci = []
        port = {}

        for interface in range(len(vnfd["vdu"][0]["external-interface"])):
            ext_intrf = vnfd["vdu"][0]["external-interface"]
            virtual_interface = ext_intrf[interface]["virtual-interface"]
            vpci.append(virtual_interface["vpci"])

            port["src_mac"] = self._split_mac_address_into_list(
                virtual_interface["local_mac"])
            port["dest_mac"] = self._split_mac_address_into_list(
                virtual_interface["dst_mac"])

            trex_cfg["port_info"].append(port.copy())

        trex_cfg["interfaces"] = vpci
        cfg_file.append(trex_cfg)

        with open('/tmp/trex_cfg.yaml', 'w') as outfile:
            outfile.write(yaml.safe_dump(cfg_file, default_flow_style=False))
        self.connection.put('/tmp/trex_cfg.yaml', '/tmp')

        self._vpci_ascending = sorted(vpci)

    def setup_vnf_environment(self, connection):
        ''' setup dpdk environment needed for vnf to run '''

        self.setup_hugepages(connection)
        connection.execute("sudo modprobe uio && sudo modprobe igb_uio")

        exit_status = connection.execute("lsmod | grep -i igb_uio")[0]
        if exit_status == 0:
            return

        dpdk = os.path.join(self.bin_path, "dpdk-16.07")
        dpdk_setup = \
            provision_tool(self.connection,
                           os.path.join(self.bin_path, "nsb_setup.sh"))
        status = connection.execute("ls {} >/dev/null 2>&1".format(dpdk))[0]
        if status:
            connection.execute("sudo bash %s dpdk >/dev/null 2>&1" % dpdk_setup)

    def scale(self, flavor=""):
        ''' scale vnfbased on flavor input '''
        super(TrexTrafficGen, self).scale(flavor)

    def instantiate(self, scenario_cfg, context_cfg):
        self._generate_trex_cfg(self.vnfd)
        self.setup_vnf_environment(self.connection)

        trex = os.path.join(self.bin_path, "trex")
        err = \
            self.connection.execute("ls {} >/dev/null 2>&1".format(trex))[0]
        if err != 0:
            LOG.info("Copying trex to destination...")
            self.connection.put("~/.bash_profile", "~/.bash_profile")
            self.connection.put(trex, trex, True)
            ko_src = os.path.join(trex, "scripts/ko/src/")
            self.connection.execute(
                "cd %s && make && sudo make install" % ko_src)

        LOG.info("Starting TRex server...")
        self._tg_process = \
            multiprocessing.Process(target=self._start_server)
        self._tg_process.start()
        while True:
            if not self._tg_process.is_alive():
                raise RuntimeError("Traffic Generator process died.")
            LOG.info("Waiting for TG Server to start.. ")
            time.sleep(1)
            status = \
                self.connection.execute("sudo lsof -i:%s" % TREX_SYNC_PORT)[0]
            if status == 0:
                LOG.info("TG server is up and running.")
                return self._tg_process.exitcode

    def listen_traffic(self, traffic_profile):
        pass

    def _get_logical_if_name(self, vpci):
        ext_intf = self.vnfd["vdu"][0]["external-interface"]
        for interface in range(len(self.vnfd["vdu"][0]["external-interface"])):
            virtual_intf = ext_intf[interface]["virtual-interface"]
            if virtual_intf["vpci"] == vpci:
                return ext_intf[interface]["name"]

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

    def _start_server(self):
        mgmt_interface = self.vnfd["mgmt-interface"]

        _server = ssh.SSH.from_node(mgmt_interface)
        _server.wait()

        _server.execute("sudo fuser -n tcp %s %s -k > /dev/null 2>&1" %
                        (TREX_SYNC_PORT, TREX_ASYNC_PORT))

        trex_path = os.path.join(self.bin_path, "trex/scripts")
        path = get_nsb_option("trex_path", trex_path)
        cmd = "sudo ./t-rex-64 -i --cfg /tmp/trex_cfg.yaml > /dev/null 2>&1"
        trex_cmd = "cd %s ; %s" % (path, cmd)

        _server.execute(trex_cmd)

    def _connect_client(self, client=None):
        if client is None:
            client = STLClient(username=self.vnfd["mgmt-interface"]["user"],
                               server=self.vnfd["mgmt-interface"]["ip"],
                               verbose_level=LoggerApi.VERBOSE_QUIET)
        # try to connect with 5s intervals, 30s max
        for idx in range(6):
            try:
                client.connect()
                break
            except STLError:
                LOG.info("Unable to connect to Trex Server.. Attempt %s", idx)
                time.sleep(5)
        return client

    def _traffic_runner(self, traffic_profile, queue,
                        client_started, terminated):
        LOG.info("Starting TRex client...")

        self.my_ports = [0, 1]
        self.client = self._connect_client()
        self.client.reset(ports=self.my_ports)

        self.client.remove_all_streams(self.my_ports)  # remove all streams

        while not terminated.value:
            traffic_profile.execute(self)
            client_started.value = 1
            last_res = self.client.get_stats(self.my_ports)
            if not isinstance(last_res, dict):  # added for mock unit test
                terminated.value = 1
                last_res = {}

            samples = {}
            for vpci_idx in range(len(self._vpci_ascending)):
                name = \
                    self._get_logical_if_name(self._vpci_ascending[vpci_idx])
                # fixme: VNFDs KPIs values needs to be mapped to TRex structure
                xe_value = last_res.get(vpci_idx, {})
                samples[name] = \
                    {"rx_throughput_fps": float(xe_value.get("rx_pps", 0.0)),
                     "tx_throughput_fps": float(xe_value.get("tx_pps", 0.0)),
                     "rx_throughput_mbps": float(xe_value.get("rx_bps", 0.0)),
                     "tx_throughput_mbps": float(xe_value.get("tx_bps", 0.0)),
                     "in_packets": xe_value.get("ipackets", 0),
                     "out_packets": xe_value.get("opackets", 0)}
            time.sleep(WAIT_QUEUE)
            queue.put(samples)

        self.client.disconnect()
        terminated.value = 0

    def collect_kpi(self):
        if not self._queue.empty():
            self._result.update(self._queue.get())
        LOG.debug("trex collect Kpis %s", self._result)
        return self._result

    def terminate(self):
        self.connection.execute("sudo fuser -n tcp %s %s -k > /dev/null 2>&1" %
                                (TREX_SYNC_PORT, TREX_ASYNC_PORT))
        self.traffic_finished = True
        if self._traffic_process:
            self._traffic_process.terminate()
