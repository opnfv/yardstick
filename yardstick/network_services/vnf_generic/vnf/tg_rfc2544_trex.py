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
""" Trex traffic generation definitions which implements rfc2544 """

from __future__ import absolute_import
from __future__ import print_function
import multiprocessing
import time
import logging
import os
import yaml

from yardstick import ssh
from yardstick.network_services.vnf_generic.vnf.base import GenericTrafficGen
from yardstick.network_services.utils import get_nsb_option
from stl.trex_stl_lib.trex_stl_client import STLClient
from stl.trex_stl_lib.trex_stl_client import LoggerApi
from stl.trex_stl_lib.trex_stl_exceptions import STLError

LOGGING = logging.getLogger(__name__)

DURATION = 30
TREX_SYNC_PORT = 4500
TREX_ASYNC_PORT = 4501


class TrexTrafficGenRFC(GenericTrafficGen):
    """
    This class handles mapping traffic profile and generating
    traffic for rfc2544 testcase.
    """

    def __init__(self, vnfd):
        super(TrexTrafficGenRFC, self).__init__(vnfd)
        self._result = {}
        self._terminated = multiprocessing.Value('i', 0)
        self._queue = multiprocessing.Queue()
        self._terminated = multiprocessing.Value('i', 0)
        self._traffic_process = None
        self._vpci_ascending = None
        self.tc_file_name = None
        self.client = None
        self.my_ports = None

        mgmt_interface = self.vnfd["mgmt-interface"]
        ssh_port = mgmt_interface.get("ssh_port", ssh.DEFAULT_PORT)
        self.connection = ssh.SSH(mgmt_interface["user"], mgmt_interface["ip"],
                                  password=mgmt_interface["password"],
                                  port=ssh_port)
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

        ext_intf = vnfd["vdu"][0]["external-interface"]
        for interface in ext_intf:
            virt_intf = interface["virtual-interface"]
            vpci.append(virt_intf["vpci"])

            port["src_mac"] = \
                self._split_mac_address_into_list(virt_intf["local_mac"])

            time.sleep(3)
            port["dest_mac"] = \
                self._split_mac_address_into_list(virt_intf["dst_mac"])
            if virt_intf["dst_mac"]:
                trex_cfg["port_info"].append(port.copy())

        trex_cfg["interfaces"] = vpci
        cfg_file.append(trex_cfg)

        with open('/tmp/trex_cfg.yaml', 'w') as outfile:
            outfile.write(yaml.safe_dump(cfg_file, default_flow_style=False))
        self.connection.put('/tmp/trex_cfg.yaml', '/etc')

        self._vpci_ascending = sorted(vpci)

    def scale(self, flavor=""):
        ''' scale vnfbased on flavor input '''
        super(TrexTrafficGenRFC, self).scale(flavor)

    def instantiate(self, scenario_cfg, context_cfg):
        self._generate_trex_cfg(self.vnfd)
        self.tc_file_name = '{0}.yaml'.format(scenario_cfg['tc'])
        trex = os.path.join(self.bin_path, "trex")
        err, _, _ = \
            self.connection.execute("ls {} >/dev/null 2>&1".format(trex))
        if err != 0:
            self.connection.put(trex, trex, True)

        LOGGING.debug("Starting TRex server...")
        _tg_server = \
            multiprocessing.Process(target=self._start_server)
        _tg_server.start()
        while True:
            if not _tg_server.is_alive():
                raise RuntimeError("Traffic Generator process died.")
            status = \
                self.connection.execute("lsof -i:%s" % TREX_SYNC_PORT)[0]
            if status == 0:
                LOGGING.info("TG server is up and running.")
                return _tg_server.exitcode
            LOGGING.info("Waiting for TG Server to start.. ")
            time.sleep(1)
        return _tg_server.is_alive()

    def listen_traffic(self, traffic_profile):
        pass

    def _get_logical_if_name(self, vpci):
        ext_intf = self.vnfd["vdu"][0]["external-interface"]
        for interface in range(len(self.vnfd["vdu"][0]["external-interface"])):
            virtual_intf = ext_intf[interface]["virtual-interface"]
            if virtual_intf["vpci"] == vpci:
                return ext_intf[interface]["name"]

    def run_traffic(self, traffic_profile):
        client_started = multiprocessing.Value('i', 0)

        self._traffic_process = \
            multiprocessing.Process(target=self._traffic_runner,
                                    args=(traffic_profile, self._queue,
                                          client_started, self._terminated))
        self._traffic_process.start()
        # Wait for traffic process to start
        while client_started.value == 0:
            time.sleep(1)

        return self._traffic_process.is_alive()

    def _start_server(self):
        mgmt_interface = self.vnfd["mgmt-interface"]
        ssh_port = mgmt_interface.get("ssh_port", ssh.DEFAULT_PORT)
        _server = ssh.SSH(mgmt_interface["user"], mgmt_interface["ip"],
                          password=mgmt_interface["password"],
                          port=ssh_port)
        _server.wait()

        _server.execute("fuser -n tcp %s %s -k > /dev/null 2>&1" %
                        (TREX_SYNC_PORT, TREX_ASYNC_PORT))
        _server.execute("pkill -9 rex > /dev/null 2>&1")

        trex_path = os.path.join(self.bin_path, "trex/scripts")
        path = get_nsb_option("trex_path", trex_path)
        trex_cmd = "cd " + path + "; sudo ./t-rex-64 -i > /dev/null 2>&1"

        _server.execute(trex_cmd)

    def _connect_client(self):
        client = STLClient(username=self.vnfd["mgmt-interface"]["user"],
                           server=self.vnfd["mgmt-interface"]["ip"],
                           verbose_level=LoggerApi.VERBOSE_QUIET)
        time.sleep(10)
        # try to connect with 5s intervals, 30s max
        for _idx in range(6):
            try:
                client.connect()
                LOGGING.info("Connecting to Trex... Attempt %s", _idx)
                break
            except STLError:
                LOGGING.info("Failed connecting to Trex Traffic Generator")
                time.sleep(5)
        return client

    @classmethod
    def _get_rfc_tolerance(cls, tc_yaml):
        tolerance = '0.8 - 1.0'
        if 'tc_options' in tc_yaml['scenarios'][0]:
            tc_options = tc_yaml['scenarios'][0]['tc_options']
            if 'rfc2544' in tc_options:
                tolerance = \
                    tc_options['rfc2544'].get('allowed_drop_rate', '0.8 - 1.0')

        tolerance = tolerance.split('-')
        min_tol = float(tolerance[0])
        if len(tolerance) == 2:
            max_tol = float(tolerance[1])
        else:
            max_tol = float(tolerance[0])

        return [min_tol, max_tol]

    def _traffic_runner(self, traffic_profile, queue,
                        client_started, terminated):
        LOGGING.info("Starting TRex client...")
        tc_yaml = {}

        with open(self.tc_file_name) as tc_file:
            tc_yaml = yaml.load(tc_file.read())

        tolerance = self._get_rfc_tolerance(tc_yaml)

        # fixme: fix passing correct trex config file,
        # instead of searching the default path
        self.my_ports = [0, 1]
        self.client = self._connect_client()
        self.client.reset(ports=self.my_ports)
        self.client.remove_all_streams(self.my_ports)  # remove all streams
        while not terminated.value:
            traffic_profile.execute(self)
            client_started.value = 1
            time.sleep(DURATION)
            self.client.stop(self.my_ports)
            time.sleep(3)
            last_res = self.client.get_stats(self.my_ports)
            samples = {}
            for vpci_idx in range(len(self._vpci_ascending)):
                name = \
                    self._get_logical_if_name(self._vpci_ascending[vpci_idx])
                # fixme: VNFDs KPIs values needs to be mapped to TRex structure
                samples[name] = \
                    {"rx_throughput_fps": last_res[vpci_idx]["rx_pps"],
                     "tx_throughput_fps": last_res[vpci_idx]["tx_pps"],
                     "rx_throughput_mbps": last_res[vpci_idx]["rx_bps"],
                     "tx_throughput_mbps": last_res[vpci_idx]["tx_bps"],
                     "in_packets": last_res[vpci_idx]["ipackets"],
                     "out_packets": last_res[vpci_idx]["opackets"]}
            samples = \
                traffic_profile.get_drop_percentage(self, samples,
                                                    tolerance[0], tolerance[1])
            queue.put(samples)
        self.client.stop(self.my_ports)
        self.client.disconnect()
        queue.put(samples)

    def collect_kpi(self):
        if not self._queue.empty():
            result = self._queue.get()
            self._result.update(result)
        LOGGING.debug("trex collect Kpis %s", self._result)
        return self._result

    def terminate(self):
        self._terminated.value = 1  # stop Trex clinet

        self.connection.execute("fuser -n tcp %s %s -k > /dev/null 2>&1" %
                                (TREX_SYNC_PORT, TREX_ASYNC_PORT))

        if self._traffic_process:
            self._traffic_process.terminate()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(relativeCreated)6d \
                              %(threadName)s %(message)s')
    CONSOLE = logging.StreamHandler()
    CONSOLE.setLevel(logging.DEBUG)

    MOCK_SCENARIO = {}
    MOCK_CONTEXT = {}
    VNFDEN = {'benchmark': {'kpi': ['rx_throughput_fps',
                                    'tx_throughput_fps',
                                    'tx_throughput_mbps',
                                    'rx_throughput_mbps',
                                    'tx_throughput_pc_linerate',
                                    'rx_throughput_pc_linerate',
                                    'min_latency',
                                    'max_latency',
                                    'avg_latency']},
              'connection-point': [{'name': 'xe0', 'type': 'VPORT'},
                                   {'name': 'xe1', 'type': 'VPORT'}],
              'description': 'TRex stateless traffic generator for RFC2544',
              'id': 'TrexTrafficGen',
              'mgmt-interface': {'ip': '1.1.1.1',
                                 'password': 'r00t',
                                 'user': 'root',
                                 'vdu-id': 'trexgen-baremetal'},
              'name': 'trexgen',
              'short-name': 'trexgen',
              'vdu': [{'description': 'TRex stateless tg for RFC2544 tests',
                       'external-interface': [{'name': 'xe0',
                                               'virtual-interface':
                                               {'bandwidth': '10 Gbps',
                                                'dst_ip': '152.16.100.19/24',
                                                'dst_mac': '00:00:00:00:00:03',
                                                'local_ip': '152.16.100.20/24',
                                                'local_mac':
                                                '00:00:00:00:00:01',
                                                'type': 'PCI-PASSTHROUGH',
                                                'vld_id': 'private',
                                                'vpci': '0000:83:00.0'},
                                               'vnfd-connection-point-ref':
                                               'xe0'},
                                              {'name': 'xe1',
                                               'virtual-interface':
                                               {'bandwidth': '10 Gbps',
                                                'dst_ip': '152.16.40.19/24',
                                                'dst_mac': '00:00:00:00:00:04',
                                                'local_ip': '152.16.40.20/24',
                                                'local_mac':
                                                '00:00:00:00:00:02',
                                                'type': 'PCI-PASSTHROUGH',
                                                'vld_id': 'public',
                                                'vpci': '0000:83:00.1'},
                                               'vnfd-connection-point-ref':
                                               'xe1'}],
                       'id': 'trexgen-baremetal',
                       'name': 'trexgen-baremetal'}]}

    YAML_FILE = 'rfc2544_acl.yaml'
    PROFILE = 'private'
    RANDIM_FIELDS = ['private.ipv4-random.outer_l3v4.srcip4',
                     'private.ipv4.outer_l3v4.dstip4']
    DATA = yaml.load(open(YAML_FILE).read())
    TREXRFCGEN = TrexTrafficGenRFC(VNFDEN)
    TREXRFCGEN.instantiate(MOCK_SCENARIO, MOCK_CONTEXT)
    TREXRFCGEN.run_traffic(DATA)
    for index in range(10):
        kpi = TREXRFCGEN.collect_kpi()
        print(kpi)
        time.sleep(35)
    TREXRFCGEN.terminate()
