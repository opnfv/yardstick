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
import os

from oslo_config import cfg
import oslo_messaging
import six

from yardstick.common import messaging


LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class MessagingProducer(object):
    """Abstract class to implement a MQ producer

    This abstract class allows a class implementing this interface to publish
    messages in a message queue.
    """

    def __init__(self, topic, pid=os.getpid(), fanout=True):
        """Init function.

        :param topic: (string) MQ exchange topic
        :param pid: (int) PID of the process implementing this MQ Notifier
        :param fanout: (bool) MQ clients may request that a copy of the message
                       be delivered to all servers listening on a topic by
                       setting fanout to ``True``, rather than just one of them
        :returns: `MessagingNotifier` class object
        """
        self._topic = topic
        self._pid = pid
        self._fanout = fanout
        self._transport = oslo_messaging.get_rpc_transport(
            cfg.CONF, url=messaging.TRANSPORT_URL)
        self._target = oslo_messaging.Target(topic=topic, fanout=fanout,
                                             server=messaging.SERVER)
        self._notifier = oslo_messaging.RPCClient(self._transport,
                                                  self._target)

    def send_message(self, method, payload):
        """Send a cast message, that will invoke a method without blocking.

        The cast() method is used to invoke an RPC method that does not return
        a value.  cast() RPC requests may be broadcast to all Servers listening
        on a given topic by setting the fanout Target property to ``True``.

        :param methos: (string) method name, that must be implemented in the
                       consumer endpoints
        :param payload: (subclass `Payload`) payload content
        """
        self._notifier.cast({'pid': self._pid},
                            method,
                            **payload.obj_to_dict())
