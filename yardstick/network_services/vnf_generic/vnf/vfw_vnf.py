# Copyright (c) 2016-2019 Intel Corporation
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

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF
from yardstick.network_services.vnf_generic.vnf.acl_vnf import AclApproxSetupEnvSetupEnvHelper

LOG = logging.getLogger(__name__)

# vFW should work the same on all systems, we can provide the binary
FW_PIPELINE_COMMAND = "sudo {tool_path} -p {port_mask_hex} -f {cfg_file} -s {script} {hwlb}"

FW_COLLECT_KPI = (r"""VFW TOTAL:[^p]+pkts_received"?:\s(\d+),[^p]+pkts_fw_forwarded"?:\s(\d+),"""
                  r"""[^p]+pkts_drop_fw"?:\s(\d+),\s""")


class FWApproxSetupEnvHelper(AclApproxSetupEnvSetupEnvHelper):

    APP_NAME = "vFW"
    CFG_CONFIG = "/tmp/vfw_config"
    CFG_SCRIPT = "/tmp/vfw_script"
    DEFAULT_CONFIG_TPL_CFG = "vfw.cfg"
    PIPELINE_COMMAND = FW_PIPELINE_COMMAND
    SW_DEFAULT_CORE = 5
    HW_DEFAULT_CORE = 2
    VNF_TYPE = "VFW"
    RULE_CMD = "vfw"
    DEFAULT_FWD_ACTIONS = ["accept", "count", "conntrack"]


class FWApproxVnf(SampleVNF):

    APP_NAME = "vFW"
    APP_WORD = 'vfw'
    COLLECT_KPI = FW_COLLECT_KPI

    COLLECT_MAP = {
        'packets_in': 1,
        'packets_fwd': 2,
        'packets_dropped': 3,
    }

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = FWApproxSetupEnvHelper

        super(FWApproxVnf, self).__init__(name, vnfd, setup_env_helper_type, resource_helper_type)

    def wait_for_instantiate(self):
        """Wait for VNF to initialize"""
        self.wait_for_initialize()
