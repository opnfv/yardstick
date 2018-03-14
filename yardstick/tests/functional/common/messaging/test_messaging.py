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
        if ctxt['pid'] == self._ctx_pid:
            self._queue.put('ID {}, data: {}'.format(self._id, kwargs['data']))


class DummyConsumer(consumer.MessagingConsumer):

    def __init__(self, id, ctx_pid, queue):
        self._id = id
        endpoints = [DummyEndpoint(id, ctx_pid, queue)]
        super(DummyConsumer, self).__init__(TOPIC, ctx_pid, endpoints)


class DummyProducer(producer.MessagingProducer):
    pass


def _run_consumer(id, ctx_pid, queue):
    _consumer = DummyConsumer(id, ctx_pid, queue)
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
        ctx_id = os.getpid()
        producer = DummyProducer(TOPIC, pid=ctx_id)

        processes = []
        for i in range(num_consumers):
            processes.append(multiprocessing.Process(
                name='consumer_{}'.format(i),
                target=_run_consumer,
                args=(i, ctx_id, output_queue)))
            processes[i].start()
        self.addCleanup(self._terminate_consumers, num_consumers, processes)

        time.sleep(2)  # Let consumers to create the listeners
        producer.send_message(METHOD_INFO, DummyPayload(version=1,
                                                        data='message 0'))
        producer.send_message(METHOD_INFO, DummyPayload(version=1,
                                                        data='message 1'))
        time.sleep(2)  # Let consumers attend the calls

        output = []
        while not output_queue.empty():
            output.append(output_queue.get(True, 1))

        self.assertEqual(num_consumers * 2, len(output))
        for i in range(num_consumers):
            self.assertIn('ID {}, data: {}'.format(1, 'message 0'), output)
            self.assertIn('ID {}, data: {}'.format(1, 'message 1'), output)
