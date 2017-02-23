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
""" AMQP Consumer scenario definition """

from __future__ import absolute_import
from __future__ import print_function
import logging
import pika
from pika.exceptions import AMQPConnectionError


class AmqpConsumer(object):
    """ This Class handles amqp consumer and collects collectd data """
    EXCHANGE = 'amq.fanout'
    EXCHANGE_TYPE = 'fanout'
    QUEUE = ''
    ROUTING_KEY = 'collectd'

    def __init__(self, amqp_url, queue):
        super(AmqpConsumer, self).__init__()
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url
        self._queue = queue

    def connect(self):
        """ connect to amqp url """
        try:
            return pika.SelectConnection(pika.URLParameters(self._url),
                                         self.on_connection_open,
                                         stop_ioloop_on_close=False)
        except AMQPConnectionError:
            raise RuntimeError

    def on_connection_open(self, unused_connection):
        """ call back from pika & open channel """
        logging.info("list of unused connections %s", unused_connection)
        self._connection.add_on_close_callback(self.on_connection_closed)
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_closed(self, connection, reply_code, reply_text):
        """ close the amqp connections. if force close, try re-connect """
        logging.info("amqp connection (%s)", connection)
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            logging.debug(('Connection closed, reopening in 5 sec: (%s) %s',
                           reply_code, reply_text))
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        """ re-connect amqp consumer"""
        self._connection.ioloop.stop()

        if not self._closing:
            self._connection = self.connect()
            self._connection.ioloop.start()

    def on_channel_open(self, channel):
        """ add close callback & setup exchange """
        self._channel = channel
        self.add_on_channel_close_callback()
        self._channel.exchange_declare(self.on_exchange_declareok,
                                       self.EXCHANGE,
                                       self.EXCHANGE_TYPE,
                                       durable=True, auto_delete=False)

    def add_on_channel_close_callback(self):
        """ register for close callback """
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        """ close amqp channel connection """
        logging.info("amqp channel closed channel(%s), "
                     "reply_code(%s) reply_text(%s)",
                     channel, reply_code, reply_text)
        self._connection.close()

    def on_exchange_declareok(self, unused_frame):
        """ if exchange declare is ok, setup queue """
        logging.info("amqp exchange unused frame (%s)", unused_frame)
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        """ setup queue & declare same with channel """
        logging.info("amqp queue name (%s)", queue_name)
        self._channel.queue_declare(self.on_queue_declareok, queue_name)

    def on_queue_declareok(self, method_frame):
        """ bind queue to channel """
        logging.info("amqp queue method frame (%s)", method_frame)
        self._channel.queue_bind(self._on_bindok, self.QUEUE,
                                 self.EXCHANGE, self.ROUTING_KEY)

    def _on_bindok(self, unused_frame):
        """ call back on bind start consuming data from amqp queue """
        logging.info("amqp unused frame %s", unused_frame)
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message,
                                                         self.QUEUE)

    def add_on_cancel_callback(self):
        """ add cancel func to amqp callback """
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """ on cancel close the channel """
        logging.info("amqp method frame %s", method_frame)
        if self._channel:
            self._channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        """ parse received data from amqp server (collectd) """
        logging.info("amqp unused channel %s, properties %s",
                     unused_channel, properties)
        metrics = body.rsplit()
        self._queue.put({metrics[1]: metrics[3]})
        self.ack_message(basic_deliver.delivery_tag)

    def ack_message(self, delivery_tag):
        """ acknowledge amqp msg """
        self._channel.basic_ack(delivery_tag)

    def on_cancelok(self, unused_frame):
        """ initiate amqp close channel on callback """
        logging.info("amqp unused frame %s", unused_frame)
        self._channel.close()

    def run(self):
        """ Initiate amqp connection. """
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        """ stop amqp consuming data """
        self._closing = True
        if self._channel:
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

        if self._connection:
            self._connection.ioloop.start()

    def close_connection(self):
        """ close amqp connection """
        self._connection.close()
