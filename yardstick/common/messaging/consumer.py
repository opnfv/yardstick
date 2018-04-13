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

import abc
import logging

from oslo_config import cfg
import oslo_messaging
import six

from yardstick.common import messaging


LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class NotificationHandler(object):
    """Abstract class to define a endpoint object for a MessagingConsumer"""

    def __init__(self, _id, ctx_pids, queue):
        self._id = _id
        self._ctx_pids = ctx_pids
        self._queue = queue


@six.add_metaclass(abc.ABCMeta)
class MessagingConsumer(object):
    """Abstract class to implement a MQ consumer

    This abstract class allows a class implementing this interface to receive
    the messages published by a `MessagingNotifier`.
    """

    def __init__(self, topic, pids, endpoints, fanout=True):
        """Init function.

        :param topic: (string) MQ exchange topic
        :param pid: (list of int) list of PIDs of the processes implementing
                    the MQ Notifier which will be in the message context
        :param endpoints: (list of class) list of classes implementing the
                          methods (see `MessagingNotifier.send_message) used by
                          the Notifier
        :param fanout: (bool) MQ clients may request that a copy of the message
                       be delivered to all servers listening on a topic by
                       setting fanout to ``True``, rather than just one of them
        :returns: `MessagingConsumer` class object
        """

        self._pids = pids
        self._endpoints = endpoints
        self._transport = oslo_messaging.get_rpc_transport(
            cfg.CONF, url=messaging.TRANSPORT_URL)
        self._target = oslo_messaging.Target(topic=topic, fanout=fanout,
                                             server=messaging.SERVER)
        self._server = oslo_messaging.get_rpc_server(
            self._transport, self._target, self._endpoints,
            executor=messaging.RPC_SERVER_EXECUTOR,
            access_policy=oslo_messaging.DefaultRPCAccessPolicy)

    def start_rpc_server(self):
        """Start the RPC server."""
        if self._server:
            self._server.start()

    def stop_rpc_server(self):
        """Stop the RPC server."""
        if self._server:
            self._server.stop()

    def wait(self):
        """Wait for message processing to complete (blocking)."""
        if self._server:
            self._server.wait()
