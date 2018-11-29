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

import logging
import yaml
import os

from multiprocessing import Queue

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ScenarioHelper
from yardstick.network_services.vnf_generic.vnf.vnf_ssh_helper import VnfSshHelper
from yardstick.network_services.utils import get_nsb_option


LOG = logging.getLogger(__name__)


class VcmtsdSetupEnvHelper(SetupEnvHelper):

    def run_vcmtsd(self):
        LOG.debug("Executing %s", self.cmd)
        exit_status, _, _ = self.ssh_helper.execute(self.cmd)
        if exit_status != 0:
            LOG.error("Error executing vcmtsd (%d)", exit_status)

    def build_us_parameters(self, pod_cfg):
        return "/opt/bin/cmk isolate --conf-dir=/etc/cmk" \
             + " --conf-dir=/etc/cmk --socket-id=" + pod_cfg['cpu_socket_id'] \
             + " --pool=shared" \
             + " /vcmts-config/run_upstream.sh" + pod_cfg['sg_id'] \
             + " " + pod_cfg['ds_core_type'] \
             + " " + pod_cfg['num_ofdm'] + "ofdm" \
             + " " + pod_cfg['num_subs'] + "cm" \
             + " " + pod_cfg['cm_crypto'] \
             + " " + pod_cfg['qat'] \
             + " " + pod_cfg['net_us'] \
             + " " + pod_cfg['power_mgmt']

    def build_ds_parameters(self, pod_cfg):
        return "/opt/bin/cmk isolate --conf-dir=/etc/cmk" \
             + " --socket-id=" + pod_cfg['cpu_socket_id'] \
             + " --pool=" + pod_cfg['ds_core_type'] \
             + " /vcmts-config/run_downstream.sh " + pod_cfg['sg_id'] \
             + " " + pod_cfg['ds_core_type'] \
             + " " + pod_cfg['ds_core_pool_index'] \
             + " " + pod_cfg['num_ofdm'] + "ofdm" \
             + " " + pod_cfg['num_subs'] + "cm" \
             + " " + pod_cfg['cm_crypto'] \
             + " " + pod_cfg['qat'] \
             + " " + pod_cfg['net_ds'] \
             + " " + pod_cfg['power_mgmt']

    def build_cmd(self, stream_dir, pod_cfg):
        if stream_dir == 'ds':
            self.cmd = self.build_ds_parameters(pod_cfg)
        else:
            self.cmd = self.build_us_parameters(pod_cfg)

    def setup_vnf_environment(self):
        pass


class VcmtsResourceHelperI(ResourceHelper):

    def __init__(self, setup_helper):
        super(VcmtsResourceHelperI, self).__init__(setup_helper)
        self._queue = Queue()

    def start(self):
        self.setup_helper.run_vcmtsd()


class VcmtsVNF(SampleVNF):

    TG_NAME = 'VcmtsVNF'
    APP_NAME = 'VcmtsVNF'
    RUN_WAIT = 4

    def __init__(self, name, vnfd, task_id):
        super(VcmtsVNF, self).__init__(name, vnfd, task_id)

        self.name = name
        self.bin_path = get_nsb_option('bin_path', '')

        self.scenario_helper = ScenarioHelper(self.name)
        self.ssh_helper = VnfSshHelper(self.vnfd_helper.mgmt_interface, self.bin_path, wait=True)

        self.setup_helper = VcmtsdSetupEnvHelper(self.vnfd_helper,
                                                self.ssh_helper,
                                                self.scenario_helper)

        self.resource_helper = VcmtsResourceHelperI(self.setup_helper)

    def read_yaml_file(self, path):
        """Read yaml file"""
        with open(path) as stream:
            data = yaml.load(stream, Loader=yaml.BaseLoader)
            return data

    def extract_pod_cfg(self, vcmts_pods_cfg, sg_id):
        for pod_cfg in vcmts_pods_cfg:
            if pod_cfg['sg_id'] == sg_id:
                return pod_cfg
        LOG.error("Service group %s not found", sg_id)
        return None

    def instantiate(self, scenario_cfg, context_cfg):
        self._update_collectd_options(scenario_cfg, context_cfg)
        vcmtsd_values_filepath = scenario_cfg['options']['vcmtsd_values']

        if not os.path.isfile(vcmtsd_values_filepath):
            LOG.exception("vcmtsd_values file provided (%s) does not exists",
                          vcmtsd_values_filepath)

        sg_id = str(scenario_cfg['options'][self.name]['sg_id'])
        stream_dir = str(scenario_cfg['options'][self.name]['stream_dir'])

        vcmtsd_values = self.read_yaml_file(vcmtsd_values_filepath)
        vcmts_pods_cfg = vcmtsd_values['topology']['vcmts_pods']

        pod_cfg = self.extract_pod_cfg(vcmts_pods_cfg, sg_id)

        self.setup_helper.build_cmd(stream_dir, pod_cfg)
        self.resource_helper.start()

    def wait_for_instantiate(self):
        pass

    def terminate(self):
        pass

    def scale(self, flavor=""):
        pass

    def collect_kpi(self):
        pass

    def start_collect(self):
        pass

    def stop_collect(self):
        pass
