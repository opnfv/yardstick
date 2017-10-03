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
""" Add generic L3 forwarder implementation based on sample_vnf.py"""

from __future__ import absolute_import
import logging
import time
import itertools
from netaddr import IPRange

from yardstick.benchmark.contexts.base import Context
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF, \
    DpdkVnfSetupEnvHelper, ScenarioHelper, VnfSshHelper, ResourceHelper

LOG = logging.getLogger(__name__)


class RouterVNFDeployHelper(object):

    def __init__(self, vnfd_helper, ssh_helper):
        super(RouterVNFDeployHelper, self).__init__()
        self.ssh_helper = ssh_helper
        self.vnfd_helper = vnfd_helper

    def configure_routes(self, node_name, scenario_cfg, context_cfg):
        # Configure IP of dataplane ports and add static ARP entries
        #
        # This function should be modified to configure a 3rd party/commercial VNF.
        # The current implementation works on a Linux based VNF with "ip" command.
        #
        # Flow contains:
        # {'src_ip': ['152.16.100.26-152.16.100.27'],
        #  'dst_ip': ['152.16.40.26-152.16.40.27'], 'count': 2}

        ifaces = []
        dst_macs = []

        ip_cmd_replace = '/sbin/ip addr replace %s/24 dev %s'
        ip_cmd_up = '/sbin/ip link set %s up'
        ip_cmd_flush = '/sbin/ip address flush dev %s'

        # Get VNF IPs from test case file
        for key, value in context_cfg['nodes'][node_name]['interfaces'].items():
            dst_macs.append(value['dst_mac'])

            # Get the network interface name using local_mac
            iname = self.ssh_helper.execute("/sbin/ip a |grep -B 1 %s | head -n 1"
                                            % (value['local_mac']))
            iname = iname[1].split(":")[1].strip()
            ifaces.append(iname)

            self.ssh_helper.execute(ip_cmd_flush % (iname))

            # Get the local_ip from context_cfg and assign to the data ports
            self.ssh_helper.execute(ip_cmd_replace % (str(value['local_ip']),
                                    iname))
            # Enable interface
            self.ssh_helper.execute(ip_cmd_up % (iname))
            time.sleep(2)

        # Configure static ARP entries for each IP
        # using SSH or REST API calls
        try:
            src_ips = scenario_cfg['options']['flow']['src_ip']
            dst_ips = scenario_cfg['options']['flow']['dst_ip']
        except KeyError:
            raise KeyError("Missing flow definition in scenario section" +
                           " of the task definition file")

        # Multiport
        ip_ranges = []
        for src, dst in itertools.izip(src_ips, dst_ips):
            range1 = itertools.cycle(iter(src.split('-')))
            range2 = itertools.cycle(iter(dst.split('-')))

            range1 = IPRange(next(range1), next(range1))
            range2 = IPRange(next(range2), next(range2))
            ip_ranges.append(range1)
            ip_ranges.append(range2)

        ip_cmd = '/sbin/ip neigh add %s lladdr %s dev %s nud perm'
        for idx , iface in enumerate(ifaces):
            for addr in ip_ranges[idx]:
                self.ssh_helper.execute(ip_cmd % (addr, dst_macs[idx], iface))

        arp_status = self.ssh_helper.execute("arp -a -n")
        LOG.debug('arp %s', arp_status)


class RouterVNF(SampleVNF):

    WAIT_TIME = 1

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = DpdkVnfSetupEnvHelper

        # For heat test cases
        vnfd['mgmt-interface'].pop("pkey", "")
        vnfd['mgmt-interface']['password'] = 'password'

        super(RouterVNF, self).__init__(name, vnfd, setup_env_helper_type, resource_helper_type)

        self.deploy_helper = RouterVNFDeployHelper(vnfd, self.ssh_helper)

    def instantiate(self, scenario_cfg, context_cfg):
        self.scenario_helper.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.nfvi_context = Context.get_context_from_server(self.scenario_helper.nodes[self.name])
        self.deploy_helper.configure_routes(self.name, scenario_cfg, context_cfg)

    def wait_for_instantiate(self):
        time.sleep(self.WAIT_TIME)

    def _run(self):
        # we can't share ssh paramiko objects to force new connection
        self.ssh_helper.drop_connection()

    def terminate(self):
        self._tear_down()
        self.resource_helper.stop_collect()

    def collect_kpi(self):
        # TODO: Implement stats collection
        # One option is to use:
        # ip_link_stats = '/sbin/ip -s link'
        # link_stats = self.ssh_helper.execute(ip_link_stats)
        # TODO: get RX/TX from link_stats and assign to results

        result = {
            "packets_in": 0,
            "packets_dropped": 0,
            "packets_fwd": 0
        }

        LOG.debug("%s collect KPIs %s", "RouterVNF", result)
        return result
