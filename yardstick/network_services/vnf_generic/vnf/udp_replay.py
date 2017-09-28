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

from yardstick.common.process import check_if_process_failed
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF
from yardstick.network_services.vnf_generic.vnf.sample_vnf import DpdkVnfSetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper


LOG = logging.getLogger(__name__)

# UDP_Replay should work the same on all systems, we can provide the binary

# we can't match the prompt regexp due to extra noise
# yardstick.ssh ssh.py:302 DEBUG stdout: UDP_Replay: lcore 0 has nothing to do
# eplUDP_Replay:  -- lcoreid=1 portid=0 rxqueueid=0
# ay>
#
# try decreasing log level to RTE_LOG_NOTICE (5)
REPLAY_PIPELINE_COMMAND = (
    """sudo {tool_path} --log-level=5 -c {cpu_mask_hex} -n 4 -w {whitelist} -- """
    """{hw_csum} -p {port_mask_hex} --config='{config}'"""
)
# {tool_path} -p {port_mask_hex} -f {cfg_file} -s {script}'


class UdpReplaySetupEnvHelper(DpdkVnfSetupEnvHelper):

    APP_NAME = "UDP_Replay"


class UdpReplayResourceHelper(ClientResourceHelper):
    pass


class UdpReplayApproxVnf(SampleVNF):

    APP_NAME = "UDP_Replay"
    APP_WORD = "UDP_Replay"
    # buffering issue?
    VNF_PROMPT = 'eplay>'

    VNF_TYPE = 'UdpReplay'

    HW_OFFLOADING_NFVI_TYPES = {'baremetal', 'sriov'}

    PIPELINE_COMMAND = REPLAY_PIPELINE_COMMAND

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = UdpReplayResourceHelper

        if setup_env_helper_type is None:
            setup_env_helper_type = UdpReplaySetupEnvHelper

        super(UdpReplayApproxVnf, self).__init__(name, vnfd, setup_env_helper_type,
                                                 resource_helper_type)

    def _build_pipeline_kwargs(self):
        ports = self.vnfd_helper.port_pairs.all_ports
        number_of_ports = len(ports)

        tool_path = self.ssh_helper.provision_tool(tool_file=self.APP_NAME)
        port_nums = self.vnfd_helper.port_nums(ports)
        ports_mask_hex = hex(sum(2 ** num for num in port_nums))
        # one core extra for master
        cpu_mask_hex = hex(2 ** (number_of_ports + 1) - 1)
        hw_csum = ""
        if (not self.scenario_helper.options.get('hw_csum', False) or
                self.nfvi_context.attrs.get('nfvi_type') not in self.HW_OFFLOADING_NFVI_TYPES):
            hw_csum = '--no-hw-csum'

        # tuples of (FLD_PORT, FLD_QUEUE, FLD_LCORE)
        #  [--config (port,queue,lcore)[,(port,queue,lcore]]"
        # start with lcore = 1 since we use lcore=0 for master
        config_value = ",".join(
            str((self.vnfd_helper.port_num(port), 0, core)).replace(" ", "") for core, port in
            enumerate(self.vnfd_helper.port_pairs.all_ports, 1))

        whitelist = " -w ".join(self.setup_helper.bound_pci)
        self.pipeline_kwargs = {
            'port_mask_hex': ports_mask_hex,
            'tool_path': tool_path,
            'hw_csum': hw_csum,
            'whitelist': whitelist,
            'cpu_mask_hex': cpu_mask_hex,
            'config': config_value,
        }

    def _build_config(self):
        self._build_pipeline_kwargs()
        return self.PIPELINE_COMMAND.format(**self.pipeline_kwargs)

    def collect_kpi(self):
        def get_sum(offset):
            return sum(int(i) for i in split_stats[offset::5])
        # we can't get KPIs if the VNF is down
        check_if_process_failed(self._vnf_process)

        number_of_ports = len(self.vnfd_helper.port_pairs.all_ports)

        stats = self.get_stats()
        stats_words = stats.split()
        split_stats = stats_words[stats_words.index('0'):][:number_of_ports * 5]
        result = {
            "packets_in": get_sum(1),
            "packets_fwd": get_sum(2),
            "packets_dropped": get_sum(3) + get_sum(4),
            'collect_stats': self.resource_helper.collect_kpi(),
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
