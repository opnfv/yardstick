# Copyright (c) 2018 Viosoft Corporation
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
import yaml
import os

from multiprocessing import Queue

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import DpdkVnfSetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper

LOG = logging.getLogger(__name__)


class PktgenParser(object):
    """ Class providing file-like API for talking with SSH connection """

    def __init__(self, q_out):
        self.queue = q_out
        self.closed = False

    def write(self, chunk):
        LOG.info("Parser called on %s", chunk)

    def close(self):
        """ close the ssh connection """
        self.closed = True

    def clear(self):
        """ clear queue till Empty """
        while self.queue.qsize() > 0:
            self.queue.get()


class VcmtsPktgenSetupEnvHelper(DpdkVnfSetupEnvHelper):

    def generate_pcap_filename(self, port_cfg):
        return port_cfg['traffic_type'] + "_" + port_cfg['num_subs'] \
             + "cms_" + port_cfg['num_ofdm'] + "ofdm.pcap"

    def find_port_cfg(self, ports_cfg, port_name):
        for port_cfg in ports_cfg:
            if port_name in port_cfg:
                return port_cfg
        return None

    def build_pktgen_parameters(self, pod_cfg):
        ports_cfg = pod_cfg['ports']
        port_cfg = [
            self.find_port_cfg(ports_cfg, 'port_0'),
            self.find_port_cfg(ports_cfg, 'port_1'),
            self.find_port_cfg(ports_cfg, 'port_2'),
            self.find_port_cfg(ports_cfg, 'port_3'),
            self.find_port_cfg(ports_cfg, 'port_4'),
            self.find_port_cfg(ports_cfg, 'port_5'),
            self.find_port_cfg(ports_cfg, 'port_6'),
            self.find_port_cfg(ports_cfg, 'port_7')
        ]

        return "/pktgen-config/setup.sh " + pod_cfg['pktgen_id']\
             + " " + pod_cfg['num_ports'] \
             + " " + port_cfg[0]['net_pktgen'] \
             + " " + port_cfg[1]['net_pktgen'] \
             + " " + port_cfg[2]['net_pktgen'] \
             + " " + port_cfg[3]['net_pktgen'] \
             + " " + port_cfg[4]['net_pktgen'] \
             + " " + port_cfg[5]['net_pktgen'] \
             + " " + port_cfg[6]['net_pktgen'] \
             + " " + port_cfg[7]['net_pktgen'] \
             + " " + self.generate_pcap_filename(port_cfg[0]) \
             + " " + self.generate_pcap_filename(port_cfg[1]) \
             + " " + self.generate_pcap_filename(port_cfg[2]) \
             + " " + self.generate_pcap_filename(port_cfg[3]) \
             + " " + self.generate_pcap_filename(port_cfg[4]) \
             + " " + self.generate_pcap_filename(port_cfg[5]) \
             + " " + self.generate_pcap_filename(port_cfg[6]) \
             + " " + self.generate_pcap_filename(port_cfg[7])

    def build_cmd(self, pod_cfg):
        self.cmd = self.build_pktgen_parameters(pod_cfg)

    def setup_vnf_environment(self):
        pass


class VcmtsPktgenResourceHelper(ClientResourceHelper):

    def __init__(self, setup_helper):
        super(VcmtsPktgenResourceHelper, self).__init__(setup_helper)
        self._queue = Queue()
        self._parser = PktgenParser(self._queue)

    def run_traffic(self, traffic_profile, *args):
        self.client_started.value = 1
        LOG.debug("Executing: '%s'", self.setup_helper.cmd)
        self.ssh_helper.run(self.setup_helper.cmd,
                            stdout=self._parser,
                            keep_stdin_open=True, pty=True)


class VcmtsPktgen(SampleVNFTrafficGen):

    TG_NAME = 'VcmtsPktgen'
    APP_NAME = 'VcmtsPktgen'
    RUN_WAIT = 4

    def __init__(self, name, vnfd, task_id, setup_env_helper_type=None,
                 resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = VcmtsPktgenSetupEnvHelper
        if resource_helper_type is None:
            resource_helper_type = VcmtsPktgenResourceHelper
        super(VcmtsPktgen, self).__init__(
            name, vnfd, task_id, setup_env_helper_type, resource_helper_type)
        self._result = {}

    def read_yaml_file(self, path):
        """Read yaml file"""
        with open(path) as stream:
            data = yaml.load(stream, Loader=yaml.BaseLoader)
            return data

    def extract_pod_cfg(self, pktgen_pods_cfg, pktgen_id):
        for pod_cfg in pktgen_pods_cfg:
            if pod_cfg['pktgen_id'] == pktgen_id:
                return pod_cfg
        LOG.error("Pkgen with id %s not found", pktgen_id)
        return None

    def instantiate(self, scenario_cfg, context_cfg):
        super(VcmtsPktgen, self).instantiate(scenario_cfg, context_cfg)
        self._start_server()
        pktgen_values_filepath = scenario_cfg['options']['pktgen_values']
        if not os.path.isfile(pktgen_values_filepath):
            LOG.exception("pktgen_values file provided (%s) does not exists",
                          pktgen_values_filepath)

        pktgen_id = str(scenario_cfg['options'][self.name]['pktgen_id'])

        pktgen_values = self.read_yaml_file(pktgen_values_filepath)
        pktgen_pods_cfg = pktgen_values['topology']['pktgen_pods']

        pod_cfg = self.extract_pod_cfg(pktgen_pods_cfg, pktgen_id)
        self.setup_helper.build_cmd(pod_cfg)
        self.setup_helper.setup_vnf_environment()
