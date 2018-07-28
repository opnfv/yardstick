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
#

import mock
import unittest

from yardstick.common import exceptions
from yardstick.network_services.vnf_generic.vnf import tg_landslide

NAME = "tg__0"


EXAMPLE_URL = 'http://example.com/'
TCL_SUCCESS_RESPONSE = 'ls_ok'

TEST_SERVERS = [
        {'ip': '192.168.122.101',
         'phySubnets': [
             {'mask': '/24',
              'base': '10.42.32.100',
              'numIps': 20,
              'name': 'eth1'}
         ],
         'role': 'SGW_Node',
         'name': 'TestServer_1'},
        {'ip': '192.168.122.102',
         'phySubnets': [
             {'mask': '/24',
              'base': '10.42.32.1',
              'numIps': 100,
              'name': 'eth1'
              },
             {'mask': '/24',
              'base': '10.42.33.1',
              'numIps': 100,
              'name': 'eth2'}
         ],
         'preResolvedArpAddress': [
             {'NumNodes': 1,
              'StartingAddress': '10.42.33.5'}
         ],
         'role': 'SGW_Nodal',
         'name': 'TestServer_2'}
    ]

TS1_SUTS = [
    {'name': 'SGW - C TestNode',
     'role': 'SgwControlAddr',
     'managementIp': '12.0.1.1',
     'ip': '10.42.32.100',
     'phy': 'eth5',
     'nextHop': '10.42.32.5'
     },
    {'name': 'SGW - U TestNode',
     'role': 'SgwUserAddr',
     'managementIp': '12.0.1.2',
     'ip': '10.42.32.101',
     'phy': 'eth5',
     'nextHop': '10.42.32.5'
     }
    ]

TS2_SUTS = [
    {'name': 'eNodeB TestNode',
     'role': 'EnbUserAddr',
     'managementIp': '12.0.2.1',
     'ip': '10.42.32.2',
     'phy': 'eth5',
     'nextHop': '10.42.32.5'
     },
    {'name': 'MME TestNode',
     'role': 'MmeControlAddr',
     'managementIp': '12.0.3.1',
     'ip': '10.42.32.1',
     'phy': 'eth5',
     'nextHop': '10.42.32.5'
     },
    {'name': 'NetHost TestNode',
     'role': 'NetworkHostAddrLocal',
     'managementIp': '12.0.4.1',
     'ip': '10.42.33.1',
     'phy': 'eth5',
     'nextHop': '10.42.32.5'
     },
    {'name': 'PGW TestNode',
     'role': 'PgwV4Sut',
     'managementIp': '12.0.5.1',
     'ip': '10.42.32.105',
     'phy': 'eth5',
     'nextHop': '10.42.32.5'
     },
    {'name': 'SGW - C SUT',
     'role': 'SgwSut',
     'managementIp': '12.0.6.1',
     'ip': '10.42.32.100'
     },
    {'name': 'SGW - U SUT',
     'role': 'SgwUserSut',
     'managementIp': '12.0.6.2',
     'ip': '10.42.32.101'}
    ]

VNFD = {
    'vnfd:vnfd-catalog': {
        'vnfd': [{
            'short-name': 'landslide',
            'vdu': [{
                'description': 'AB client interface details',
                'name': 'abclient-baremetal',
                'id': 'abclient-baremetal',
                'external-interface': []}],
            'description': 'Spirent Landslide traffic generator',
            'config': [{'test_server': TEST_SERVERS[0], 'suts': TS1_SUTS},
                       {'test_server': TEST_SERVERS[1], 'suts': TS2_SUTS}],
            'mgmt-interface': {
                'vdu-id': 'landslide-tas',
                'user': 'user',
                'password': 'user',
                'super-user': 'super-user',
                'super-user-password': 'super-user-password',
                'cfguser_password': 'cfguser_password',
                'license': 48,
                'proto': 'http',
                'ip': '1.1.1.1'},
            'benchmark': {
                'kpi': [
                    'tx_throughput_mbps',
                    'rx_throughput_mbps',
                    'in_packets',
                    'out_packets',
                    'activation_rate_sessps',
                    'deactivation_rate_sessps']},
            'id': 'LandslideTrafficGen',
            'name': 'LandslideTrafficGen'}]}}

