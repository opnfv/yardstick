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
     'name': 'TestServer_2',
     'thread_model': 'Fireball'
     }
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

DMF_CFG = {
    "dmf": {
        "library": "test",
        "name": "Basic UDP"
    },
    "clientPort": {
        "clientPort": 2002,
        "isClientPortRange": "false"
    },
    "dataProtocol": "udp",
    "serverPort": 2003
}

SESSION_PROFILE = {
    'keywords': '',
    'duration': 60,
    'iterations': 1,
    'description': 'UE default bearer creation test case',
    'name': 'default_bearer_capacity',
    'reportOptions': {'Format': '1'},
    "reservePorts": "true",
    "reservations": [
        {"tsId": 4,
         "tsIndex": 0,
         "tsName": TEST_SERVERS[0]['name'],
         "phySubnets": [
             {"base": "10.42.32.100", "mask": "/24", "name": "eth5",
              "numIps": 20},
             {"base": "10.42.33.100", "mask": "/24", "name": "eth6",
              "numIps": 20}
         ]},
        {"tsId": 2,
         "tsIndex": 1,
         "tsName": "TestServer_2",
         "phySubnets": [
             {"base": "10.42.32.1", "mask": "/24", "name": "eth5",
              "numIps": 100},
             {"base": "10.42.33.1", "mask": "/24", "name": "eth6",
              "numIps": 100}
         ]}
    ],
    'tsGroups': [
        {
            'testCases': [{
                'type': 'SGW_Node',
                'name': '',
                'linked': False,
                'AssociatedPhys': '',
                'parameters': {
                    'SgiPtpTunnelEn': 'false',
                    'Gtp2Imsi': '505024101215074',
                    'Sessions': '100000',
                    'S5Protocol': 'GTPv2',
                    'TrafficMtu': '1500',
                    'Gtp2Version': '13.6.0',
                    'BearerV4AddrPool': '1.0.0.1',
                    'Gtp2Imei': '50502410121507',
                    'PgwNodeEn': 'true',
                    'DedicatedsPerDefaultBearer': '0',
                    'DefaultBearers': '1',
                    'SgwUserAddr': {
                        'numLinksOrNodes': 1,
                        'phy': 'eth1',
                        'forcedEthInterface': '',
                        'ip': 'SGW_USER_IP',
                        'class': 'TestNode',
                        'ethStatsEnabled': False,
                        'mtu': 1500
                    },
                    'SgwControlAddr': {
                        'numLinksOrNodes': 1,
                        'phy': 'eth1',
                        'forcedEthInterface': '',
                        'ip': 'SGW_CONTROL_IP',
                        'class': 'TestNode',
                        'ethStatsEnabled': False,
                        'mtu': 1500,
                        'nextHop': 'SGW_CONTROL_NEXT_HOP'
                    },
                    'BearerAddrPool': '2001::1',
                    'TestType': 'SGW-NODE'
                }
            }],
            'tsId': TEST_SERVERS[0]['name']},
        {
            'testCases': [{
                'type': 'SGW_Nodal',
                'name': '',
                'parameters': {
                    'DataTraffic': 'Continuous',
                    'TrafficStartType': 'When All Sessions Established',
                    'NetworkHost': 'Local',
                    'Gtp2Imsi': '505024101215074',
                    'Dmf': {
                        'mainflows': [
                            {
                                'name': 'Basic UDP',
                                'library': 'test'
                            }
                        ],
                        'class': 'Dmf',
                        'instanceGroups': [
                            {
                                'startPaused': False,
                                'rate': 0,
                                'mainflowIdx': 0,
                                'mixType': ''
                            }
                        ]
                    },
                    'S5Protocol': 'GTPv2',
                    'DataUserCfgFileEn': 'false',
                    'PgwUserSutEn': 'false',
                    'MmeControlAddr': {
                        'numLinksOrNodes': 1,
                        'phy': 'eth1',
                        'forcedEthInterface': '',
                        'ip': 'MME_CONTROL_IP',
                        'class': 'TestNode',
                        'ethStatsEnabled': False,
                        'mtu': 1500
                    },
                    'SgwUserSut': {
                        'class': 'Sut',
                        'name': 'SGW_USER_NAME'
                    },
                    'TestActivity': 'Capacity Test',
                    'NetworkHostAddrLocal': {
                        'numLinksOrNodes': 1,
                        'phy': 'eth2',
                        'forcedEthInterface': '',
                        'ip': 'NET_HOST_IP',
                        'class': 'TestNode',
                        'ethStatsEnabled': False,
                        'mtu': 1500
                    },
                    'DedicatedsPerDefaultBearer': '0',
                    'DisconnectRate': '1000.0',
                    'Sessions': '100000',
                    'SgwSut': {
                        'class': 'Sut',
                        'name': 'SGW_CONTROL_NAME'
                    },
                    'TrafficMtu': '1500',
                    'Gtp2Version': '13.6.0',
                    'Gtp2Imei': '50502410121507',
                    'PgwNodeEn': 'false',
                    'StartRate': '1000.0',
                    'PgwV4Sut': {
                        'class': 'Sut',
                        'name': 'PGW_SUT_NAME'
                    },
                    'DefaultBearers': '1',
                    'EnbUserAddr': {
                        'numLinksOrNodes': 1,
                        'phy': 'eth1',
                        'forcedEthInterface': '',
                        'ip': 'ENB_USER_IP',
                        'class': 'TestNode',
                        'ethStatsEnabled': False,
                        'mtu': 1500
                    },
                    'TestType': 'SGW-NODAL'
                }
            }],
            'tsId': TEST_SERVERS[1]['name']
        }
    ]
}


