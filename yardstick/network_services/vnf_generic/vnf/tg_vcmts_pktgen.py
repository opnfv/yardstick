# Copyright (c) 2019 Viosoft Corporation
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
import time
import socket
import yaml
import os

from yardstick.network_services.vnf_generic.vnf import sample_vnf


LOG = logging.getLogger(__name__)


class PktgenHelper(object):

    RETRY_SECONDS = 0.5
    RETRY_COUNT = 20

    def __init__(self, host, port=23000):
        self.host = host
        self.port = port
        self.connected = False

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
        if self.connected:
            return True
        LOG.info("Connecting to pktgen instance at %s...", self.host)
        for idx in range(self.RETRY_COUNT):
            self.connected = self._connect()
            if self.connected:
                return True
            LOG.debug("Connection attempt %d: Unable to connect to %s, retrying in %d seconds",
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


class VcmtsPktgenSetupEnvHelper(sample_vnf.SetupEnvHelper):

    BASE_PARAMETERS = "export LUA_PATH=/vcmts/Pktgen.lua;"\
                    + "export CMK_PROC_FS=/host/proc;"

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
        cmd = self.build_pktgen_parameters(pod_cfg)
        LOG.debug("Executing: '%s'", cmd)
        self.ssh_helper.send_command(cmd)
        LOG.info("Pktgen executed")

    def setup_vnf_environment(self):
        pass


class VcmtsPktgen(sample_vnf.SampleVNFTrafficGen):

    TG_NAME = 'VcmtsPktgen'
    APP_NAME = 'VcmtsPktgen'
    RUN_WAIT = 4
    DEFAULT_RATE = 8.0

    PKTGEN_BASE_PORT = 23000

    def __init__(self, name, vnfd, task_id, setup_env_helper_type=None,
                 resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = VcmtsPktgenSetupEnvHelper
        super(VcmtsPktgen, self).__init__(
            name, vnfd, task_id, setup_env_helper_type, resource_helper_type)

        self.pktgen_address = vnfd['mgmt-interface']['ip']
        LOG.info("Pktgen container '%s', IP: %s", name, self.pktgen_address)

    def extract_pod_cfg(self, pktgen_pods_cfg, pktgen_id):
        for pod_cfg in pktgen_pods_cfg:
            if pod_cfg['pktgen_id'] == pktgen_id:
                return pod_cfg
        return None

    def instantiate(self, scenario_cfg, context_cfg):
        super(VcmtsPktgen, self).instantiate(scenario_cfg, context_cfg)
        self._start_server()
        options = scenario_cfg.get('options', {})
        self.pktgen_rate = options.get('pktgen_rate', self.DEFAULT_RATE)

        try:
            pktgen_values_filepath = options['pktgen_values']
        except KeyError:
            raise KeyError("Missing pktgen_values key in scenario options" \
                           "section of the task definition file")

        if not os.path.isfile(pktgen_values_filepath):
            raise RuntimeError("The pktgen_values file path provided " \
                               "does not exists")

        with open(pktgen_values_filepath) as stream:
            pktgen_values = yaml.load(stream, Loader=yaml.BaseLoader)

        if pktgen_values == None:
            raise RuntimeError("Error reading pktgen_values file provided (" +
                               pktgen_values_filepath + ")")

        self.pktgen_id = int(options[self.name]['pktgen_id'])
        self.resource_helper.pktgen_id = self.pktgen_id

        self.pktgen_helper = PktgenHelper(self.pktgen_address,
                                          self.PKTGEN_BASE_PORT + self.pktgen_id)

        pktgen_pods_cfg = pktgen_values['topology']['pktgen_pods']

        self.pod_cfg = self.extract_pod_cfg(pktgen_pods_cfg,
                                            str(self.pktgen_id))

        if self.pod_cfg == None:
            raise KeyError("Pktgen with id " + str(self.pktgen_id) + \
                           " was not found")

        self.setup_helper.start_pktgen(self.pod_cfg)

    def run_traffic(self, traffic_profile):
        if not self.pktgen_helper.connect():
            raise IOError("Could not connect to pktgen")
        LOG.info("Connected to pktgen instance at %s", self.pktgen_address)

        commands = []
        for i in range(8):
            commands.append('pktgen.set("' + str(i) + '", "rate", ' +
                            "%0.1f" % self.pktgen_rate + ');')

        commands.append('pktgen.start("all");')

        for command in commands:
            if self.pktgen_helper.send_command(command):
                LOG.debug("Command '%s' sent to pktgen", command)
        LOG.info("Traffic started on %s...", self.name)
        return True
