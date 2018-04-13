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
import os
import time

from yardstick.common.messaging import consumer
from yardstick.common.messaging import payloads
from yardstick.common.messaging import producer
from yardstick.tests.functional import base


TOPIC = 'topic_MQ'
METHOD_INFO = 'info'


class DummyPayload(payloads.Payload):
    REQUIRED_FIELDS = {'version', 'data'}


class DummyEndpoint(consumer.NotificationHandler):

    def info(self, ctxt, **kwargs):
        if ctxt['pid'] in self._ctx_pids:
            self._queue.put('ID {}, data: {}, pid: {}'.format(
                self._id, kwargs['data'], ctxt['pid']))


class DummyConsumer(consumer.MessagingConsumer):

    def __init__(self, _id, ctx_pids, queue):
        self._id = _id
        endpoints = [DummyEndpoint(_id, ctx_pids, queue)]
        super(DummyConsumer, self).__init__(TOPIC, ctx_pids, endpoints)


class DummyProducer(producer.MessagingProducer):
    pass


def _run_consumer(_id, ctx_pids, queue):
    _consumer = DummyConsumer(_id, ctx_pids, queue)
    _consumer.start_rpc_server()
    _consumer.wait()


class MessagingTestCase(base.BaseFunctionalTestCase):

    @staticmethod
    def _terminate_consumers(num_consumers, processes):
        for i in range(num_consumers):
            processes[i].terminate()

    def test_run_five_consumers(self):
        output_queue = multiprocessing.Queue()
        num_consumers = 10
        ctx_1 = 100001
        ctx_2 = 100002
        producers = [DummyProducer(TOPIC, pid=ctx_1),
                     DummyProducer(TOPIC, pid=ctx_2)]

        processes = []
        for i in range(num_consumers):
            processes.append(multiprocessing.Process(
                name='consumer_{}'.format(i),
                target=_run_consumer,
                args=(i, [ctx_1, ctx_2], output_queue)))
            processes[i].start()
        self.addCleanup(self._terminate_consumers, num_consumers, processes)

        time.sleep(2)  # Let consumers to create the listeners
        for producer in producers:
            for message in ['message 0', 'message 1']:
                producer.send_message(METHOD_INFO,
                                      DummyPayload(version=1, data=message))

        time.sleep(2)  # Let consumers attend the calls
        output = []
        while not output_queue.empty():
            output.append(output_queue.get(True, 1))

        self.assertEqual(num_consumers * 4, len(output))
        msg_template = 'ID {}, data: {}, pid: {}'
        for i in range(num_consumers):
            for ctx in [ctx_1, ctx_2]:
                for message in ['message 0', 'message 1']:
                    msg = msg_template.format(i, message, ctx)
                    self.assertIn(msg, output)
