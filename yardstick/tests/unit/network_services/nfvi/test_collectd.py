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

from __future__ import absolute_import
import unittest
import multiprocessing
import mock

from yardstick.network_services.nfvi.collectd import AmqpConsumer


class TestAmqpConsumer(unittest.TestCase):
    def setUp(self):
        self.queue = multiprocessing.Queue()
        self.url = 'amqp://admin:admin@127.0.0.1:5672/%2F'
        self.amqp_consumer = AmqpConsumer(self.url, self.queue)

    def test___init__(self):
        self.assertEqual(self.url, self.amqp_consumer._url)

    def test_on_connection_open(self):
        self.amqp_consumer._connection = mock.Mock(autospec=AmqpConsumer)
        self.amqp_consumer._connection.add_on_close_callback = \
            mock.Mock(return_value=0)
        self.amqp_consumer._connection.channel = mock.Mock(return_value=0)
        self.assertEqual(None, self.amqp_consumer.on_connection_open(10))

    def test_on_connection_closed(self):
        self.amqp_consumer._connection = mock.Mock(autospec=AmqpConsumer)
        self.amqp_consumer._connection.ioloop = mock.Mock()
        self.amqp_consumer._connection.ioloop.stop = mock.Mock(return_value=0)
        self.amqp_consumer._connection.add_timeout = mock.Mock(return_value=0)
        self.amqp_consumer._closing = True
        self.assertEqual(None,
                         self.amqp_consumer.on_connection_closed("", 404,
                                                                 "Not Found"))
        self.amqp_consumer._closing = False
        self.assertEqual(None,
                         self.amqp_consumer.on_connection_closed("", 404,
                                                                 "Not Found"))

    def test_reconnect(self):
        self.amqp_consumer._connection = mock.Mock(autospec=AmqpConsumer)
        self.amqp_consumer._connection.ioloop = mock.Mock()
        self.amqp_consumer._connection.ioloop.stop = mock.Mock(return_value=0)
        self.amqp_consumer.connect = mock.Mock(return_value=0)
        self.amqp_consumer._closing = True
        self.assertEqual(None, self.amqp_consumer.reconnect())

    def test_on_channel_open(self):
        self.amqp_consumer._connection = mock.Mock(autospec=AmqpConsumer)
        self.amqp_consumer._connection.add_on_close_callback = \
            mock.Mock(return_value=0)
        self.amqp_consumer._channel = mock.Mock()
        self.amqp_consumer.add_on_channel_close_callback = mock.Mock()
        self.amqp_consumer._channel.exchange_declare = \
            mock.Mock(return_value=0)
        self.assertEqual(None,
                         self.amqp_consumer.on_channel_open(
                             self.amqp_consumer._channel))

    def test_add_on_channel_close_callback(self):
        self.amqp_consumer._connection = mock.Mock(autospec=AmqpConsumer)
        self.amqp_consumer._connection.add_on_close_callback = \
            mock.Mock(return_value=0)
        self.amqp_consumer._channel = mock.Mock()
        self.amqp_consumer._channel.add_on_close_callback = mock.Mock()
        self.assertEqual(None,
                         self.amqp_consumer.add_on_channel_close_callback())

    def test_on_channel_closed(self):
        self.amqp_consumer._connection = mock.Mock(autospec=AmqpConsumer)
        self.amqp_consumer._connection.close = mock.Mock(return_value=0)
        _channel = mock.Mock()
        self.assertEqual(None,
                         self.amqp_consumer.on_channel_closed(_channel,
                                                              "", ""))

    def test_ion_exchange_declareok(self):
        self.amqp_consumer.setup_queue = mock.Mock(return_value=0)
        self.assertEqual(None, self.amqp_consumer.on_exchange_declareok(10))

    def test_setup_queue(self):
        self.amqp_consumer._channel = mock.Mock()
        self.amqp_consumer._channel.add_on_close_callback = mock.Mock()
        self.assertEqual(None, self.amqp_consumer.setup_queue("collectd"))

    def test_on_queue_declareok(self):
        self.amqp_consumer._channel = mock.Mock()
        self.amqp_consumer._channel.queue_bind = mock.Mock()
        self.assertEqual(None, self.amqp_consumer.on_queue_declareok(10))

    def test__on_bindok(self):
        self.amqp_consumer._channel = mock.Mock()
        self.amqp_consumer._channel.basic_consume = mock.Mock()
        self.amqp_consumer.add_on_cancel_callback = mock.Mock()
        self.assertEqual(None, self.amqp_consumer._on_bindok(10))

    def test_add_on_cancel_callback(self):
        self.amqp_consumer._channel = mock.Mock()
        self.amqp_consumer._channel.add_on_cancel_callback = mock.Mock()
        self.assertEqual(None, self.amqp_consumer.add_on_cancel_callback())

    def test_on_consumer_cancelled(self):
        self.amqp_consumer._channel = mock.Mock()
        self.amqp_consumer._channel.close = mock.Mock()
        self.assertEqual(None, self.amqp_consumer.on_consumer_cancelled(10))

    def test_on_message(self):
        body = "msg {} cpu/cpu-0/ipc 101010:10"
        properties = ""
        basic_deliver = mock.Mock()
        basic_deliver.delivery_tag = mock.Mock(return_value=0)
        self.amqp_consumer.ack_message = mock.Mock()
        self.assertEqual(None,
                         self.amqp_consumer.on_message(10, basic_deliver,
                                                       properties, body))

    def test_ack_message(self):
        self.amqp_consumer._channel = mock.Mock()
        self.amqp_consumer._channel.basic_ack = mock.Mock()
        self.assertEqual(None, self.amqp_consumer.ack_message(10))

    def test_on_cancelok(self):
        self.amqp_consumer._channel = mock.Mock()
        self.amqp_consumer._channel.close = mock.Mock()
        self.assertEqual(None, self.amqp_consumer.on_cancelok(10))

    def test_run(self):
        self.amqp_consumer._connection = mock.Mock(autospec=AmqpConsumer)
        self.amqp_consumer.connect = mock.Mock()
        self.amqp_consumer._connection.ioloop.start = mock.Mock()
        self.assertEqual(None, self.amqp_consumer.run())

    def test_stop(self):
        self.amqp_consumer._connection = mock.Mock(autospec=AmqpConsumer)
        self.amqp_consumer.connect = mock.Mock()
        self.amqp_consumer._connection.ioloop.start = mock.Mock()
        self.amqp_consumer._channel = mock.Mock()
        self.amqp_consumer._channel.basic_cancel = mock.Mock()
        self.assertEqual(None, self.amqp_consumer.stop())

    def test_close_connection(self):
        self.amqp_consumer._connection = mock.Mock(autospec=AmqpConsumer)
        self.amqp_consumer._connection.close = mock.Mock()
        self.assertEqual(None, self.amqp_consumer.close_connection())
