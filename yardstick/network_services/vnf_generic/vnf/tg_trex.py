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
""" Trex acts as traffic generation and vnf definitions based on IETS Spec """

from __future__ import absolute_import
from __future__ import print_function

import logging
import os

import yaml

from yardstick.common.utils import mac_address_to_hex_list
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper

LOG = logging.getLogger(__name__)


class TrexResourceHelper(ClientResourceHelper):

    CONF_FILE = '/tmp/trex_cfg.yaml'
    QUEUE_WAIT_TIME = 1
    RESOURCE_WORD = 'trex'
    RUN_DURATION = 0

    SYNC_PORT = 4500
    ASYNC_PORT = 4501

    def generate_cfg(self):
        ext_intf = self.vnfd_helper.interfaces
        vpci_list = []
        port_list = []
        trex_cfg = {
            'port_limit': 0,
            'version': '2',
            'interfaces': vpci_list,
            'port_info': port_list,
            "port_limit": len(ext_intf),
            "version": '2',
        }
        cfg_file = [trex_cfg]

        for interface in ext_intf:
            virtual_interface = interface['virtual-interface']
            vpci_list.append(virtual_interface["vpci"])
            dst_mac = virtual_interface["dst_mac"]

            if not dst_mac:
                continue

            local_mac = virtual_interface["local_mac"]
            port_list.append({
                "src_mac": mac_address_to_hex_list(local_mac),
                "dest_mac": mac_address_to_hex_list(dst_mac),
            })

        cfg_str = yaml.safe_dump(cfg_file, default_flow_style=False, explicit_start=True)
        self.ssh_helper.upload_config_file(os.path.basename(self.CONF_FILE), cfg_str)
        self._vpci_ascending = sorted(vpci_list)

    def check_status(self):
        status, _, _ = self.ssh_helper.execute("sudo lsof -i:%s" % self.SYNC_PORT)
        return status

    # temp disable
    DISABLE_DEPLOY = True

    def setup(self):
        if self.DISABLE_DEPLOY:
            return

        trex_path = self.ssh_helper.join_bin_path('trex')

        err = self.ssh_helper.execute("which {}".format(trex_path))[0]
        if err == 0:
            return

        LOG.info("Copying %s to destination...", self.RESOURCE_WORD)
        self.ssh_helper.run("sudo mkdir -p '{}'".format(os.path.dirname(trex_path)))
        self.ssh_helper.put("~/.bash_profile", "~/.bash_profile")
        self.ssh_helper.put(trex_path, trex_path, True)
        ko_src = os.path.join(trex_path, "scripts/ko/src/")
        self.ssh_helper.execute(self.MAKE_INSTALL.format(ko_src))

    def start(self, ports=None, *args, **kwargs):
        cmd = "sudo fuser -n tcp {0.SYNC_PORT} {0.ASYNC_PORT} -k > /dev/null 2>&1"
        self.ssh_helper.execute(cmd.format(self))

        self.ssh_helper.execute("sudo pkill -9 rex > /dev/null 2>&1")

        trex_path = self.ssh_helper.join_bin_path("trex", "scripts")
        path = get_nsb_option("trex_path", trex_path)

        # cmd = "sudo ./t-rex-64 -i --cfg %s > /dev/null 2>&1" % self.CONF_FILE
        cmd = "./t-rex-64 -i --cfg '{}'".format(self.CONF_FILE)

        # if there are errors we want to see them
        # we have to sudo cd because the path might be owned by root
        trex_cmd = """sudo bash -c "cd '{}' ; {}" >/dev/null""".format(path, cmd)
        self.ssh_helper.execute(trex_cmd)

    def terminate(self):
        super(TrexResourceHelper, self).terminate()
        cmd = "sudo fuser -n tcp %s %s -k > /dev/null 2>&1"
        self.ssh_helper.execute(cmd % (self.SYNC_PORT, self.ASYNC_PORT))


class TrexTrafficGen(SampleVNFTrafficGen):
    """
    This class handles mapping traffic profile and generating
    traffic for given testcase
    """

    APP_NAME = 'TRex'

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = TrexResourceHelper

        super(TrexTrafficGen, self).__init__(name, vnfd, setup_env_helper_type,
                                             resource_helper_type)

    def _check_status(self):
        return self.resource_helper.check_status()

    def _start_server(self):
        super(TrexTrafficGen, self)._start_server()
        self.resource_helper.start()

    def scale(self, flavor=""):
        pass

    def listen_traffic(self, traffic_profile):
        pass

    def terminate(self):
        self.resource_helper.terminate()
