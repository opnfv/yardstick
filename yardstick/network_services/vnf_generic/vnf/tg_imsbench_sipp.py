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
import os
from collections import deque

from yardstick.network_services.vnf_generic.vnf import sample_vnf

LOG = logging.getLogger(__name__)


class SippSetupEnvHelper(sample_vnf.SetupEnvHelper):
    APP_NAME = "ImsbenchSipp"


class SippResourceHelper(sample_vnf.ClientResourceHelper):
    pass


class SippVnf(sample_vnf.SampleVNFTrafficGen):
    """
    This class calls the test script from TG machine, then gets the result file
    from IMS machine. After that, the result file is handled line by line, and
    is updated to database.
    """

    APP_NAME = "ImsbenchSipp"
    APP_WORD = "ImsbenchSipp"
    VNF_TYPE = "ImsbenchSipp"
    HW_OFFLOADING_NFVI_TYPES = {'baremetal', 'sriov'}
    RESULT = "/tmp/final_result.dat"
    SIPP_RESULT = "/tmp/sipp_dat_files/final_result.dat"
    LOCAL_PATH = "/tmp"
    CMD = "./SIPp_benchmark.bash {} {} {} '{}'"

    def __init__(self, name, vnfd, setup_env_helper_type=None,
                 resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = SippResourceHelper
        if setup_env_helper_type is None:
            setup_env_helper_type = SippSetupEnvHelper
        super(SippVnf, self).__init__(
            name, vnfd, setup_env_helper_type, resource_helper_type)
        self.params = ""
        self.pcscf_ip = self.vnfd_helper.interfaces[0]["virtual-interface"]\
            ["peer_intf"]["local_ip"]
        self.sipp_ip = self.vnfd_helper.interfaces[0]["virtual-interface"]\
            ["local_ip"]
        self.media_ip = self.vnfd_helper.interfaces[1]["virtual-interface"]\
            ["local_ip"]
        self.queue = ""
        self.count = 0

    def instantiate(self, scenario_cfg, context_cfg):
        super(SippVnf, self).instantiate(scenario_cfg, context_cfg)
        self.params = str(scenario_cfg.get("options").get("port", "5060"))+";" \
                  + str(scenario_cfg.get("options").get("start_user", "1"))+";" \
                  + str(scenario_cfg.get("options").get("end_user", "10000")) + ";" \
                  + str(scenario_cfg.get("options").get("init_reg_cps", "50")) + ";" \
                  + str(scenario_cfg.get("options").get("init_reg_max", "5000")) + ";" \
                  + str(scenario_cfg.get("options").get("reg_cps", "50")) + ";" \
                  + str(scenario_cfg.get("options").get("reg_step", "10")) + ";" \
                  + str(scenario_cfg.get("options").get("rereg_cps", "10")) + ";" \
                  + str(scenario_cfg.get("options").get("rereg_step", "5")) + ";" \
                  + str(scenario_cfg.get("options").get("dereg_cps", "10")) + ";" \
                  + str(scenario_cfg.get("options").get("dereg_step", "5")) + ";" \
                  + str(scenario_cfg.get("options").get("msgc_cps", "10")) + ";" \
                  + str(scenario_cfg.get("options").get("msgc_step", "2")) + ";" \
                  + str(scenario_cfg.get("options").get("run_mode", "rtp")) + ";" \
                  + str(scenario_cfg.get("options").get("call_cps", "10")) + ";" \
                  + str(scenario_cfg.get("options").get("hold_time", "15")) + ";" \
                  + str(scenario_cfg.get("options").get("call_step", "5"))

    def wait_for_instantiate(self):
        pass

    def get_result_files(self):
        self.ssh_helper.get(self.SIPP_RESULT, self.LOCAL_PATH, True)

    # Example of result file:
    # cat /tmp/final_result.dat
    #   timestamp:1000 reg:100 reg_saps:0
    #   timestamp:2000 reg:100 reg_saps:50
    #   timestamp:3000 reg:100 reg_saps:50
    #   timestamp:4000 reg:100 reg_saps:50
    #   ...
    #   reg_Requested_prereg:50
    #   reg_Effective_prereg:49.49
    #   reg_DOC:0
    #   ...
    @staticmethod
    def handle_result_files(filename):
        with open(filename, 'r') as f:
            content = f.readlines()
        result = [{k: v for k, v in [i.split(":", 1) for i in x.split()]}
                  for x in content if x]
        return deque(result)

    def run_traffic(self, traffic_profile):
        traffic_profile.execute_traffic(self)
        cmd = self.CMD.format(self.sipp_ip, self.media_ip,
                              self.pcscf_ip, self.params)
        self.ssh_helper.execute(cmd, None, 3600, False)
        self.get_result_files()
        self.queue = self.handle_result_files(self.RESULT)

    def collect_kpi(self):
        result = {}

        if self.queue:
            result = dict(self.queue.popleft())
        return result

    @staticmethod
    def count_line_num(fname):
        if os.path.getsize(fname) > 0:
            with open(fname, 'r') as f:
                return sum(1 for x in f)
        return 0

    def is_ended(self):
        """
        The test will end when the results are pushed into database.
        It does not depend on the "duration" value, so this value will be set
        enough big to make sure that the test will end before duration.
        """
        num_lines = self.count_line_num(self.RESULT)
        if self.count == num_lines:
            LOG.debug('TG IS ENDED.....................')
            self.count = 0
            return True
        self.count += 1
        return False

    def terminate(self):
        LOG.debug('TERMINATE:.....................')
        self.resource_helper.terminate()
