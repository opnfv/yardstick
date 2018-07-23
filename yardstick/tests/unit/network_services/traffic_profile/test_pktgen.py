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

from yardstick.common import utils
from yardstick.network_services.traffic_profile import pktgen
from yardstick.tests.unit import base as ut_base


class TestIXIARFC2544Profile(ut_base.BaseUnitTestCase):

    def setUp(self):
        self._tp_config = {'traffic_profile': {}}
        self._host = 'localhost'
        self._port = '12345'
        self.tp = pktgen.PktgenTrafficProfile(self._tp_config)
        self.tp.init(self._host, self._port)
        self._mock_send_socket_command = mock.patch.object(
            utils, 'send_socket_command', return_value=0)
        self.mock_send_socket_command = self._mock_send_socket_command.start()
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_send_socket_command.stop()

    def test_start(self):
        self.tp.start()
        self.mock_send_socket_command.assert_called_once_with(
            self._host, self._port, 'pktgen.start("0")')

    def test_stop(self):
        self.tp.stop()
        self.mock_send_socket_command.assert_called_once_with(
            self._host, self._port, 'pktgen.stop("0")')

    def test_rate(self):
        rate = 75
        self.tp.rate(rate)
        command = 'pktgen.set("0", "rate", 75)'
        self.mock_send_socket_command.assert_called_once_with(
            self._host, self._port, command)

    def test_clear_all_stats(self):
        self.tp.clear_all_stats()
        self.mock_send_socket_command.assert_called_once_with(
            self._host, self._port, 'clr')

    def test_help(self):
        self.tp.help()
        self.mock_send_socket_command.assert_called_once_with(
            self._host, self._port, 'help')
