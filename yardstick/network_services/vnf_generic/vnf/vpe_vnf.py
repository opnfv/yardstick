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
""" vPE (Power Edge router) VNF model definitions based on IETS Spec """

from __future__ import absolute_import
from __future__ import print_function


import os
import logging
import re
import posixpath

from six.moves import configparser, zip

from yardstick.common.process import check_if_process_failed
from yardstick.network_services.helpers.samplevnf_helper import PortPairs
from yardstick.network_services.pipeline import PipelineRules
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF, DpdkVnfSetupEnvHelper
from yardstick.benchmark.contexts import base as ctx_base

LOG = logging.getLogger(__name__)

VPE_PIPELINE_COMMAND = "sudo {tool_path} -p {port_mask_hex} -f {cfg_file} -s {script} {hwlb}"

VPE_COLLECT_KPI = """\
Pkts in:\\s(\\d+)\r\n\
\tPkts dropped by AH:\\s(\\d+)\r\n\
\tPkts dropped by other:\\s(\\d+)\
"""


class ConfigCreate(object):

    def __init__(self, vnfd_helper, socket):
        super(ConfigCreate, self).__init__()
        self.sw_q = -1
        self.sink_q = -1
        self.n_pipeline = 1
        self.vnfd_helper = vnfd_helper
        self.uplink_ports = self.vnfd_helper.port_pairs.uplink_ports
        self.downlink_ports = self.vnfd_helper.port_pairs.downlink_ports
        self.pipeline_per_port = 9
        self.socket = socket
        self._dpdk_port_to_link_id_map = None


    def generate_vpe_script(self, interfaces):
        rules = PipelineRules(pipeline_id=1)
        for uplink_port, downlink_port in zip(self.uplink_ports, self.downlink_ports):

            uplink_intf = \
                next(intf["virtual-interface"] for intf in interfaces
                     if intf["name"] == uplink_port)
            downlink_intf = \
                next(intf["virtual-interface"] for intf in interfaces
                     if intf["name"] == downlink_port)

            dst_port0_ip = uplink_intf["dst_ip"]
            dst_port1_ip = downlink_intf["dst_ip"]
            dst_port0_mac = uplink_intf["dst_mac"]
            dst_port1_mac = downlink_intf["dst_mac"]

            rules.add_firewall_script(dst_port0_ip)
            rules.next_pipeline()
            rules.add_flow_classification_script()
            rules.next_pipeline()
            rules.add_flow_action()
            rules.next_pipeline()
            rules.add_flow_action2()
            rules.next_pipeline()
            rules.add_route_script(dst_port1_ip, dst_port1_mac)
            rules.next_pipeline()
            rules.add_route_script2(dst_port0_ip, dst_port0_mac)
            rules.next_pipeline(num=4)

        return rules.get_string()


class VpeApproxSetupEnvHelper(DpdkVnfSetupEnvHelper):

    APP_NAME = 'vPE_vnf'
    CFG_SCRIPT = "/tmp/vpe_script"
    TM_CONFIG = "/tmp/full_tm_profile_10G.cfg"
    CORES = ['0', '1', '2', '3', '4', '5']
    PIPELINE_COMMAND = VPE_PIPELINE_COMMAND

    def _build_vnf_ports(self):
        self._port_pairs = PortPairs(self.vnfd_helper.interfaces)
        self.uplink_ports = self._port_pairs.uplink_ports
        self.downlink_ports = self._port_pairs.downlink_ports
        self.all_ports = self._port_pairs.all_ports

    def build_config(self):
        vnf_cfg = self.scenario_helper.vnf_cfg
        config_file = vnf_cfg.get('file', '/tmp/vpe_config')
        vpe_vars = {
            "bin_path": self.ssh_helper.bin_path,
            "socket": self.socket,
        }
        self._build_vnf_ports()
        vpe_conf = ConfigCreate(self.vnfd_helper, self.socket)

        config_basename = posixpath.basename(config_file)
        script_basename = posixpath.basename(self.CFG_SCRIPT)
        with open(config_file) as handle:
            vpe_config = handle.read()

        self.ssh_helper.upload_config_file(config_basename, vpe_config.format(**vpe_vars))

        vpe_script = vpe_conf.generate_vpe_script(self.vnfd_helper.interfaces)
        self.ssh_helper.upload_config_file(script_basename, vpe_script.format(**vpe_vars))

        LOG.info("Provision and start the %s", self.APP_NAME)
        LOG.info(config_file)
        LOG.info(self.CFG_SCRIPT)
        self._build_pipeline_kwargs()
        self.pipeline_kwargs['cfg_file'] = '/tmp/' + config_basename
        return self.PIPELINE_COMMAND.format(**self.pipeline_kwargs)


class VpeApproxVnf(SampleVNF):
    """ This class handles vPE VNF model-driver definitions """

    APP_NAME = 'vPE_vnf'
    APP_WORD = 'vpe'
    COLLECT_KPI = VPE_COLLECT_KPI
    WAIT_TIME = 20

    def __init__(self, name, vnfd, task_id, setup_env_helper_type=None,
                 resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = VpeApproxSetupEnvHelper
        super(VpeApproxVnf, self).__init__(
            name, vnfd, task_id, setup_env_helper_type, resource_helper_type)

    def get_stats(self, *args, **kwargs):
        raise NotImplementedError

    def collect_kpi(self):
        # we can't get KPIs if the VNF is down
        check_if_process_failed(self._vnf_process)
        physical_node = ctx_base.Context.get_physical_node_from_server(
            self.scenario_helper.nodes[self.name])

        result = {
            "physical_node": physical_node,
            'pkt_in_up_stream': 0,
            'pkt_drop_up_stream': 0,
            'pkt_in_down_stream': 0,
            'pkt_drop_down_stream': 0,
            'collect_stats': self.resource_helper.collect_kpi(),
        }

        indexes_in = [1]
        indexes_drop = [2, 3]
        command = 'p {0} stats port {1} 0'
        for index, direction in ((5, 'up'), (9, 'down')):
            key_in = "pkt_in_{0}_stream".format(direction)
            key_drop = "pkt_drop_{0}_stream".format(direction)
            for mode in ('in', 'out'):
                stats = self.vnf_execute(command.format(index, mode))
                match = re.search(self.COLLECT_KPI, stats, re.MULTILINE)
                if not match:
                    continue
                result[key_in] += sum(int(match.group(x)) for x in indexes_in)
                result[key_drop] += sum(int(match.group(x)) for x in indexes_drop)

        LOG.debug("%s collect KPIs %s", self.APP_NAME, result)
        return result
