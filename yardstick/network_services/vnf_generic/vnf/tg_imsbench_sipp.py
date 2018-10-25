# Copyright (c) 2018 Viosoft Corporation
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
import logging
import time
from collections import deque

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper

LOG = logging.getLogger(__name__)

class SippSetupEnvHelper(SetupEnvHelper):
    APP_NAME = "ImsbenchSipp"

class SippResourceHelper(ClientResourceHelper):
    pass

class SippVnf(SampleVNFTrafficGen):

    APP_NAME = "ImsbenchSipp"
    APP_WORD = "ImsbenchSipp"
    VNF_TYPE = 'ImsbenchSipp'
    HW_OFFLOADING_NFVI_TYPES = {'baremetal', 'sriov'}
    WAIT_TIME = 60
    RESULT = "/tmp/final_result.dat"
    SIPP_RESULT = "/tmp/sipp_dat_files/final_result.dat"
    CMD = "./SIPp_benchmark.bash {} {} {} '{}'"

    def __init__(self, name, vnfd, task_id, setup_env_helper_type=None,
                 resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = SippResourceHelper
        if setup_env_helper_type is None:
            setup_env_helper_type = SippSetupEnvHelper
        super(SippVnf, self).__init__(
            name, vnfd, task_id, setup_env_helper_type, resource_helper_type)
        self.timestamp = 0
        self.params = ""
        self.influxdb_url = ""
        pcscf_intf = self.vnfd_helper.interfaces[0]["virtual-interface"]["peer_intf"]["vnf__0"]
        self.pcscf_ip = pcscf_intf["local_ip"]
        self.sipp_ip = self.vnfd_helper.interfaces[0]["virtual-interface"]["local_ip"]
        self.media_ip = self.vnfd_helper.interfaces[1]["virtual-interface"]["local_ip"]
        self.results = ""
        self.queue = ""
    def instantiate(self, scenario_cfg, context_cfg):
        super(SippVnf, self).instantiate(scenario_cfg, context_cfg)
        self.params = str(scenario_cfg.get("options").get("port"))+";"	\
                      + str(scenario_cfg.get("options").get("start_user"))+";"	\
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
                      + scenario_cfg.get("options").get("run_mode") + ";" \
                      + str(scenario_cfg.get("options").get("call_cps")) + ";" \
                      + str(scenario_cfg.get("options").get("hold_time")) + ";" \
		      + str(scenario_cfg.get("options").get("call_step"))

    def wait_for_instantiate(self):
        time.sleep(self.WAIT_TIME)

    def _get_result_files(self):
        self.ssh_helper.get(self.SIPP_RESULT, '/tmp/', True)

    def _handle_result_files(self):
        result_list = []
        self.queue = deque(result_list)
        with open(self.RESULT, 'r') as f:
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
                self.queue.append(d)

    def run_traffic(self, traffic_profile):
        time.sleep(self.WAIT_TIME)
        cmd = self.CMD.format(self.sipp_ip, self.media_ip, self.pcscf_ip, self.params)
        self.ssh_helper.execute(cmd, None, 3600, False)
        self._get_result_files()
        self.results = self._handle_result_files()

    def collect_kpi(self):
        result = {}
        if self.queue:
            result = dict(self.queue.popleft())
        return result

    def terminate(self):
        LOG.debug('TERMINATE:.....................')
