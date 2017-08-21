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
from __future__ import print_function
import logging

from yardstick.benchmark.scenarios.networking.vnf_generic import find_relative_file
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF, DpdkVnfSetupEnvHelper
from yardstick.network_services.yang_model import YangModel

LOG = logging.getLogger(__name__)

# ACL should work the same on all systems, we can provide the binary
ACL_PIPELINE_COMMAND = \
    'sudo {tool_path} -p {ports_len_hex} -f {cfg_file} -s {script}'

ACL_COLLECT_KPI = r"""\
ACL TOTAL:[^p]+pkts_processed"?:\s(\d+),[^p]+pkts_drop"?:\s(\d+),[^p]+pkts_received"?:\s(\d+),"""


class AclApproxSetupEnvSetupEnvHelper(DpdkVnfSetupEnvHelper):

    APP_NAME = "vACL"
    CFG_CONFIG = "/tmp/acl_config"
    CFG_SCRIPT = "/tmp/acl_script"
    PIPELINE_COMMAND = ACL_PIPELINE_COMMAND
    HW_DEFAULT_CORE = 2
    SW_DEFAULT_CORE = 5
    DEFAULT_CONFIG_TPL_CFG = "acl.cfg"
    VNF_TYPE = "ACL"


class AclApproxVnf(SampleVNF):

    APP_NAME = "vACL"
    APP_WORD = 'acl'
    COLLECT_KPI = ACL_COLLECT_KPI

    COLLECT_MAP = {
        'packets_in': 3,
        'packets_fwd': 1,
        'packets_dropped': 2,
    }

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = AclApproxSetupEnvSetupEnvHelper

        super(AclApproxVnf, self).__init__(name, vnfd, setup_env_helper_type, resource_helper_type)
        self.acl_rules = None

    def scale(self, flavor=""):
        raise NotImplementedError

    def _start_vnf(self):
        yang_model_path = find_relative_file(self.scenario_helper.options['rules'],
                                             self.scenario_helper.task_path)
        yang_model = YangModel(yang_model_path)
        self.acl_rules = yang_model.get_rules()
        super(AclApproxVnf, self)._start_vnf()
