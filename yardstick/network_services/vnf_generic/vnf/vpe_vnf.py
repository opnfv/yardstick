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

LOG = logging.getLogger(__name__)

VPE_PIPELINE_COMMAND = """sudo {tool_path} -p {port_mask_hex} -f {cfg_file} -s {script}"""

VPE_COLLECT_KPI = """\
Pkts in:\\s(\\d+)\r\n\
\tPkts dropped by AH:\\s(\\d+)\r\n\
\tPkts dropped by other:\\s(\\d+)\
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

    @property
    def dpdk_port_to_link_id_map(self):
        # we need interface name -> DPDK port num (PMD ID) -> LINK ID
        # LINK ID -> PMD ID is governed by the port mask
        # LINK instances are created implicitly based on the PORT_MASK application startup
        # argument. LINK0 is the first port enabled in the PORT_MASK, port 1 is the next one,
        # etc. The LINK ID is different than the DPDK PMD-level NIC port ID, which is the actual
        #  position in the bitmask mentioned above. For example, if bit 5 is the first bit set
        # in the bitmask, then LINK0 is having the PMD ID of 5. This mechanism creates a
        # contiguous LINK ID space and isolates the configuration file against changes in the
        # board PCIe slots where NICs are plugged in.
        if self._dpdk_port_to_link_id_map is None:
            self._dpdk_port_to_link_id_map = {}
            for link_id, port_name in enumerate(sorted(self.vnfd_helper.port_pairs.all_ports,
                                                       key=self.vnfd_helper.port_num)):
                self._dpdk_port_to_link_id_map[port_name] = link_id
        return self._dpdk_port_to_link_id_map

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
        for port in self.downlink_ports:
            new_section = 'RXQ{0}.0'.format(self.dpdk_port_to_link_id_map[port])
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

    def vpe_upstream(self, vnf_cfg, index=0):
        parser = configparser.ConfigParser()
        parser.read(os.path.join(vnf_cfg, 'vpe_upstream'))

        for pipeline in parser.sections():
            for k, v in parser.items(pipeline):
                if k == "pktq_in":
                    if "RXQ" in v:
                        port = self.dpdk_port_to_link_id_map[self.uplink_ports[index]]
                        value = "RXQ{0}.0".format(port)
                    else:
                        value = self.get_sink_swq(parser, pipeline, k, index)

                    parser.set(pipeline, k, value)

                elif k == "pktq_out":
                    if "TXQ" in v:
                        port = self.dpdk_port_to_link_id_map[self.downlink_ports[index]]
                        value = "TXQ{0}.0".format(port)
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

    def vpe_downstream(self, vnf_cfg, index):
        parser = configparser.ConfigParser()
        parser.read(os.path.join(vnf_cfg, 'vpe_downstream'))
        for pipeline in parser.sections():
            for k, v in parser.items(pipeline):

                if k == "pktq_in":
                    port = self.dpdk_port_to_link_id_map[self.downlink_ports[index]]
                    if "RXQ" not in v:
                        value = self.get_sink_swq(parser, pipeline, k, index)
                    elif "TM" in v:
                        value = "RXQ{0}.0 TM{1}".format(port, index)
                    else:
                        value = "RXQ{0}.0".format(port)

                    parser.set(pipeline, k, value)

                if k == "pktq_out":
                    port = self.dpdk_port_to_link_id_map[self.uplink_ports[index]]
                    if "TXQ" not in v:
                        self.sw_q += 1
                        value = self.get_sink_swq(parser, pipeline, k, index)
                    elif "TM" in v:
                        value = "TXQ{0}.0 TM{1}".format(port, index)
                    else:
                        value = "TXQ{0}.0".format(port)

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
            for index, _ in enumerate(self.uplink_ports):
                config = self.vpe_upstream(vnf_cfg, index)
                config.write(cfg_file)
                config = self.vpe_downstream(vnf_cfg, index)
                config = self.vpe_tmq(config, index)
                config.write(cfg_file)

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

    def generate_tm_cfg(self, vnf_cfg):
        vnf_cfg = os.path.join(vnf_cfg, "full_tm_profile_10G.cfg")
        if os.path.exists(vnf_cfg):
            return open(vnf_cfg).read()


class VpeApproxSetupEnvHelper(DpdkVnfSetupEnvHelper):

    APP_NAME = 'vPE_vnf'
    CFG_CONFIG = "/tmp/vpe_config"
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
        vpe_vars = {
            "bin_path": self.ssh_helper.bin_path,
            "socket": self.socket,
        }

        self._build_vnf_ports()
        vpe_conf = ConfigCreate(self.vnfd_helper, self.socket)
        vpe_conf.create_vpe_config(self.scenario_helper.vnf_cfg)

        config_basename = posixpath.basename(self.CFG_CONFIG)
        script_basename = posixpath.basename(self.CFG_SCRIPT)
        tm_basename = posixpath.basename(self.TM_CONFIG)
        with open(self.CFG_CONFIG) as handle:
            vpe_config = handle.read()

        self.ssh_helper.upload_config_file(config_basename, vpe_config.format(**vpe_vars))

        vpe_script = vpe_conf.generate_vpe_script(self.vnfd_helper.interfaces)
        self.ssh_helper.upload_config_file(script_basename, vpe_script.format(**vpe_vars))

        tm_config = vpe_conf.generate_tm_cfg(self.scenario_helper.vnf_cfg)
        self.ssh_helper.upload_config_file(tm_basename, tm_config)

        LOG.info("Provision and start the %s", self.APP_NAME)
        LOG.info(self.CFG_CONFIG)
        LOG.info(self.CFG_SCRIPT)
        self._build_pipeline_kwargs()
        return self.PIPELINE_COMMAND.format(**self.pipeline_kwargs)


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
        # we can't get KPIs if the VNF is down
        check_if_process_failed(self._vnf_process)
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
