# Copyright (c) 2018-2019 Intel Corporation
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

from yardstick.common import constants
from yardstick.common import exceptions
from yardstick.network_services.vnf_generic.vnf import base as vnf_base
from yardstick.network_services.vnf_generic.vnf import tg_pktgen
from yardstick.tests.unit import base as ut_base


class PktgenTrafficGenTestCase(ut_base.BaseUnitTestCase):

    SERVICE_PORTS = [{'port': constants.LUA_PORT,
                      'node_port': '34501'}]
    VNFD = {'mgmt-interface': {'ip': '1.2.3.4',
                               'service_ports': SERVICE_PORTS},
            'vdu': [{'external-interface': 'interface'}],
            'benchmark': {'kpi': 'fake_kpi'}
            }

    def test__init(self):
        tg = tg_pktgen.PktgenTrafficGen('name1', self.VNFD)
        self.assertTrue(isinstance(tg, vnf_base.GenericTrafficGen))

    def test_run_traffic(self):
        tg = tg_pktgen.PktgenTrafficGen('name1', self.VNFD)
        mock_tp = mock.Mock()
        with mock.patch.object(tg, '_is_running', return_value=True):
            tg.run_traffic(mock_tp)

        mock_tp.init.assert_called_once_with(tg._node_ip, tg._lua_node_port)

    def test__get_lua_node_port(self):
        tg = tg_pktgen.PktgenTrafficGen('name1', self.VNFD)
        service_ports = [{'port': constants.LUA_PORT,
                          'node_port': '12345'}]
        self.assertEqual(12345, tg._get_lua_node_port(service_ports))

    def test__get_lua_node_port_no_lua_port(self):
        tg = tg_pktgen.PktgenTrafficGen('name1', self.VNFD)
        service_ports = [{'port': '333'}]
        self.assertIsNone(tg._get_lua_node_port(service_ports))

    def test__is_running(self):
        tg = tg_pktgen.PktgenTrafficGen('name1', self.VNFD)
        with mock.patch.object(tg, '_traffic_profile'):
            self.assertTrue(tg._is_running())

    def test__is_running_exception(self):
        tg = tg_pktgen.PktgenTrafficGen('name1', self.VNFD)
        with mock.patch.object(tg, '_traffic_profile') as mock_tp:
            mock_tp.help.side_effect = exceptions.PktgenActionError()
            self.assertFalse(tg._is_running())
