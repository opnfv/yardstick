# Copyright (c) 2017 Intel Corporation
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

from __future__ import print_function, absolute_import

import logging

from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.vnf_generic.vnf.prox_vnf import ProxApproxVnf
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen

LOG = logging.getLogger(__name__)


class ProxTrafficGen(SampleVNFTrafficGen):

    APP_NAME = 'ProxTG'
    PROX_MODE = "Traffic Gen"
    LUA_PARAMETER_NAME = "gen"
    WAIT_TIME = 1

    @staticmethod
    def _sort_vpci(vnfd):
        """

        :param vnfd: vnfd.yaml
        :return: trex_cfg.yaml file
        """

        def key_func(interface):
            return interface["virtual-interface"]["vpci"], interface["name"]

        ext_intf = vnfd["vdu"][0]["external-interface"]
        return sorted(ext_intf, key=key_func)

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        # don't call superclass, use custom wrapper of ProxApproxVnf
        self._vnf_wrapper = ProxApproxVnf(name, vnfd, setup_env_helper_type, resource_helper_type)
        self.bin_path = get_nsb_option('bin_path', '')
        self.name = self._vnf_wrapper.name
        self.ssh_helper = self._vnf_wrapper.ssh_helper
        self.setup_helper = self._vnf_wrapper.setup_helper
        self.resource_helper = self._vnf_wrapper.resource_helper
        self.scenario_helper = self._vnf_wrapper.scenario_helper

        self.runs_traffic = True
        self.traffic_finished = False
        self.tg_port_pairs = None
        self._tg_process = None
        self._traffic_process = None

        # used for generating stats
        self.vpci_if_name_ascending = self._sort_vpci(vnfd)

    def listen_traffic(self, traffic_profile):
        pass

    def terminate(self):
        self._vnf_wrapper.terminate()
        super(ProxTrafficGen, self).terminate()

    def instantiate(self, scenario_cfg, context_cfg):
        self._vnf_wrapper.instantiate(scenario_cfg, context_cfg)
        self._tg_process = self._vnf_wrapper._vnf_process

    def wait_for_instantiate(self):
        self._vnf_wrapper.wait_for_instantiate()

    # TODO: fix this, not sure if we want the TG KPIS or the VNF KPIS
    # def collect_kpi(self):
    #     return self._vnf_wrapper.collect_kpi()
