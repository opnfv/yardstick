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
import time
import uuid

from yardstick.common import constants
from yardstick.common import exceptions
from yardstick.common import utils
from yardstick.network_services.vnf_generic.vnf import base as vnf_base


LOG = logging.getLogger(__name__)


class PktgenTrafficGen(vnf_base.GenericTrafficGen,
                       vnf_base.GenericVNFEndpoint):
    """DPDK Pktgen traffic generator

    Website: http://pktgen-dpdk.readthedocs.io/en/latest/index.html
    """

    TIMEOUT = 30

    def __init__(self, name, vnfd, task_id):
        vnf_base.GenericTrafficGen.__init__(self, name, vnfd, task_id)
        self.queue = multiprocessing.Queue()
        self._id = uuid.uuid1().int
        self._mq_producer = self._setup_mq_producer(self._id)
        vnf_base.GenericVNFEndpoint.__init__(self, self._id, [task_id],
                                             self.queue)
        self._consumer = vnf_base.GenericVNFConsumer([task_id], self)
        self._consumer.start_rpc_server()
        self._traffic_profile = None
        self._node_ip = vnfd['mgmt-interface'].get('ip')
        self._lua_node_port = self._get_lua_node_port(
            vnfd['mgmt-interface'].get('service_ports', []))
        self.rate = 1

    def instantiate(self, scenario_cfg, context_cfg):
        pass

    def run_traffic(self, traffic_profile):
        self._traffic_profile = traffic_profile
        self._traffic_profile.init(self._node_ip, self._lua_node_port)
        utils.wait_until_true(self._is_running, timeout=self.TIMEOUT,
                              sleep=2)

    def terminate(self):
        pass

    def collect_kpi(self):
        pass

    def scale(self, flavor=''):
        pass

    def wait_for_instantiate(self):
        pass

    def runner_method_start_iteration(self, ctxt, **kwargs):
        LOG.debug('Start method')
        #NOTE(ralonsoh): 'rate' should be modified between iterations. The
        #current implementation is just for testing.
        self.rate += 1
        self._traffic_profile.start()
        self._traffic_profile.rate(self.rate)
        time.sleep(4)
        self._traffic_profile.stop()
        self._mq_producer.tg_method_iteration(1, 1, {})

    def runner_method_stop_iteration(self, ctxt, **kwargs):
        LOG.debug('Stop method')

    @staticmethod
    def _get_lua_node_port(service_ports):
        for port in (port for port in service_ports if
                     int(port['port']) == constants.LUA_PORT):
            return int(port['node_port'])
        #NOTE(ralonsoh): in case LUA port is not present, an exception should
        #be raised.

    def _is_running(self):
        try:
            self._traffic_profile.help()
            return True
        except exceptions.PktgenActionError:
            return False
