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
import time

from yardstick.network_services.vnf_generic.vnf import sample_vnf

LOG = logging.getLogger(__name__)


class VimsSetupEnvHelper(sample_vnf.SetupEnvHelper):

    def setup_vnf_environment(self):
        LOG.debug('VimsSetupEnvHelper:\n')


class VimsResourceHelper(sample_vnf.ClientResourceHelper):
    pass


class VimsPcscfVnf(sample_vnf.SampleVNF):

    APP_NAME = "VimsPcscf"
    APP_WORD = "VimsPcscf"

    def __init__(self, name, vnfd, setup_env_helper_type=None,
                 resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = VimsResourceHelper
        if setup_env_helper_type is None:
            setup_env_helper_type = VimsSetupEnvHelper
        super(VimsPcscfVnf, self).__init__(name, vnfd, setup_env_helper_type,
                                           resource_helper_type)

    def wait_for_instantiate(self):
        pass

    def _run(self):
        pass

    def start_collect(self):
        # TODO
        pass

    def collect_kpi(self):
        # TODO
        pass


class VimsHssVnf(sample_vnf.SampleVNF):

    APP_NAME = "VimsHss"
    APP_WORD = "VimsHss"
    CMD = "sudo /media/generate_user.sh {} {} >> /dev/null 2>&1"

    def __init__(self, name, vnfd, setup_env_helper_type=None,
                 resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = VimsResourceHelper
        if setup_env_helper_type is None:
            setup_env_helper_type = VimsSetupEnvHelper
        super(VimsHssVnf, self).__init__(name, vnfd, setup_env_helper_type,
                                         resource_helper_type)
        self.start_user = 1
        self.end_user = 10000

    def instantiate(self, scenario_cfg, context_cfg):
        LOG.debug("scenario_cfg=%s\n", scenario_cfg)
        self.start_user = scenario_cfg.get("options").get("start_user")
        self.end_user = scenario_cfg.get("options").get("end_user")
        # TODO
        # Need to check HSS services are ready before generating user accounts
        # Now, adding time sleep that manually configured by user
        # to wait for HSS services.
        self.WAIT_TIME = scenario_cfg.get("options").get("wait_time")
        time.sleep(self.WAIT_TIME)
        LOG.debug("Generate user accounts from %d to %d\n",
                  self.start_user, self.end_user)
        cmd = self.CMD.format(self.start_user, self.end_user)
        self.ssh_helper.execute(cmd, None, 3600, False)

    def wait_for_instantiate(self):
        pass

    def start_collect(self):
        # TODO
        pass

    def collect_kpi(self):
        # TODO
        pass
