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


from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxDpdkVnfSetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen

LOG = logging.getLogger(__name__)


class ProxTrafficGen(SampleVNFTrafficGen):

    PROX_MODE = "Traffic Gen"
    LUA_PARAMETER_NAME = "gen"

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
        if setup_env_helper_type is None:
            setup_env_helper_type = ProxDpdkVnfSetupEnvHelper

        if resource_helper_type is None:
            resource_helper_type = ProxResourceHelper

        super(ProxTrafficGen, self).__init__(name, vnfd, setup_env_helper_type,
                                             resource_helper_type)
        self._result = {}
        # for some reason
        self.vpci_if_name_ascending = self._sort_vpci(vnfd)
        self._traffic_process = None

    def listen_traffic(self, traffic_profile):
        pass

    def terminate(self):
        super(ProxTrafficGen, self).terminate()
        self.resource_helper.terminate()
        if self._traffic_process:
            self._traffic_process.terminate()
        self.ssh_helper.execute("pkill prox")
        self.resource_helper.rebind_drivers()
