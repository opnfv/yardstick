# Copyright (c) 2019 Viosoft Corporation
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
import re
import time
from collections import Counter
from enum import Enum

from yardstick.benchmark.contexts.base import Context
from yardstick.common.process import check_if_process_failed
from yardstick.network_services import constants
from yardstick.network_services.helpers.cpu import CpuSysCores
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF
from yardstick.network_services.vnf_generic.vnf.vpp_helpers import \
    VppSetupEnvHelper, VppConfigGenerator

LOG = logging.getLogger(__name__)


class CryptoAlg(Enum):
    """Encryption algorithms."""
    AES_CBC_128 = ('aes-cbc-128', 'AES-CBC', 16)
    AES_CBC_192 = ('aes-cbc-192', 'AES-CBC', 24)
    AES_CBC_256 = ('aes-cbc-256', 'AES-CBC', 32)
    AES_GCM_128 = ('aes-gcm-128', 'AES-GCM', 20)

    def __init__(self, alg_name, scapy_name, key_len):
        self.alg_name = alg_name
        self.scapy_name = scapy_name
        self.key_len = key_len


class IntegAlg(Enum):
    """Integrity algorithms."""
    SHA1_96 = ('sha1-96', 'HMAC-SHA1-96', 20)
    SHA_256_128 = ('sha-256-128', 'SHA2-256-128', 32)
    SHA_384_192 = ('sha-384-192', 'SHA2-384-192', 48)
    SHA_512_256 = ('sha-512-256', 'SHA2-512-256', 64)
    AES_GCM_128 = ('aes-gcm-128', 'AES-GCM', 20)

    def __init__(self, alg_name, scapy_name, key_len):
        self.alg_name = alg_name
        self.scapy_name = scapy_name
        self.key_len = key_len


