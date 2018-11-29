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
import time
import socket

from multiprocessing import Queue

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper

LOG = logging.getLogger(__name__)


class PktgenHelper(object):

    RETRY_SECONDS = 8

    def __init__(self, host, port=23000):
        self.host = host
        self.port = port

    def _connect(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ret = True
        try:
            self._sock.settimeout(5)
            self._sock.connect((self.host, self.port))
        except Exception:   # pylint: disable=broad-except
            self._sock.close()
            ret = False

        return ret

    def connect(self):
        for idx in range(4):
            self.connected = self._connect()
            if self.connected:
                return True
            LOG.info("Connection attempt %d: Unable to connect to %s, retrying in %d seconds",
                     idx, self.host, self.RETRY_SECONDS)
            time.sleep(self.RETRY_SECONDS)

        LOG.error("Error, Unable to connect to pktgen instance on %s !",
                  self.host)
        return False


    def send_command(self, command):
        if not self.connected:
            raise IOError("Pktgen socket is not connected")

        ret = True

        try:
            self._sock.sendall(command + "\n")
            time.sleep(1)
        except Exception as e:   # pylint: disable=broad-except
            LOG.error("Error sending command '%s': %s", command, e)
            ret = False

        return ret


class VcmtsPktgenSetupEnvHelper(SetupEnvHelper):

    BASE_PARAMETERS = "export LUA_PATH=/vcmts/Pktgen.lua;"\
                    + "export CMK_PROC_FS=/host/proc;"

    def __init__(self, vnfd_helper, ssh_helper, scenario_helper):
        super(VcmtsPktgenSetupEnvHelper, self).__init__(vnfd_helper, ssh_helper, scenario_helper)
        self.pktgen_address = vnfd_helper['mgmt-interface']['ip']

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

        pktgen_parameters = self.BASE_PARAMETERS + " " \
             + " /pktgen-config/setup.sh " + pod_cfg['pktgen_id'] \
             + " " + pod_cfg['num_ports']

        for i in range(8):
            pktgen_parameters += " " + port_cfg[i]['net_pktgen']

        for i in range(8):
            pktgen_parameters += " " + self.generate_pcap_filename(port_cfg[i])

        return pktgen_parameters

    def start_pktgen(self, pod_cfg):
        self.cmd = self.build_pktgen_parameters(pod_cfg)
        self._queue = Queue()
        self.ssh_helper.send_command(self.cmd)
        time.sleep(10)
        self.pktgen_helper = PktgenHelper(self.pktgen_address)
        if not self.pktgen_helper.connect():
            raise IOError("Could not connect to pktgen, unable to send commands")
        LOG.info("Connected to pktgen instance at %s", self.pktgen_address)

    def setup_vnf_environment(self):
        pass


class VcmtsPktgenResourceHelper(ClientResourceHelper):

    def __init__(self, setup_helper):
        super(VcmtsPktgenResourceHelper, self).__init__(setup_helper)
        self._queue = Queue()

    def run_traffic(self, traffic_profile, *args):
        self.client_started.value = 1
        LOG.info("Starting traffic...")

        commands = [
            'pktgen.start("all");'
        ]

        for command in commands:
            if self.setup_helper.pktgen_helper.send_command(command):
                LOG.info("Command '%s' sent to pktgen", command)


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

        LOG.info("Pktgen container '%s', IP: %s", name, vnfd['mgmt-interface']['ip'])
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
        self.setup_helper.start_pktgen(pod_cfg)
