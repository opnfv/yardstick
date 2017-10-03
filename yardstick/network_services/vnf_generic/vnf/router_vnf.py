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
""" Base class implementation for generic vnf implementation """

from __future__ import absolute_import
import logging
import time
from netaddr import *

from yardstick.benchmark.scenarios.networking.vnf_generic import find_relative_file
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF, \
 DpdkVnfSetupEnvHelper, ScenarioHelper, VnfSshHelper
from yardstick.network_services.yang_model import YangModel

LOG = logging.getLogger(__name__)

class RouterVNFDeployHelper(object):

    def __init__(self, vnfd_helper, ssh_helper):
        super(RouterVNFDeployHelper, self).__init__()
        self.ssh_helper = ssh_helper
        self.vnfd_helper = vnfd_helper

    def deploy_vnfs(self, app_name, scenario_cfg, context_cfg):
        # Configure IP of dtaplane ports
        # TODO:
        #LOG.debug(scenario_cfg['options'])
        # CONTEXT =  local_ip
        # TODO:
        # Get the local_ip from context_cfg and assign to the data ports
        exit_status = self.ssh_helper.execute("/sbin/ip addr replace 152.16.100.19/24 dev dp0s10")
        exit_status = self.ssh_helper.execute("/sbin/ip addr replace 152.16.40.19/24 dev dp0s11")

        # Configure static ARP entries
        # SSH or REST API calls        
        # TODO:
        # for ip in {26..105}
        # do
        #  arp -i $NIC1 -s 152.16.101.${ip} $TH_NIC1_MAC
        #done
        LOG.debug("SCENARIO")
        LOG.debug(scenario_cfg)
        LOG.debug("FLOW")
        # Flow contains:
        # {'src_ip': ['152.16.100.26-152.16.100.27'], 'dst_ip': ['152.16.40.26-152.16.40.27'], 'count': 2}
        LOG.debug(scenario_cfg['options']['flow'])
        if "flow" in scenario_cfg['options']:
            src_ips = scenario_cfg['options']['flow']['src_ip']
            dst_ips = scenario_cfg['options']['flow']['dst_ip']

        range1 = src_ips[0].split('-')
        range2 = dst_ips[0].split('-')

        if len(range1) > 1:
            range1 = IPRange(a[0], a[1])

        if len(range2) > 1:
            range2 = IPRange(b[0], b[1])

        addrs = list(range1)
        addrs2 = list(range2)

        LOG.debug("CONTEXT")
        LOG.debug(context_cfg)
        for a in addrs:
            arp_status = self.ssh_helper.execute("/sbin/ip neigh add %s lladdr 90:e2:ba:bf:8a:10 dev dp0s10 nud perm" % str(a))

        for b in addrs2:
            arp2_status = self.ssh_helper.execute("/sbin/ip neigh add %s lladdr 90:e2:ba:bf:8a:40 dev dp0s11 nud perm" % str(b))

        arp_status = self.ssh_helper.execute("arp -a")
        LOG.debug('arp %s', arp2_status)

class RouterVNF(SampleVNF):

    WAIT_TIME = 1

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        super(RouterVNF, self).__init__(name, vnfd)
        self.bin_path = '' 
        self.scenario_helper = ScenarioHelper(self.name)
        self.ssh_helper = VnfSshHelper(self.vnfd_helper.mgmt_interface, self.bin_path)

        if setup_env_helper_type is None:
            setup_env_helper_type = DpdkVnfSetupEnvHelper
        self.setup_helper = setup_env_helper_type(self.vnfd_helper,
                                                  self.ssh_helper,
                                                  self.scenario_helper)

        self.deploy_helper = RouterVNFDeployHelper(vnfd, self.ssh_helper)

        #if resource_helper_type is None:
        #    resource_helper_type = ResourceHelper

        #self.resource_helper = resource_helper_type(self.setup_helper)

        self.context_cfg = None
        self.nfvi_context = None
        self.pipeline_kwargs = {}
        self.uplink_ports = None
        self.downlink_ports = None
        # TODO(esm): make QueueFileWrapper invert-able so that we
        #            never have to manage the queues
        #self.q_in = Queue()
        #self.q_out = Queue()
        self.queue_wrapper = None
        self.run_kwargs = {}
        self.used_drivers = {}
        self.vnf_port_pairs = None
        self._vnf_process = None


    def instantiate(self, scenario_cfg, context_cfg):
        self.scenario_helper.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        #self.nfvi_context = Context.get_context_from_server(self.scenario_helper.nodes[self.name])
        # self.nfvi_context = None
        LOG.info(self.scenario_helper.nodes)
        self.deploy_helper.deploy_vnfs("RouterVNF", scenario_cfg, context_cfg)

        #self.resource_helper.setup()
        #self._start_vnf()

    def wait_for_instantiate(self):
        buf = []
        time.sleep(self.WAIT_TIME)  # Give some time for config to load
        return 0

    def _run(self):
        # we can't share ssh paramiko objects to force new connection
        self.ssh_helper.drop_connection()
        cmd = self._build_config()
        # kill before starting
        self.setup_helper.kill_vnf()

        LOG.debug(cmd)
        self._build_run_kwargs()
        self.ssh_helper.run(cmd, **self.run_kwargs)

    def terminate(self):
        if self._vnf_process:
            self._vnf_process.terminate()
        self.setup_helper.kill_vnf()
        self._tear_down()
        self.resource_helper.stop_collect()

    def get_stats(self, *args, **kwargs):
        """
        Method for checking the statistics

        :return:
           VNF statistics
        """
        #cmd = 'p {0} stats'.format(self.APP_WORD)
        #out = self.vnf_execute(cmd)
        out = {"result":0} 
        return out

    def collect_kpi(self):
        stats = self.get_stats()
        #m = re.search(self.COLLECT_KPI, stats, re.MULTILINE)
        #if m:
        #    result = {k: int(m.group(v)) for k, v in self.COLLECT_MAP.items()}
        #    result["collect_stats"] = self.resource_helper.collect_kpi()
        #else:
        result = {
            "packets_in": 0,
            "packets_fwd": 0,
            "packets_dropped": 0,
        }
        LOG.debug("%s collect KPIs %s", "RouterVNF", result)
        return result

