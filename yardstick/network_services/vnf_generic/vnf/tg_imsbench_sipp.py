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

    APP_NAME = "ImsbenchSipp"
    APP_WORD = "ImsbenchSipp"
    VNF_TYPE = "ImsbenchSipp"
    HW_OFFLOADING_NFVI_TYPES = {'baremetal', 'sriov'}
    RESULT = "/root/final_result.dat"
    SIPP_RESULT = "/root/sipp_dat_files/final_result.dat"
    LOCAL_PATH = "/root"
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
        self.params = str(scenario_cfg.get("options").get("port"))+";" \
                  + str(scenario_cfg.get("options").get("start_user"))+";" \
                  + str(scenario_cfg.get("options").get("end_user")) + ";" \
                  + str(scenario_cfg.get("options").get("init_reg_cps")) + ";" \
                  + str(scenario_cfg.get("options").get("init_reg_max")) + ";" \
                  + str(scenario_cfg.get("options").get("reg_cps")) + ";" \
                  + str(scenario_cfg.get("options").get("reg_step")) + ";" \
                  + str(scenario_cfg.get("options").get("rereg_cps")) + ";" \
                  + str(scenario_cfg.get("options").get("rereg_step")) + ";" \
                  + str(scenario_cfg.get("options").get("dereg_cps")) + ";" \
                  + str(scenario_cfg.get("options").get("dereg_step")) + ";" \
                  + str(scenario_cfg.get("options").get("msgc_cps")) + ";" \
                  + str(scenario_cfg.get("options").get("msgc_step")) + ";" \
                  + str(scenario_cfg.get("options").get("run_mode")) + ";" \
                  + str(scenario_cfg.get("options").get("call_cps")) + ";" \
                  + str(scenario_cfg.get("options").get("hold_time")) + ";" \
                  + str(scenario_cfg.get("options").get("call_step"))

    def wait_for_instantiate(self):
        pass

    def get_result_files(self):
        self.ssh_helper.get(self.SIPP_RESULT, self.LOCAL_PATH, True)

    @staticmethod
    def handle_result_files(file):
        result_list = []
        queue = deque(result_list)
        with open(file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                d = {}
                for x in line.split():
                    try:
                        key, value = x.strip().split(':')
                    except ValueError:
                        continue
                    d[key] = round(float(value), 2)
                queue.append(d)
        return queue

    def run_traffic(self, traffic_profile):
        traffic_profile.execute_traffic(self)
        cmd = self.CMD.format(self.sipp_ip, self.media_ip,
                              self.pcscf_ip, self.params)
        self.ssh_helper.execute(cmd, None, 3600, False)
        self.get_result_files()

    def collect_kpi(self):
        result = {}
        test = self.handle_result_files(self.RESULT)
        if test:
            result = dict(test.popleft())
        return result

    @staticmethod
    def count_line_num(fname):
        i = ((),)
        if os.path.getsize(fname) > 0:
            with open(fname, 'r') as f:
                for i in enumerate(f):
                    pass
                return i[0] + 1
        else:
            return 0

    def is_ended(self):
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