class VipsecApproxSetupEnvHelper(VppSetupEnvHelper):
    DEFAULT_IPSEC_VNF_CFG = {
        'crypto_type': 'SW_cryptodev',
        'rxq': 1,
        'worker_config': '1C/1T',
        'worker_threads': 1,
    }

    def __init__(self, vnfd_helper, ssh_helper, scenario_helper):
        super(VipsecApproxSetupEnvHelper, self).__init__(
            vnfd_helper, ssh_helper, scenario_helper)

    def _get_crypto_type(self):
        vnf_cfg = self.scenario_helper.options.get('vnf_config',
                                                   self.DEFAULT_IPSEC_VNF_CFG)
        return vnf_cfg.get('crypto_type', 'SW_cryptodev')

    def _get_crypto_algorithms(self):
        vpp_cfg = self.scenario_helper.all_options.get('vpp_config', {})
        return vpp_cfg.get('crypto_algorithms', 'aes-gcm')

    def _get_n_tunnels(self):
        vpp_cfg = self.scenario_helper.all_options.get('vpp_config', {})
        return vpp_cfg.get('tunnels', 1)

    def _get_n_connections(self):
        try:
            flow_cfg = self.scenario_helper.all_options['flow']
            return flow_cfg['count']
        except KeyError:
            raise KeyError("Missing flow definition in scenario section" +
                           " of the task definition file")

    def _get_flow_src_start_ip(self):
        node_name = self.find_encrypted_data_interface()["node_name"]
        try:
            flow_cfg = self.scenario_helper.all_options['flow']
            src_ips = flow_cfg['src_ip']
            dst_ips = flow_cfg['dst_ip']
        except KeyError:
            raise KeyError("Missing flow definition in scenario section" +
                           " of the task definition file")

        for src, dst in zip(src_ips, dst_ips):
            flow_src_start_ip, _ = src.split('-')
            flow_dst_start_ip, _ = dst.split('-')

            if node_name == "vnf__0":
                return flow_src_start_ip
            elif node_name == "vnf__1":
                return flow_dst_start_ip

    def _get_flow_dst_start_ip(self):
        node_name = self.find_encrypted_data_interface()["node_name"]
        try:
            flow_cfg = self.scenario_helper.all_options['flow']
            src_ips = flow_cfg['src_ip']
            dst_ips = flow_cfg['dst_ip']
        except KeyError:
            raise KeyError("Missing flow definition in scenario section" +
                           " of the task definition file")

        for src, dst in zip(src_ips, dst_ips):
            flow_src_start_ip, _ = src.split('-')
            flow_dst_start_ip, _ = dst.split('-')

            if node_name == "vnf__0":
                return flow_dst_start_ip
            elif node_name == "vnf__1":
                return flow_src_start_ip

    def build_config(self):
        vnf_cfg = self.scenario_helper.options.get('vnf_config',
                                                   self.DEFAULT_IPSEC_VNF_CFG)
        rxq = vnf_cfg.get('rxq', 1)
        phy_cores = vnf_cfg.get('worker_threads', 1)
        # worker_config = vnf_cfg.get('worker_config', '1C/1T').split('/')[1].lower()

        vpp_cfg = self.create_startup_configuration_of_vpp()
        self.add_worker_threads_and_rxqueues(vpp_cfg, phy_cores, rxq)
        self.add_pci_devices(vpp_cfg)

        frame_size_cfg = self.scenario_helper.all_options.get('framesize', {})
        uplink_cfg = frame_size_cfg.get('uplink', {})
        downlink_cfg = frame_size_cfg.get('downlink', {})
        framesize = min(self.calculate_frame_size(uplink_cfg),
                        self.calculate_frame_size(downlink_cfg))
        if framesize < 1522:
            vpp_cfg.add_dpdk_no_multi_seg()

        crypto_algorithms = self._get_crypto_algorithms()
        if crypto_algorithms == 'aes-gcm':
            self.add_dpdk_cryptodev(vpp_cfg, 'aesni_gcm', phy_cores)
        elif crypto_algorithms == 'cbc-sha1':
            self.add_dpdk_cryptodev(vpp_cfg, 'aesni_mb', phy_cores)

        vpp_cfg.add_dpdk_dev_default_rxd(2048)
        vpp_cfg.add_dpdk_dev_default_txd(2048)
        self.apply_config(vpp_cfg, True)
        self.update_vpp_interface_data()

    def setup_vnf_environment(self):
        resource = super(VipsecApproxSetupEnvHelper,
                         self).setup_vnf_environment()

        self.start_vpp_service()

        sys_cores = CpuSysCores(self.ssh_helper)
        self._update_vnfd_helper(sys_cores.get_cpu_layout())
        self.update_vpp_interface_data()
        self.iface_update_numa()

        return resource

    @staticmethod
    def calculate_frame_size(frame_cfg):
        if not frame_cfg:
            return 64

        imix_count = {size.upper().replace('B', ''): int(weight)
                      for size, weight in frame_cfg.items()}
        imix_sum = sum(imix_count.values())
        if imix_sum <= 0:
            return 64
        packets_total = sum([int(size) * weight
                             for size, weight in imix_count.items()])
        return packets_total / imix_sum

    def check_status(self):
        ipsec_created = False
        cmd = "vppctl show int"
        _, stdout, _ = self.ssh_helper.execute(cmd)
        entries = re.split(r"\n+", stdout)
        tmp = [re.split(r"\s\s+", entry, 5) for entry in entries]

        for item in tmp:
            if isinstance(item, list):
                if item[0] and item[0] != 'local0':
                    if "ipsec" in item[0] and not ipsec_created:
                        ipsec_created = True
                    if len(item) > 2 and item[2] == 'down':
                        return False
        return ipsec_created

    def get_vpp_statistics(self):
        cmd = "vppctl show int {intf}"
        result = {}
        for interface in self.vnfd_helper.interfaces:
            iface_name = self.get_value_by_interface_key(
                interface["virtual-interface"]["ifname"], "vpp_name")
            command = cmd.format(intf=iface_name)
            _, stdout, _ = self.ssh_helper.execute(command)
            result.update(
                self.parser_vpp_stats(interface["virtual-interface"]["ifname"],
                                      iface_name, stdout))
        self.ssh_helper.execute("vppctl clear interfaces")
        return result

    @staticmethod
    def parser_vpp_stats(interface, iface_name, stats):
        packets_in = 0
        packets_fwd = 0
        packets_dropped = 0
        result = {}

        entries = re.split(r"\n+", stats)
        tmp = [re.split(r"\s\s+", entry, 5) for entry in entries]

        for item in tmp:
            if isinstance(item, list):
                if item[0] == iface_name and len(item) >= 5:
                    if item[3] == 'rx packets':
                        packets_in = int(item[4])
                    elif item[4] == 'rx packets':
                        packets_in = int(item[5])
                elif len(item) == 3:
                    if item[1] == 'tx packets':
                        packets_fwd = int(item[2])
                    elif item[1] == 'drops' or item[1] == 'rx-miss':
                        packets_dropped = int(item[2])
        if packets_dropped == 0 and packets_in > 0 and packets_fwd > 0:
            packets_dropped = abs(packets_fwd - packets_in)

        result[interface] = {
            'packets_in': packets_in,
            'packets_fwd': packets_fwd,
            'packets_dropped': packets_dropped,
        }

        return result

    def create_ipsec_tunnels(self):
        self.initialize_ipsec()

        # TODO generate the same key
        crypto_algorithms = self._get_crypto_algorithms()
        if crypto_algorithms == 'aes-gcm':
            encr_alg = CryptoAlg.AES_GCM_128
            auth_alg = IntegAlg.AES_GCM_128
            encr_key = 'LNYZXMBQDKESNLREHJMS'
            auth_key = 'SWGLDTYZSQKVBZZMPIEV'
        elif crypto_algorithms == 'cbc-sha1':
            encr_alg = CryptoAlg.AES_CBC_128
            auth_alg = IntegAlg.SHA1_96
            encr_key = 'IFEMSHYLCZIYFUTT'
            auth_key = 'PEALEIPSCPTRHYJSDXLY'

        self.execute_script("enable_dpdk_traces.vat", json_out=False)
        self.execute_script("enable_vhost_user_traces.vat", json_out=False)
        self.execute_script("enable_memif_traces.vat", json_out=False)

        node_name = self.find_encrypted_data_interface()["node_name"]
        n_tunnels = self._get_n_tunnels()
        n_connections = self._get_n_connections()
        flow_dst_start_ip = self._get_flow_dst_start_ip()
        if node_name == "vnf__0":
            self.vpp_create_ipsec_tunnels(
                self.find_encrypted_data_interface()["local_ip"],
                self.find_encrypted_data_interface()["peer_intf"]["local_ip"],
                self.find_encrypted_data_interface()["ifname"],
                n_tunnels, n_connections, encr_alg, encr_key, auth_alg,
                auth_key, flow_dst_start_ip)
        elif node_name == "vnf__1":
            self.vpp_create_ipsec_tunnels(
                self.find_encrypted_data_interface()["local_ip"],
                self.find_encrypted_data_interface()["peer_intf"]["local_ip"],
                self.find_encrypted_data_interface()["ifname"],
                n_tunnels, n_connections, encr_alg, encr_key, auth_alg,
                auth_key, flow_dst_start_ip, 20000, 10000)

    def find_raw_data_interface(self):
        try:
            return self.vnfd_helper.find_virtual_interface(vld_id="uplink_0")
        except KeyError:
            return self.vnfd_helper.find_virtual_interface(vld_id="downlink_0")

    def find_encrypted_data_interface(self):
        return self.vnfd_helper.find_virtual_interface(vld_id="ciphertext")

    def create_startup_configuration_of_vpp(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_unix_log()
        vpp_config_generator.add_unix_cli_listen()
        vpp_config_generator.add_unix_nodaemon()
        vpp_config_generator.add_unix_coredump()
        vpp_config_generator.add_dpdk_socketmem('1024,1024')
        vpp_config_generator.add_dpdk_no_tx_checksum_offload()
        vpp_config_generator.add_dpdk_log_level('debug')
        for interface in self.vnfd_helper.interfaces:
            vpp_config_generator.add_dpdk_uio_driver(
                interface["virtual-interface"]["driver"])
        vpp_config_generator.add_heapsize('4G')
        # TODO Enable configuration depend on VPP version
        vpp_config_generator.add_statseg_size('4G')
        vpp_config_generator.add_plugin('disable', ['default'])
        vpp_config_generator.add_plugin('enable', ['dpdk_plugin.so'])
        vpp_config_generator.add_ip6_hash_buckets('2000000')
        vpp_config_generator.add_ip6_heap_size('4G')
        vpp_config_generator.add_ip_heap_size('4G')
        return vpp_config_generator

    def add_worker_threads_and_rxqueues(self, vpp_cfg, phy_cores,
                                        rx_queues=None):
        thr_count_int = phy_cores
        cpu_count_int = phy_cores
        num_mbufs_int = 32768

        numa_list = []

        if_list = [self.find_encrypted_data_interface()["ifname"],
                   self.find_raw_data_interface()["ifname"]]
        for if_key in if_list:
            try:
                numa_list.append(
                    self.get_value_by_interface_key(if_key, 'numa_node'))
            except KeyError:
                pass
        numa_cnt_mc = Counter(numa_list).most_common()

        if numa_cnt_mc and numa_cnt_mc[0][0] is not None and \
                numa_cnt_mc[0][0] != -1:
            numa = numa_cnt_mc[0][0]
        elif len(numa_cnt_mc) > 1 and numa_cnt_mc[0][0] == -1:
            numa = numa_cnt_mc[1][0]
        else:
            numa = 0

        try:
            smt_used = CpuSysCores.is_smt_enabled(self.vnfd_helper['cpuinfo'])
        except KeyError:
            smt_used = False

        cpu_main = CpuSysCores.cpu_list_per_node_str(self.vnfd_helper, numa,
                                                     skip_cnt=1, cpu_cnt=1)
        cpu_wt = CpuSysCores.cpu_list_per_node_str(self.vnfd_helper, numa,
                                                   skip_cnt=2,
                                                   cpu_cnt=cpu_count_int,
                                                   smt_used=smt_used)

        if smt_used:
            thr_count_int = 2 * cpu_count_int

        if rx_queues is None:
            rxq_count_int = int(thr_count_int / 2)
        else:
            rxq_count_int = rx_queues

        if rxq_count_int == 0:
            rxq_count_int = 1

        num_mbufs_int = num_mbufs_int * rxq_count_int

        vpp_cfg.add_cpu_main_core(cpu_main)
        vpp_cfg.add_cpu_corelist_workers(cpu_wt)
        vpp_cfg.add_dpdk_dev_default_rxq(rxq_count_int)
        vpp_cfg.add_dpdk_num_mbufs(num_mbufs_int)

    def add_pci_devices(self, vpp_cfg):
        pci_devs = [self.find_encrypted_data_interface()["vpci"],
                    self.find_raw_data_interface()["vpci"]]
        vpp_cfg.add_dpdk_dev(*pci_devs)

    def add_dpdk_cryptodev(self, vpp_cfg, sw_pmd_type, count):
        crypto_type = self._get_crypto_type()
        smt_used = CpuSysCores.is_smt_enabled(self.vnfd_helper['cpuinfo'])
        cryptodev = self.find_encrypted_data_interface()["vpci"]
        socket_id = self.get_value_by_interface_key(
            self.find_encrypted_data_interface()["ifname"], "numa_node")

        if smt_used:
            thr_count_int = count * 2
            if crypto_type == 'HW_cryptodev':
                vpp_cfg.add_dpdk_cryptodev(thr_count_int, cryptodev)
            else:
                vpp_cfg.add_dpdk_sw_cryptodev(sw_pmd_type, socket_id,
                                              thr_count_int)
        else:
            thr_count_int = count
            if crypto_type == 'HW_cryptodev':
                vpp_cfg.add_dpdk_cryptodev(thr_count_int, cryptodev)
            else:
                vpp_cfg.add_dpdk_sw_cryptodev(sw_pmd_type, socket_id,
                                              thr_count_int)

    def initialize_ipsec(self):
        flow_src_start_ip = self._get_flow_src_start_ip()

        self.set_interface_state(
            self.find_encrypted_data_interface()["ifname"], 'up')
        self.set_interface_state(self.find_raw_data_interface()["ifname"],
                                 'up')
        self.vpp_interfaces_ready_wait()
        self.vpp_set_interface_mtu(
            self.find_encrypted_data_interface()["ifname"])
        self.vpp_set_interface_mtu(self.find_raw_data_interface()["ifname"])
        self.vpp_interfaces_ready_wait()

        self.set_ip(self.find_encrypted_data_interface()["ifname"],
                    self.find_encrypted_data_interface()["local_ip"], 24)
        self.set_ip(self.find_raw_data_interface()["ifname"],
                    self.find_raw_data_interface()["local_ip"],
                    24)

        self.add_arp_on_dut(self.find_encrypted_data_interface()["ifname"],
                            self.find_encrypted_data_interface()["peer_intf"][
                                "local_ip"],
                            self.find_encrypted_data_interface()["peer_intf"][
                                "local_mac"])
        self.add_arp_on_dut(self.find_raw_data_interface()["ifname"],
                            self.find_raw_data_interface()["peer_intf"][
                                "local_ip"],
                            self.find_raw_data_interface()["peer_intf"][
                                "local_mac"])

        self.vpp_route_add(flow_src_start_ip, 8,
                           self.find_raw_data_interface()["peer_intf"][
                               "local_ip"],
                           self.find_raw_data_interface()["ifname"])


class VipsecApproxVnf(SampleVNF):
    """ This class handles vIPSEC VNF model-driver definitions """

    APP_NAME = 'vIPSEC'
    APP_WORD = 'vipsec'
    WAIT_TIME = 20

    def __init__(self, name, vnfd, setup_env_helper_type=None,
                 resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = VipsecApproxSetupEnvHelper
        super(VipsecApproxVnf, self).__init__(
            name, vnfd, setup_env_helper_type,
            resource_helper_type)

    def _run(self):
        # we can't share ssh paramiko objects to force new connection
        self.ssh_helper.drop_connection()
        # kill before starting
        self.setup_helper.kill_vnf()
        self._build_config()
        self.setup_helper.create_ipsec_tunnels()

    def wait_for_instantiate(self):
        time.sleep(self.WAIT_TIME)
        while True:
            status = self.setup_helper.check_status()
            if not self._vnf_process.is_alive() and not status:
                raise RuntimeError("%s VNF process died." % self.APP_NAME)
            LOG.info("Waiting for %s VNF to start.. ", self.APP_NAME)
            time.sleep(self.WAIT_TIME_FOR_SCRIPT)
            status = self.setup_helper.check_status()
            if status:
                LOG.info("%s VNF is up and running.", self.APP_NAME)
                self._vnf_up_post()
                return self._vnf_process.exitcode

    def terminate(self):
        self.setup_helper.kill_vnf()
        self._tear_down()
        self.resource_helper.stop_collect()
        if self._vnf_process is not None:
            # be proper and join first before we kill
            LOG.debug("joining before terminate %s", self._vnf_process.name)
            self._vnf_process.join(constants.PROCESS_JOIN_TIMEOUT)
            self._vnf_process.terminate()

    def collect_kpi(self):
        # we can't get KPIs if the VNF is down
        check_if_process_failed(self._vnf_process, 0.01)
        physical_node = Context.get_physical_node_from_server(
            self.scenario_helper.nodes[self.name])
        result = {"physical_node": physical_node}
        result["collect_stats"] = self.setup_helper.get_vpp_statistics()
        LOG.debug("%s collect KPIs %s", self.APP_NAME, result)
        return result
