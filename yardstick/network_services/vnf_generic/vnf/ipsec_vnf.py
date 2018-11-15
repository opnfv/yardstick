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

from yardstick.benchmark.contexts.base import Context
from yardstick.common.process import check_if_process_failed
from yardstick.network_services import constants
from yardstick.network_services.helpers.cpu import CpuSysCores
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF
from yardstick.network_services.vnf_generic.vnf.vpp_helpers import \
    VppSetupEnvHelper

LOG = logging.getLogger(__name__)


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
        # TODO Implement later
        pass

    def setup_vnf_environment(self):
        resource = super(VipsecApproxSetupEnvHelper,
                         self).setup_vnf_environment()

        self.start_vpp_service()

        sys_cores = CpuSysCores(self.ssh_helper)
        self._update_vnfd_helper(sys_cores.get_cpu_layout())

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
        # TODO Implement later
        return None

    def create_ipsec_tunnels(self):
        # TODO Implement later
        pass

    def find_raw_data_interface(self):
        try:
            return self.vnfd_helper.find_virtual_interface(vld_id="uplink_0")
        except KeyError:
            return self.vnfd_helper.find_virtual_interface(vld_id="downlink_0")

    def find_encrypted_data_interface(self):
        return self.vnfd_helper.find_virtual_interface(vld_id="ciphertext")


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
