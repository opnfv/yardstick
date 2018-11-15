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

from yardstick.network_services.vnf_generic.vnf.sample_vnf import \
    DpdkVnfSetupEnvHelper

LOG = logging.getLogger(__name__)


class VppSetupEnvHelper(DpdkVnfSetupEnvHelper):
    APP_NAME = "vpp"
    CFG_CONFIG = "/etc/vpp/startup.conf"
    CFG_SCRIPT = ""
    PIPELINE_COMMAND = ""
    VNF_TYPE = "IPSEC"
    VAT_BIN_NAME = 'vpp_api_test'

    def __init__(self, vnfd_helper, ssh_helper, scenario_helper):
        super(VppSetupEnvHelper, self).__init__(vnfd_helper, ssh_helper,
                                                scenario_helper)

    def kill_vnf(self):
        ret_code, _, _ = \
            self.ssh_helper.execute(
                'service {name} stop'.format(name=self.APP_NAME))
        if int(ret_code):
            raise RuntimeError(
                'Failed to stop service {name}'.format(name=self.APP_NAME))

    def tear_down(self):
        pass

    def start_vpp_service(self):
        ret_code, _, _ = \
            self.ssh_helper.execute(
                'service {name} restart'.format(name=self.APP_NAME))
        if int(ret_code):
            raise RuntimeError(
                'Failed to start service {name}'.format(name=self.APP_NAME))

    def _update_vnfd_helper(self, additional_data, iface_key=None):
        for k, v in additional_data.items():
            if iface_key is None:
                if isinstance(v, dict) and k in self.vnfd_helper:
                    self.vnfd_helper[k].update(v)
                else:
                    self.vnfd_helper[k] = v
            else:
                if isinstance(v,
                              dict) and k in self.vnfd_helper.find_virtual_interface(
                    ifname=iface_key):
                    self.vnfd_helper.find_virtual_interface(ifname=iface_key)[
                        k].update(v)
                else:
                    self.vnfd_helper.find_virtual_interface(ifname=iface_key)[
                        k] = v

    def get_value_by_interface_key(self, interface, key):
        try:
            return self.vnfd_helper.find_virtual_interface(
                ifname=interface).get(key)
        except (KeyError, ValueError):
            return None