TAS_INFO = VNFD['vnfd:vnfd-catalog']['vnfd'][0]['mgmt-interface']


class TestLandslideTclClient(unittest.TestCase):
    def setUp(self):
        self.mock_tcl_handler = mock.Mock(spec=tg_landslide.LsTclHandler)
        self.ls_res_helper = mock.Mock(
            spec=tg_landslide.LandslideResourceHelper)
        self.ls_tcl_client = tg_landslide.LandslideTclClient(
            self.mock_tcl_handler,
            self.ls_res_helper)

    def test___init__(self, *args):
        self.ls_tcl_client = tg_landslide.LandslideTclClient(
            self.mock_tcl_handler,
            self.ls_res_helper)
        self.assertIsNone(self.ls_tcl_client.tcl_server_ip)
        self.assertIsNone(self.ls_tcl_client._user)
        self.assertIsNone(self.ls_tcl_client._library_id)
        self.assertIsNone(self.ls_tcl_client._basic_library_id)
        self.assertEqual(set(), self.ls_tcl_client.ts_ids)
        self.assertIsInstance(self.ls_tcl_client._tc_types, set)
        self.assertIsNotNone(self.ls_tcl_client._tc_types)

    def test_connect_login_success(self, *args):
        lib_id = '123'
        exec_responses = ['java0x2', lib_id, lib_id]
        auth = ('user', 'password')
        self.mock_tcl_handler.execute.side_effect = exec_responses
        self.ls_tcl_client.connect(TAS_INFO['ip'], *auth)
        self.assertEqual(lib_id, self.ls_tcl_client._library_id)
        self.assertEqual(lib_id, self.ls_tcl_client._basic_library_id)
        self.assertEqual(TAS_INFO['ip'], self.ls_tcl_client.tcl_server_ip)
        self.assertEqual(auth[0], self.ls_tcl_client._user)
        self.assertEqual(len(exec_responses),
                         self.mock_tcl_handler.execute.call_count)

    def test_connect_login_failed(self, *args):
        exec_responses = ['Login failed']
        auth = ('user', 'password')
        self.mock_tcl_handler.execute.side_effect = exec_responses
        self.assertRaises(exceptions.LandslideTclException,
                          self.ls_tcl_client.connect,
                          TAS_INFO['ip'],
                          *auth)
        self.assertIsNone(self.ls_tcl_client._library_id)
        self.assertIsNone(self.ls_tcl_client._basic_library_id)
        self.assertIsNone(self.ls_tcl_client.tcl_server_ip)
        self.assertIsNone(self.ls_tcl_client._user)
        self.assertEqual(len(exec_responses),
                         self.mock_tcl_handler.execute.call_count)

    def test_disconnect(self, *args):
        self.ls_tcl_client.disconnect()
        self.assertEqual(1, self.mock_tcl_handler.execute.call_count)
        self.assertIsNone(self.ls_tcl_client.tcl_server_ip)
        self.assertIsNone(self.ls_tcl_client._user)
        self.assertIsNone(self.ls_tcl_client._library_id)
        self.assertIsNone(self.ls_tcl_client._basic_library_id)

    def test_create_test_server(self, *args):
        return_value = '2'
        self.mock_tcl_handler.execute.return_value = return_value
        self.ls_tcl_client._ts_context.license_data = {'lic_id': return_value}
        self.ls_tcl_client.create_test_server(TEST_SERVERS[0])
        self.assertEqual(3, self.mock_tcl_handler.execute.call_count)

    def test_create_test_server_fail_limit_reach(self, *args):
        self.mock_tcl_handler.execute.side_effect = ['TS not found',
                                                     'Add failed']
        self.assertRaises(RuntimeError,
                          self.ls_tcl_client.create_test_server,
                          TEST_SERVERS[0])
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)

    def test__add_test_server(self):
        ts_id = '2'
        self.mock_tcl_handler.execute.side_effect = ['TS not found', ts_id]
        self.assertEqual(self.ls_tcl_client._add_test_server('name', 'ip'),
                         ts_id)
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)

    def test__add_test_server_failed(self):
        self.mock_tcl_handler.execute.side_effect = ['TS not found',
                                                     'Add failed']
        self.assertRaises(RuntimeError, self.ls_tcl_client._add_test_server,
                          'name', 'ip')
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)

    def test__update_license(self):
        curr_lic_id = '111'
        new_lic_id = '222'
        exec_resp = ['java0x4',
                     curr_lic_id,
                     TCL_SUCCESS_RESPONSE,
                     TCL_SUCCESS_RESPONSE]
        self.ls_tcl_client._ts_context.license_data = {'lic_id': new_lic_id}
        self.mock_tcl_handler.execute.side_effect = exec_resp
        self.ls_tcl_client._update_license('name')
        self.assertEqual(len(exec_resp),
                         self.mock_tcl_handler.execute.call_count)

    def test__update_license_same_as_current(self):
        curr_lic_id = '111'
        new_lic_id = '111'
        exec_resp = ['java0x4', curr_lic_id]
        self.ls_tcl_client._ts_context.license_data = {'lic_id': new_lic_id}
        self.mock_tcl_handler.execute.side_effect = exec_resp
        self.ls_tcl_client._update_license('name')
        self.assertEqual(len(exec_resp),
                         self.mock_tcl_handler.execute.call_count)

    def test__set_thread_model_update_needed(self):
        self.ls_tcl_client._ts_context.vnfd_helper = {
            'mgmt-interface': {
                'cfguser_password': 'cfguser_password'
            }
        }
        exec_resp = ['java0x4', 'V0', '', '']
        self.mock_tcl_handler.execute.side_effect = exec_resp
        self.ls_tcl_client._set_thread_model('name', 'Fireball')
        self.assertEqual(len(exec_resp),
                         self.mock_tcl_handler.execute.call_count)

    def test__set_thread_model_no_update_needed(self):
        self.ls_tcl_client._ts_context.vnfd_helper = {
            'mgmt-interface': {
                'cfguser_password': 'cfguser_password'
            }
        }
        exec_resp = ['java0x4', 'V0']
        self.mock_tcl_handler.execute.side_effect = exec_resp
        self.ls_tcl_client._set_thread_model('name', 'Legacy')
        self.assertEqual(len(exec_resp),
                         self.mock_tcl_handler.execute.call_count)

    def test_create_test_session(self):
        exec_resp = ['java0x5', '', '', '']
        self.mock_tcl_handler.execute.side_effect = exec_resp
        _test_session = {'name': 'name',
                         'description': 'description',
                         'duration': 100,
                         'reservePorts': False,
                         'tsGroups': []}
        self.ls_tcl_client._save_test_session = mock.Mock()
        self.ls_tcl_client.create_test_session(_test_session)
        self.assertEqual(len(exec_resp),
                         self.mock_tcl_handler.execute.call_count)

    def test__save_dmf_valid(self):
        exec_resp = [TCL_SUCCESS_RESPONSE, TCL_SUCCESS_RESPONSE]
        self.mock_tcl_handler.execute.side_effect = exec_resp
        self.ls_tcl_client._save_dmf()
        self.assertEqual(len(exec_resp),
                         self.mock_tcl_handler.execute.call_count)

    def test__save_dmf_invalid(self):
        exec_resp = ['Invalid', 'List of errors and warnings']
        self.mock_tcl_handler.execute.side_effect = exec_resp
        self.assertRaises(exceptions.LandslideTclException,
                          self.ls_tcl_client._save_dmf)
        self.assertEqual(len(exec_resp),
                         self.mock_tcl_handler.execute.call_count)


class TestLsTclHandler(unittest.TestCase):

    def setUp(self):
        self.mock_lsapi = mock.patch.object(tg_landslide, 'LsApi')
        self.mock_lsapi.start()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.mock_lsapi.stop()

    def test___init__(self, *args):
        self.ls_tcl_handler = tg_landslide.LsTclHandler()
        self.assertEqual(self.ls_tcl_handler.tcl_cmds, {})
        self.ls_tcl_handler._ls.tcl.assert_called_once()

    def test_execute(self, *args):
        self.ls_tcl_handler = tg_landslide.LsTclHandler()
        self.ls_tcl_handler.execute('command')
        self.assertIn('command', self.ls_tcl_handler.tcl_cmds)
