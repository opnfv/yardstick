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

import multiprocessing
import time
import uuid

import mock

from yardstick.common import messaging
from yardstick.common.messaging import payloads
from yardstick.common.messaging import producer
from yardstick.network_services.vnf_generic.vnf import base as vnf_base
from yardstick.tests.functional import base as ft_base


class _TrafficGenMQConsumer(vnf_base.GenericTrafficGen,
                            vnf_base.GenericVNFEndpoint):  # pragma: no cover

    def __init__(self, name, vnfd, task_id):
        vnf_base.GenericTrafficGen.__init__(self, name, vnfd, task_id)
        self.queue = multiprocessing.Queue()
        self._id = uuid.uuid1().int
        vnf_base.GenericVNFEndpoint.__init__(self, self._id, [task_id],
                                             self.queue)
        self._consumer = vnf_base.GenericVNFConsumer([task_id], self)
        self._consumer.start_rpc_server()

    def run_traffic(self, *args):
        pass

    def terminate(self):
        pass

    def collect_kpi(self):
        pass

    def instantiate(self, *args):
        pass

    def scale(self, flavor=''):
        pass

    def runner_method_start_iteration(self, ctxt, **kwargs):
        if ctxt['id'] in self._ctx_ids:
            self._queue.put(
                {'action': messaging.RUNNER_METHOD_START_ITERATION,
                 'payload': payloads.RunnerPayload.dict_to_obj(kwargs)})

    def runner_method_stop_iteration(self, ctxt, **kwargs):
        if ctxt['id'] in self._ctx_ids:
            self._queue.put(
                {'action': messaging.RUNNER_METHOD_STOP_ITERATION,
                 'payload': payloads.RunnerPayload.dict_to_obj(kwargs)})


class _DummyProducer(producer.MessagingProducer):
    pass


class GenericVNFMQConsumerTestCase(ft_base.BaseFunctionalTestCase):

    def test_fistro(self):
        vnfd = {'benchmark': {'kpi': mock.ANY},
                'vdu': [{'external-interface': 'ext_int'}]
                }
        task_id = uuid.uuid1().int
        tg_obj = _TrafficGenMQConsumer('name_tg', vnfd, task_id)
        producer = _DummyProducer(messaging.TOPIC_RUNNER, task_id)

        num_messages = 10
        for i in range(num_messages):
            pload = payloads.RunnerPayload(version=10, data=i)
            for method in (messaging.RUNNER_METHOD_START_ITERATION,
                           messaging.RUNNER_METHOD_STOP_ITERATION):
                producer.send_message(method, pload)

        time.sleep(0.5)  # Let consumers attend the calls
        output = []
        while not tg_obj.queue.empty():
            data = tg_obj.queue.get(True, 1)
            data_dict = {'action': data['action'],
                         'payload': data['payload'].obj_to_dict()}
            output.append(data_dict)

        self.assertEqual(num_messages * 2, len(output))
        for i in range(num_messages):
            pload = payloads.RunnerPayload(version=10, data=i).obj_to_dict()
            for method in (messaging.RUNNER_METHOD_START_ITERATION,
                           messaging.RUNNER_METHOD_STOP_ITERATION):
                reg = {'action': method, 'payload': pload}
                self.assertIn(reg, output)