class TestLandslideResourceHelper(unittest.TestCase):
    TEST_TERMINATED = 1
    SUCCESS_RECORD_ID = 11

    TEST_RESULTS_DATA = {
        "interval": 0,
        "elapsedTime": 138,
        "actualTime": 1521548057296,
        "iteration": 1,
        "tabs": {
            "Test Summary": {
                "Start Time": "Tue Mar 20 07:11:55 CDT 2018",
                "Attempted Dedicated Bearer Session Connects": "0",
                "Attempted Dedicated Bearer Session Disconnects": "0",
                "Actual Dedicated Bearer Session Connects": "0",
                "Actual Dedicated Bearer Session Disconnects": "0",
                "Dedicated Bearer Sessions Pending": "0",
                "Dedicated Bearer Sessions Established": "0"
            }}}

    def setUp(self):
        self.mock_lsapi = mock.patch.object(tg_landslide, 'LsApi')
        self.mock_lsapi.start()

        mock_env_helper = mock.Mock()
        self.res_helper = tg_landslide.LandslideResourceHelper(mock_env_helper)
        self.res_helper._url = EXAMPLE_URL

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.mock_lsapi.stop()
        self.res_helper._url = None

    def test___init__(self, *args):
        self.assertIsInstance(self.res_helper,
                              tg_landslide.LandslideResourceHelper)
        self.assertEqual({}, self.res_helper._result)

    def test_terminate(self):
        self.assertRaises(NotImplementedError, self.res_helper.terminate)

    def test_collect_kpi_test_running(self):
        self.assertRaises(NotImplementedError, self.res_helper.collect_kpi)


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
        self.ls_tcl_client._ts_context.vnfd_helper = \
            VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.ls_tcl_client._ts_context.license_data = {'lic_id': return_value}
        self.mock_tcl_handler.execute.return_value = return_value
        self.ls_tcl_client._set_thread_model = mock.Mock()
        res = self.ls_tcl_client.create_test_server(TEST_SERVERS[1])
        self.assertEqual(3, self.mock_tcl_handler.execute.call_count)
        self.ls_tcl_client._set_thread_model.assert_called_once_with(
            TEST_SERVERS[1]['name'],
            TEST_SERVERS[1]['thread_model'])
        self.assertEqual(int(return_value), res)

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
        self.assertEqual(ts_id,
                         self.ls_tcl_client._add_test_server('name', 'ip'))
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

    @mock.patch.object(tg_landslide.LandslideTclClient,
                       'resolve_test_server_name', return_value='2')
    def test_create_test_session(self, *args):
        self.ls_tcl_client._save_test_session = mock.Mock()
        self.ls_tcl_client._configure_ts_group = mock.Mock()
        self.ls_tcl_client.create_test_session(SESSION_PROFILE)
        self.assertEqual(20, self.mock_tcl_handler.execute.call_count)

    def test_create_dmf(self):
        self.mock_tcl_handler.execute.return_value = '2'
        self.ls_tcl_client._save_dmf = mock.Mock()
        self.ls_tcl_client.create_dmf(DMF_CFG)
        self.assertEqual(6, self.mock_tcl_handler.execute.call_count)

    def test_configure_dmf(self):
        self.mock_tcl_handler.execute.return_value = '2'
        self.ls_tcl_client._save_dmf = mock.Mock()
        self.ls_tcl_client.configure_dmf(DMF_CFG)
        self.assertEqual(6, self.mock_tcl_handler.execute.call_count)

    def test_delete_dmf(self):
        self.assertRaises(NotImplementedError,
                          self.ls_tcl_client.delete_dmf,
                          DMF_CFG)

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

    def test__configure_report_options(self):
        _options = {'format': 'CSV', 'PerInterval': False}
        self.ls_tcl_client._configure_report_options(_options)
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)

    def test___configure_ts_group(self, *args):
        self.ls_tcl_client._configure_tc_type = mock.Mock()
        self.ls_tcl_client._configure_preresolved_arp = mock.Mock()
        self.ls_tcl_client.resolve_test_server_name = mock.Mock(
            return_value='2')
        self.ls_tcl_client._configure_ts_group(
            SESSION_PROFILE['tsGroups'][0], 0)
        self.assertEqual(1, self.mock_tcl_handler.execute.call_count)

    def test___configure_ts_group_resolve_ts_fail(self, *args):
        self.ls_tcl_client._configure_tc_type = mock.Mock()
        self.ls_tcl_client._configure_preresolved_arp = mock.Mock()
        self.ls_tcl_client.resolve_test_server_name = mock.Mock(
            return_value='TS Not Found')
        self.assertRaises(RuntimeError, self.ls_tcl_client._configure_ts_group,
                          SESSION_PROFILE['tsGroups'][0], 0)
        self.assertEqual(0, self.mock_tcl_handler.execute.call_count)

    def test__configure_tc_type(self):
        _tc = SESSION_PROFILE['tsGroups'][0]['testCases'][0]
        self.mock_tcl_handler.execute.return_value = TCL_SUCCESS_RESPONSE
        self.ls_tcl_client._configure_parameters = mock.Mock()
        self.ls_tcl_client._configure_tc_type(_tc, 0)
        self.assertEqual(7, self.mock_tcl_handler.execute.call_count)

    def test__configure_tc_type_wrong_type(self):
        _tc = SESSION_PROFILE['tsGroups'][0]['testCases'][0]
        _tc['type'] = 'not_supported'
        self.ls_tcl_client._configure_parameters = mock.Mock()
        self.assertRaises(RuntimeError,
                          self.ls_tcl_client._configure_tc_type,
                          _tc, 0)

    def test__configure_tc_type_not_found_basic_lib(self):
        _tc = SESSION_PROFILE['tsGroups'][0]['testCases'][0]
        self.ls_tcl_client._configure_parameters = mock.Mock()
        self.mock_tcl_handler.execute.return_value = 'Invalid'
        self.assertRaises(RuntimeError,
                          self.ls_tcl_client._configure_tc_type,
                          _tc, 0)
        self.assertEqual(0, self.mock_tcl_handler.execute.call_count)

    def test__configure_parameters(self):
        _params = SESSION_PROFILE['tsGroups'][0]['testCases'][0]['parameters']
        self.ls_tcl_client._configure_parameters(_params)
        self.assertEqual(16, self.mock_tcl_handler.execute.call_count)

    def test__configure_array_param(self):
        _array = {"class": "Array",
                  "array": ["0"]}
        self.ls_tcl_client._configure_array_param('name', _array)
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)

    def test__configure_test_node_param(self):
        _params = SESSION_PROFILE['tsGroups'][0]['testCases'][0]['parameters']
        self.ls_tcl_client._configure_test_node_param('SgwUserAddr',
                                                      _params['SgwUserAddr'])
        self.assertEqual(1, self.mock_tcl_handler.execute.call_count)

    def test__configure_sut_param(self):
        _params = {'name': 'name'}
        self.ls_tcl_client._configure_sut_param('name', _params)
        self.assertEqual(1, self.mock_tcl_handler.execute.call_count)

    def test__configure_dmf_param(self):
        _params = {"mainflows": [{"library": '111',
                                  "name": "Basic UDP"}],
                   "instanceGroups": [{
                       "mainflowIdx": 0,
                       "mixType": "",
                       "rate": 0.0,
                       "rows": [{
                           "clientPort": 0,
                           "context": 0,
                           "node": 0,
                           "overridePort": False,
                           "ratingGroup": 0,
                           "role": 0,
                           "serviceId": 0,
                           "transport": "Any"}]
                   }]}
        self.ls_tcl_client._get_library_id = mock.Mock(return_value='111')
        res = self.ls_tcl_client._configure_dmf_param('name', _params)
        self.assertEqual(5, self.mock_tcl_handler.execute.call_count)
        self.assertIsNone(res)

    def test__configure_dmf_param_no_instance_groups(self):
        _params = {"mainflows": [{"library": '111',
                                  "name": "Basic UDP"}]}
        self.ls_tcl_client._get_library_id = mock.Mock(return_value='111')
        res = self.ls_tcl_client._configure_dmf_param('name', _params)
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)
        self.assertIsNone(res)

    def test__configure_reservation(self):
        _reservation = SESSION_PROFILE['reservations'][0]
        self.ls_tcl_client.resolve_test_server_name = mock.Mock(
            return_value='2')
        res = self.ls_tcl_client._configure_reservation(_reservation)
        self.assertIsNone(res)
        self.assertEqual(6, self.mock_tcl_handler.execute.call_count)

    def test__configure_preresolved_arp(self):
        _arp = [{'StartingAddress': '10.81.1.10',
                 'NumNodes': 1}]
        res = self.ls_tcl_client._configure_preresolved_arp(_arp)
        self.assertEqual(1, self.mock_tcl_handler.execute.call_count)
        self.assertIsNone(res)

    def test__configure_preresolved_arp_none(self):
        res = self.ls_tcl_client._configure_preresolved_arp(None)
        self.assertIsNone(res)

    def test_delete_test_session(self):
        self.assertRaises(NotImplementedError,
                          self.ls_tcl_client.delete_test_session, {})

    def test__save_test_session(self):
        self.mock_tcl_handler.execute.side_effect = [TCL_SUCCESS_RESPONSE,
                                                     TCL_SUCCESS_RESPONSE]
        res = self.ls_tcl_client._save_test_session()
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)
        self.assertIsNone(res)

    def test__save_test_session_invalid(self):
        self.mock_tcl_handler.execute.side_effect = ['Invalid', 'Errors']
        self.assertRaises(exceptions.LandslideTclException,
                          self.ls_tcl_client._save_test_session)
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)

    def test__get_library_id_system_lib(self):
        self.mock_tcl_handler.execute.side_effect = ['111']
        res = self.ls_tcl_client._get_library_id('name')
        self.assertEqual(1, self.mock_tcl_handler.execute.call_count)
        self.assertEqual('111', res)

    def test__get_library_id_user_lib(self):
        self.mock_tcl_handler.execute.side_effect = ['Not found', '222']
        res = self.ls_tcl_client._get_library_id('name')
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)
        self.assertEqual('222', res)

    def test__get_library_id_exception(self):
        self.mock_tcl_handler.execute.side_effect = ['Not found', 'Not found']
        self.assertRaises(exceptions.LandslideTclException,
                          self.ls_tcl_client._get_library_id,
                          'name')
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)


class TestLsTclHandler(unittest.TestCase):

    def setUp(self):
        self.mock_lsapi = mock.patch.object(tg_landslide, 'LsApi')
        self.mock_lsapi.start()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.mock_lsapi.stop()

    def test___init__(self, *args):
        self.ls_tcl_handler = tg_landslide.LsTclHandler()
        self.assertEqual({}, self.ls_tcl_handler.tcl_cmds)
        self.ls_tcl_handler._ls.tcl.assert_called_once()

    def test_execute(self, *args):
        self.ls_tcl_handler = tg_landslide.LsTclHandler()
        self.ls_tcl_handler.execute('command')
        self.assertIn('command', self.ls_tcl_handler.tcl_cmds)
