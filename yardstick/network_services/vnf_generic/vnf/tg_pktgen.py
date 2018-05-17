# Copyright (c) 2018 Intel Corporation
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
import os

import yaml

from yardstick.benchmark.contexts import base as context_base
from yardstick.common import exceptions
from yardstick.common import utils
from yardstick.common.utils import mac_address_to_hex_list, try_int
from yardstick.network_services.utils import get_nsb_option

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import DpdkVnfSetupEnvHelper

from yardstick.network_services.vnf_generic.vnf import base


LOG = logging.getLogger(__name__)


class PktgenCtl(object):

    def __init__(self, host, port):
        """DPDK Pktgen controller class

        :param host: (str) ip or host name
        :param port: (int) TCP socket port number for Lua commands
        """
        self._host = host
        self._port = port

    def start(self):
        if utils.send_socket_command(self._host, self._port,
                                     'pktgen.start("0")') != 0:
            raise exceptions.PktgenActionError(action='start')

    def stop(self):
        if utils.send_socket_command(self._host, self._port,
                                     'pktgen.stop("0")') != 0:
            raise exceptions.PktgenActionError(action='stop')

    def rate(self, rate):
        command = 'pktgen.set("0", "rate", ' + str(rate) + ')'
        if utils.send_socket_command(self._host, self._port, command) != 0:
            raise exceptions.PktgenActionError(action='rate')




class PktgenResourceHelper(object):

    LUA_PORT_NAME = 'lua'

    def __init__(self, pktgen_context):
        self._context = pktgen_context
        self._k8s_template = pktgen_context.template

    def get_lua_port(self):
        # Esto esta en node_ports = []
        # node_ports = self._context.get('node_ports', [])
        # for node_port in (node_port for node_port in node_ports
        #                   if node_port.get('name') == self.LUA_PORT_NAME):
        #     return node_port['port']
        # return None
        name = get_from_context
        service_name = '{}-service'.format(name)
        pass

    def get_lua_host(self):
        pass


class PktgenTrafficGen(base.GenericTrafficGen):
    """DPDK Pktgen traffic generator

    Website: http://pktgen-dpdk.readthedocs.io/en/latest/index.html
    """

    #APP_NAME = 'Pktgen'

    def __init__(self, name, vnfd):
        self._context = None
        self._name = name
        self._resource_helper = None
        super(PktgenTrafficGen, self).__init__(name, vnfd)

    def instantiate(self, scenario_cfg, context_cfg):
        """Para empezar, meter probar cosas...."""
        # Leer cluster IP y puerto Lua. https://gerrit.opnfv.org/gerrit/#/c/57529/
        # --> node_ports: name=lua
        self._context = context_base.Context.get_context_from_server(
            self.scenario_helper.nodes[self._name])
        self._resource_helper = PktgenResourceHelper(self._context)

    def run_traffic(self, traffic_profile):
        # traffic_profile no se usa?? ya veremos.
        # 1) set rate
        # 2) start
        pass

    def wait_for_instantiate(self):
        # Que hacemos?
        pass

    # def _check_status(self):
    #     return self.resource_helper.check_status()
    #
    # def _start_server(self):
    #     super(TrexTrafficGen, self)._start_server()
    #     self.resource_helper.start()
    #



    def terminate(self):
        pass
