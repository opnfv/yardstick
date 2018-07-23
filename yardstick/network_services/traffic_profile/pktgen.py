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

from yardstick.common import exceptions
from yardstick.common import utils
from yardstick.network_services.traffic_profile import base as tp_base


class PktgenTrafficProfile(tp_base.TrafficProfile):
    """This class handles Pktgen Trex Traffic profile execution"""

    def __init__(self, tp_config):  # pragma: no cover
        super(PktgenTrafficProfile, self).__init__(tp_config)
        self._host = None
        self._port = None

    def init(self, host, port):  # pragma: no cover
        """Initialize control parameters

        :param host: (str) ip or host name
        :param port: (int) TCP socket port number for Lua commands
        """
        self._host = host
        self._port = port

    def start(self):
        if utils.send_socket_command(self._host, self._port,
                                     'pktgen.start("0")') != 0:
            raise exceptions.PktgenActionError(action='start')

    def stop(self):
        if utils.send_socket_command(self._host, self._port,
                                     'pktgen.stop("0")') != 0:
            raise exceptions.PktgenActionError(action='stop')

    def rate(self, rate):
        command = 'pktgen.set("0", "rate", ' + str(rate) + ')'
        if utils.send_socket_command(self._host, self._port, command) != 0:
            raise exceptions.PktgenActionError(action='rate')

    def clear_all_stats(self):
        if utils.send_socket_command(self._host, self._port, 'clr') != 0:
            raise exceptions.PktgenActionError(action='clear all stats')

    def help(self):
        if utils.send_socket_command(self._host, self._port, 'help') != 0:
            raise exceptions.PktgenActionError(action='help')

    def execute_traffic(self, *args, **kwargs):  # pragma: no cover
        pass
