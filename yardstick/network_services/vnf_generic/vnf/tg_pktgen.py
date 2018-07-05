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
import multiprocessing
import os
import uuid

import yaml

from yardstick.benchmark.contexts import base as context_base
from yardstick.common import exceptions
from yardstick.common import utils
from yardstick.common.utils import mac_address_to_hex_list, try_int
from yardstick.network_services.utils import get_nsb_option

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import DpdkVnfSetupEnvHelper

from yardstick.network_services.vnf_generic.vnf import base as vnf_base


LOG = logging.getLogger(__name__)


# class PktgenCtl(object):
#
#     def __init__(self, host, port):
#         """DPDK Pktgen controller class
#
#         :param host: (str) ip or host name
#         :param port: (int) TCP socket port number for Lua commands
#         """
#         self._host = host
#         self._port = port
#
#     def start(self):
#         if utils.send_socket_command(self._host, self._port,
#                                      'pktgen.start("0")') != 0:
#             raise exceptions.PktgenActionError(action='start')
#
#     def stop(self):
#         if utils.send_socket_command(self._host, self._port,
#                                      'pktgen.stop("0")') != 0:
#             raise exceptions.PktgenActionError(action='stop')
#
#     def rate(self, rate):
#         command = 'pktgen.set("0", "rate", ' + str(rate) + ')'
#         if utils.send_socket_command(self._host, self._port, command) != 0:
#             raise exceptions.PktgenActionError(action='rate')
#


#
# class PktgenResourceHelper(object):
#
#     LUA_PORT_NAME = 'lua'
#
#     def __init__(self, pktgen_context):
#         self._context = pktgen_context
#         self._k8s_template = pktgen_context.template
#
#     def get_lua_port(self):
#         # Esto esta en node_ports = []
#         # node_ports = self._context.get('node_ports', [])
#         # for node_port in (node_port for node_port in node_ports
#         #                   if node_port.get('name') == self.LUA_PORT_NAME):
#         #     return node_port['port']
#         # return None
#         name = get_from_context
#         service_name = '{}-service'.format(name)
#         pass
#
#     def get_lua_host(self):
#         pass


class PktgenTrafficGen(vnf_base.GenericTrafficGen,
                       vnf_base.GenericVNFEndpoint):
    """DPDK Pktgen traffic generator

    Website: http://pktgen-dpdk.readthedocs.io/en/latest/index.html
    """

    ###APP_NAME = 'Pktgen'

    def __init__(self, name, vnfd, task_id):
        #self._context = None
        #self._resource_helper = None
        vnf_base.GenericTrafficGen.__init__(self, name, vnfd, task_id)
        self.queue = multiprocessing.Queue()
        self._id = uuid.uuid1().int
        vnf_base.GenericVNFEndpoint.__init__(self, self._id, [task_id],
                                             self.queue)
        self._consumer = vnf_base.GenericVNFConsumer([task_id], self)
        self._consumer.start_rpc_server()

    def instantiate(self, scenario_cfg, context_cfg):
        pass


    def run_traffic(self, traffic_profile):
        pass

    def terminate(self):
        pass

    def collect_kpi(self):
        pass

    def scale(self, flavor=''):
        pass

    def wait_for_instantiate(self):
        pass

    def runner_method_start_iteration(self, ctxt, **kwargs):
        # pragma: no cover
        LOG.error("Start method")
        pass
        # if ctxt['id'] in self._ctx_ids:
        #     self._queue.put(
        #         {'action': messaging.RUNNER_METHOD_START_ITERATION,
        #          'payload': payloads.RunnerPayload.dict_to_obj(kwargs)})

    def runner_method_stop_iteration(self, ctxt, **kwargs):
        LOG.error("Stop method")
        pass

        # if ctxt['id'] in self._ctx_ids:
        #     self._queue.put(
        #         {'action': messaging.RUNNER_METHOD_STOP_ITERATION,
        #          'payload': payloads.RunnerPayload.dict_to_obj(kwargs)})



