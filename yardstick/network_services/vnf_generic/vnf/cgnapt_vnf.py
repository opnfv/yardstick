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

from __future__ import absolute_import
import time
import logging

from six.moves import zip
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF, DpdkVnfSetupEnvHelper

LOG = logging.getLogger(__name__)

# CGNAPT should work the same on all systems, we can provide the binary
CGNAPT_PIPELINE_COMMAND = 'sudo {tool_path} -p {ports_len_hex} -f {cfg_file} -s {script}'
WAIT_FOR_STATIC_NAPT = 4

CGNAPT_COLLECT_KPI = """\
CG-NAPT(.*\n)*\
Received\s(\d+),\
Missed\s(\d+),\
Dropped\s(\d+),\
Translated\s(\d+),\
ingress\
"""


class CgnaptApproxSetupEnvHelper(DpdkVnfSetupEnvHelper):

    APP_NAME = "vCGNAPT"
    CFG_CONFIG = "/tmp/cgnapt_config"
    CFG_SCRIPT = "/tmp/cgnapt_script"
    DEFAULT_CONFIG_TPL_CFG = "cgnat.cfg"
    PIPELINE_COMMAND = CGNAPT_PIPELINE_COMMAND
    SW_DEFAULT_CORE = 6
    HW_DEFAULT_CORE = 3
    VNF_TYPE = "CGNAPT"

    @staticmethod
    def _generate_ip_from_pool(ip):
        ip_parts = ip.split('.')
        assert len(ip_parts) == 4
        iter1 = (str(n) for n in range(int(ip_parts[2]), 256))
        for ip_parts[2] in iter1:
            yield '.'.join(ip_parts)

    @staticmethod
    def _update_cgnat_script_file(ip_pipeline_cfg, mcpi, vnf_str):
        pipeline_config_str = str(ip_pipeline_cfg)
        input_cmds = '\n'.join(mcpi)
        icmp_flag = 'link 0 down' in input_cmds
        if icmp_flag:
            pipeline_config_str = ''
        return '\n'.join([pipeline_config_str, input_cmds])

    def scale(self, flavor=""):
        raise NotImplementedError

    def _get_cgnapt_config(self, interfaces=None):
        if interfaces is None:
            interfaces = self.vnfd_helper.interfaces

        gateway_ips = []

        # fixme: Get private port and gateway from port list
        priv_ports = interfaces[::2]
        for interface in priv_ports:
            gateway_ips.append(self._get_ports_gateway(interface["name"]))
        return gateway_ips


class CgnaptApproxVnf(SampleVNF):

    APP_NAME = "vCGNAPT"
    APP_WORD = 'cgnapt'
    COLLECT_KPI = CGNAPT_COLLECT_KPI

    COLLECT_MAP = {
        "packets_in": 2,
        "packets_fwd": 5,
        "packets_dropped": 4,
    }

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = CgnaptApproxSetupEnvHelper

        super(CgnaptApproxVnf, self).__init__(name, vnfd, setup_env_helper_type,
                                              resource_helper_type)

    def _vnf_up_post(self):
        super(CgnaptApproxVnf, self)._vnf_up_post()
        if self.scenario_helper.options.get('napt', 'static') != 'static':
            return

        ip_iter = self.setup_helper._generate_ip_from_pool("152.16.40.10")
        gw_ips = self.setup_helper._get_cgnapt_config()
        if self.scenario_helper.vnf_cfg.get("lb_config", "SW") == 'HW':
            pipeline = self.setup_helper.HW_DEFAULT_CORE
            offset = 3
        else:
            pipeline = self.setup_helper.SW_DEFAULT_CORE - 1
            offset = 0

        worker_threads = int(self.scenario_helper.vnf_cfg["worker_threads"])
        cmd_template = "p {0} entry addm {1} 1 {2} 1 0 32 65535 65535 65535"
        for gw, ip in zip(gw_ips, ip_iter):
            cmd = cmd_template.format(pipeline, gw, ip)
            pipeline += worker_threads
            pipeline += offset
            self.vnf_execute(cmd)

        time.sleep(WAIT_FOR_STATIC_NAPT)
