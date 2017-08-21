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

from yardstick.network_services.pipeline import PipelineRules
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF, DpdkVnfSetupEnvHelper

LOG = logging.getLogger(__name__)

VPE_PIPELINE_COMMAND = """sudo {tool_path} -p {ports_len_hex} -f {cfg_file} -s {script}"""

VPE_COLLECT_KPI = """\
Pkts in:\s(\d+)\r\n\
\tPkts dropped by Pkts in:\s(\d+)\r\n\
\tPkts dropped by AH:\s(\d+)\r\n\\
\tPkts dropped by other:\s(\d+)\
"""


class ConfigCreate(object):

    @staticmethod
    def vpe_tmq(config, index):
        tm_q = 'TM{0}'.format(index)
        config.add_section(tm_q)
        config.set(tm_q, 'burst_read', '24')
        config.set(tm_q, 'burst_write', '32')
        config.set(tm_q, 'cfg', '/tmp/full_tm_profile_10G.cfg')
        return config

    def __init__(self, priv_ports, pub_ports, socket):
        super(ConfigCreate, self).__init__()
        self.sw_q = -1
        self.sink_q = -1
        self.n_pipeline = 1
        self.priv_ports = priv_ports
        self.pub_ports = pub_ports
        self.pipeline_per_port = 9
        self.socket = socket

    def vpe_initialize(self, config):
        config.add_section('EAL')
        config.set('EAL', 'log_level', '0')

        config.add_section('PIPELINE0')
        config.set('PIPELINE0', 'type', 'MASTER')
        config.set('PIPELINE0', 'core', 's%sC0' % self.socket)

        config.add_section('MEMPOOL0')
        config.set('MEMPOOL0', 'pool_size', '256K')

        config.add_section('MEMPOOL1')
        config.set('MEMPOOL1', 'pool_size', '2M')
        return config

    def vpe_rxq(self, config):
        for port in self.pub_ports:
            new_section = 'RXQ{0}.0'.format(port)
            config.add_section(new_section)
            config.set(new_section, 'mempool', 'MEMPOOL1')

        return config

    def get_sink_swq(self, parser, pipeline, k, index):
        sink = ""
        pktq = parser.get(pipeline, k)
        if "SINK" in pktq:
            self.sink_q += 1
            sink = " SINK{0}".format(self.sink_q)
        if "TM" in pktq:
            sink = " TM{0}".format(index)
        pktq = "SWQ{0}{1}".format(self.sw_q, sink)
        return pktq

    def vpe_upstream(self, vnf_cfg, intf):
        parser = configparser.ConfigParser()
        parser.read(os.path.join(vnf_cfg, 'vpe_upstream'))
        for pipeline in parser.sections():
            for k, v in parser.items(pipeline):
                if k == "pktq_in":
                    index = intf['index']
                    if "RXQ" in v:
                        value = "RXQ{0}.0".format(index)
                    else:
                        value = self.get_sink_swq(parser, pipeline, k, index)

                    parser.set(pipeline, k, value)

                elif k == "pktq_out":
                    index = intf['peer_intf']['index']
                    if "TXQ" in v:
                        value = "TXQ{0}.0".format(index)
                    else:
                        self.sw_q += 1
                        value = self.get_sink_swq(parser, pipeline, k, index)

                    parser.set(pipeline, k, value)

            new_pipeline = 'PIPELINE{0}'.format(self.n_pipeline)
            if new_pipeline != pipeline:
                parser._sections[new_pipeline] = parser._sections[pipeline]
                parser._sections.pop(pipeline)
            self.n_pipeline += 1
        return parser

    def vpe_downstream(self, vnf_cfg, intf):
        parser = configparser.ConfigParser()
        parser.read(os.path.join(vnf_cfg, 'vpe_downstream'))
        for pipeline in parser.sections():
            for k, v in parser.items(pipeline):
                index = intf['dpdk_port_num']
                peer_index = intf['peer_intf']['dpdk_port_num']

                if k == "pktq_in":
                    if "RXQ" not in v:
                        value = self.get_sink_swq(parser, pipeline, k, index)
                    elif "TM" in v:
                        value = "RXQ{0}.0 TM{1}".format(peer_index, index)
                    else:
                        value = "RXQ{0}.0".format(peer_index)

                    parser.set(pipeline, k, value)

                if k == "pktq_out":
                    if "TXQ" not in v:
                        self.sw_q += 1
                        value = self.get_sink_swq(parser, pipeline, k, index)
                    elif "TM" in v:
                        value = "TXQ{0}.0 TM{1}".format(peer_index, index)
                    else:
                        value = "TXQ{0}.0".format(peer_index)

                    parser.set(pipeline, k, value)

            new_pipeline = 'PIPELINE{0}'.format(self.n_pipeline)
            if new_pipeline != pipeline:
                parser._sections[new_pipeline] = parser._sections[pipeline]
                parser._sections.pop(pipeline)
            self.n_pipeline += 1
        return parser

    def create_vpe_config(self, vnf_cfg):
        config = configparser.ConfigParser()
        vpe_cfg = os.path.join("/tmp/vpe_config")
        with open(vpe_cfg, 'w') as cfg_file:
            config = self.vpe_initialize(config)
            config = self.vpe_rxq(config)
            config.write(cfg_file)
            for index, priv_port in enumerate(self.priv_ports):
                config = self.vpe_upstream(vnf_cfg, priv_port)
                config.write(cfg_file)
                config = self.vpe_downstream(vnf_cfg, priv_port)
                config = self.vpe_tmq(config, index)
                config.write(cfg_file)

    def generate_vpe_script(self, interfaces):
        rules = PipelineRules(pipeline_id=1)
        for priv_port, pub_port in zip(self.priv_ports, self.pub_ports):
            priv_intf = interfaces[priv_port]["virtual-interface"]
            pub_intf = interfaces[pub_port]["virtual-interface"]

            dst_port0_ip = priv_intf["dst_ip"]
            dst_port1_ip = pub_intf["dst_ip"]
            dst_port0_mac = priv_intf["dst_mac"]
            dst_port1_mac = pub_intf["dst_mac"]

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

    CFG_CONFIG = "/tmp/vpe_config"
    CFG_SCRIPT = "/tmp/vpe_script"
    CORES = ['0', '1', '2', '3', '4', '5']
    PIPELINE_COMMAND = VPE_PIPELINE_COMMAND

    def build_config(self):
        vpe_vars = {
            "bin_path": self.ssh_helper.bin_path,
            "socket": self.socket,
        }

        all_ports = []
        priv_ports = []
        pub_ports = []
        for interface in self.vnfd_helper.interfaces:
            all_ports.append(interface['name'])
            vld_id = interface['virtual-interface']['vld_id']
            if vld_id.startswith('private'):
                priv_ports.append(interface)
            elif vld_id.startswith('public'):
                pub_ports.append(interface)

        vpe_conf = ConfigCreate(priv_ports, pub_ports, self.socket)
        vpe_conf.create_vpe_config(self.scenario_helper.vnf_cfg)

        config_basename = posixpath.basename(self.CFG_CONFIG)
        script_basename = posixpath.basename(self.CFG_SCRIPT)
        with open(self.CFG_CONFIG) as handle:
            vpe_config = handle.read()

        self.ssh_helper.upload_config_file(config_basename, vpe_config.format(**vpe_vars))

        vpe_script = vpe_conf.generate_vpe_script(self.vnfd_helper.interfaces)
        self.ssh_helper.upload_config_file(script_basename, vpe_script.format(**vpe_vars))


class VpeApproxVnf(SampleVNF):
    """ This class handles vPE VNF model-driver definitions """

    APP_NAME = 'vPE_vnf'
    APP_WORD = 'vpe'
    COLLECT_KPI = VPE_COLLECT_KPI
    WAIT_TIME = 20

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = VpeApproxSetupEnvHelper

        super(VpeApproxVnf, self).__init__(name, vnfd, setup_env_helper_type, resource_helper_type)

    def get_stats(self, *args, **kwargs):
        raise NotImplementedError

    def collect_kpi(self):
        result = {
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
