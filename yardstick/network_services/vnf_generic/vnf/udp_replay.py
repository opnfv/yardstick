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
import logging

from yardstick.network_services.vnf_generic.vnf.sample_vnf import (SampleVNF,
                                                                   DpdkVnfSetupEnvHelper,
                                                                   ClientResourceHelper,
                                                                   )

LOG = logging.getLogger(__name__)

# UDP_Replay should work the same on all systems, we can provide the binary
REPLAY_PIPELINE_COMMAND = (
    """sudo {tool_path} -c {cpu_mask_hex} -n 4 -w {whitelist} -- """
    """{hw_csum} -p {ports_len_hex} --config='{config}'"""
)
# {tool_path} -p {ports_len_hex} -f {cfg_file} -s {script}'


class UdpReplaySetupEnvHelper(DpdkVnfSetupEnvHelper):

    APP_NAME = "UDP_Replay"


class UdpReplayResourceHelper(ClientResourceHelper):
    pass


class UdpReplayApproxVnf(SampleVNF):

    APP_NAME = "UDP_Replay"
    APP_WORD = "UDP_Replay"
    VNF_PROMPT = 'Replay>'

    VNF_TYPE = 'UdpReplay'

    CSUM_MAP = {
        'baremetal': '',
        'sriov': '',
    }

    PIPELINE_COMMAND = REPLAY_PIPELINE_COMMAND

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = UdpReplayResourceHelper

        if setup_env_helper_type is None:
            setup_env_helper_type = UdpReplaySetupEnvHelper

        super(UdpReplayApproxVnf, self).__init__(name, vnfd, setup_env_helper_type,
                                                 resource_helper_type)

    def _start_server(self):
        super(UdpReplayApproxVnf, self)._start_server()
        self.resource_helper.start()

    def scale(self, flavor=""):
        """ scale vnfbased on flavor input """
        raise NotImplementedError

    def _deploy(self):
        self.generate_port_pairs()
        super(UdpReplayApproxVnf, self)._deploy()

    def _build_pipeline_kwargs(self):
        tool_path = self.ssh_helper.provision_tool(tool_file=self.APP_NAME)
        ports_mask = 2 ** len(self.all_ports) - 1
        ports_mask_hex = hex(ports_mask)
        # cpu_mask_hex = hex(ports_mask * 2)
        # was causing segmentation fault, works with 0x7
        cpu_mask_hex = hex(7)
        hw_csum = self.CSUM_MAP.get(self.nfvi_context.attrs.get('nfvi_type'), "--no-hw-csum")
        config_value = "".join(str((port, 0, port + 1)) for port in self.all_ports)

        whitelist = " -w ".join(self.setup_helper.bound_pci)
        self.pipeline_kwargs = {
            'ports_len_hex': ports_mask_hex,
            'tool_path': tool_path,
            'hw_csum': hw_csum,
            'whitelist': whitelist,
            'cpu_mask_hex': cpu_mask_hex,
            'config': config_value,
        }

    def _build_config(self):
        # FIXME: should be calculated from topology
        self.all_ports = [0, 1]
        self._build_pipeline_kwargs()
        return self.PIPELINE_COMMAND.format(**self.pipeline_kwargs)

    def collect_kpi(self):
        def get_sum(offset):
            return sum(int(i) for i in split_stats[offset::5])

        # this gets called during instantiation but in a different process
        # this process wouldn't see the self.all_ports
        self._build_config()

        stats = self.get_stats()
        stats_words = stats.split()
        split_stats = stats_words[stats_words.index('0'):][:len(self.all_ports) * 5]
        result = {
            "packets_in": get_sum(1),
            "packets_fwd": get_sum(2),
            "packets_dropped": get_sum(3) + get_sum(4),
            "collect_stats": {},
        }

        LOG.debug("UDP Replay collect KPIs %s", result)
        return result

    def get_stats(self):
        """
        Method for checking the statistics

        :return:
           UDP Replay statistics
        """
        cmd = 'UDP_Replay stats'
        out = self.vnf_execute(cmd)
        return out
