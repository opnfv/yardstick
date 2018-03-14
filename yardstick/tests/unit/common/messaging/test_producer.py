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

import mock
from oslo_config import cfg
import oslo_messaging

from yardstick.common import messaging
from yardstick.common.messaging import producer
from yardstick.tests.unit import base as ut_base


class _MessagingProducer(producer.MessagingProducer):
    pass


class MessagingProducerTestCase(ut_base.BaseUnitTestCase):

    def test__init(self):
        with mock.patch.object(oslo_messaging, 'RPCClient') as \
                mock_RPCClient, \
                mock.patch.object(oslo_messaging, 'get_rpc_transport') as \
                mock_get_rpc_transport, \
                mock.patch.object(oslo_messaging, 'Target') as \
                mock_Target:
            mock_get_rpc_transport.return_value = 'test_rpc_transport'
            mock_Target.return_value = 'test_Target'

            _MessagingProducer('test_topic', 'test_pid', fanout=True)
            mock_get_rpc_transport.assert_called_once_with(
                cfg.CONF, url=messaging.TRANSPORT_URL)
            mock_Target.assert_called_once_with(
                topic='test_topic', fanout=True, server=messaging.SERVER)
            mock_RPCClient.assert_called_once_with('test_rpc_transport',
                                                   'test_Target')
