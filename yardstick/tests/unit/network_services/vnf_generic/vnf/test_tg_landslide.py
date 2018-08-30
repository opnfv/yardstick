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

import copy
import mock
import requests
import time
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
    'reportOptions': {'format': 'CSV'},
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
         "tsName": TEST_SERVERS[1]['name'],
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
    PROTO_PORT = 8080
    EXAMPLE_URL = ''.join([TAS_INFO['proto'], '://', TAS_INFO['ip'], ':',
                           str(PROTO_PORT), '/api/'])
    SUCCESS_CREATED_CODE = 201
    SUCCESS_OK_CODE = 200
    INVALID_REST_CODE = '400'
    NOT_MODIFIED_CODE = 500810
    ERROR_CODE = 500800
    SUCCESS_RECORD_ID = 11
    EXPIRE_DATE = '2020/01/01 12:00 FLE Standard Time'
    TEST_USER = 'test'
    TEST_TERMINATED = 1
    AUTH_DATA = {'user': TAS_INFO['user'], 'password': TAS_INFO['password']}
    TEST_SESSION_NAME = 'default_bearer_capacity'

    USERS_DATA = {
        "users": [{
            "url": ''.join([EXAMPLE_URL, 'users/', str(SUCCESS_RECORD_ID)]),
            "id": SUCCESS_RECORD_ID,
            "level": 1,
            "username": TEST_USER
        }]
    }

    CREATE_USER_DATA = {'username': TAS_INFO['user'],
                        'expiresOn': EXPIRE_DATE,
                        'level': 1,
                        'contactInformation': '',
                        'fullName': 'Test User',
                        'password': TAS_INFO['password'],
                        'isActive': 'true'}

    SUTS_DATA = {
        "suts": [
            {
                "url": ''.join([EXAMPLE_URL, 'suts/', str(SUCCESS_RECORD_ID)]),
                "id": SUCCESS_RECORD_ID,
                "name": "10.41.32.1"
            }]}

    TEST_SERVERS_DATA = {
        "testServers": [
            {
                "url": ''.join([EXAMPLE_URL, "testServers/1"]),
                "id": 1,
                "name": TEST_SERVERS[0]['name'],
                "state": "READY",
                "version": "16.4.0.10"
            },
            {
                "url": ''.join([EXAMPLE_URL, "testServers/2"]),
                "id": 2,
                "name": TEST_SERVERS[1]['name'],
                "state": "READY",
                "version": "16.4.0.10"
            }

        ]
    }

    RUN_ID = 3

    RUNNING_TESTS_DATA = {
        "runningTests": [{
            "url": ''.join([EXAMPLE_URL, "runningTests/{}".format(RUN_ID)]),
            "measurementsUrl": ''.join(
                [EXAMPLE_URL,
                 "runningTests/{}/measurements".format(RUN_ID)]),
            "criteriaUrl": ''.join(
                [EXAMPLE_URL,
                 "runningTests/{}/criteria".format(RUN_ID)]),
            "noteToUser": "",
            "id": RUN_ID,
            "library": SUCCESS_RECORD_ID,
            "name": "default_bearer_capacity",
            "user": TEST_USER,
            "criteriaStatus": "NA",
            "testStateOrStep": "COMPLETE"
        }]}

    TEST_RESULTS_DATA = {
        "interval": 0,
        "elapsedTime": 138,
        "actualTime": 1521548057296,
        "iteration": 1,
        "tabs": {
            "Test Summary": {
                "Start Time": "Tue Mar 20 07:11:55 CDT 2018",
                "Actual Dedicated Bearer Session Connects": "100",
                "Actual Dedicated Bearer Session Disconnects": "100",
                "Actual Disconnect Rate(Sessions / Second)(P - I)": "164.804",
                "Average Session Disconnect Time(P - I)": "5.024 s",
                "Total Data Sent + Received Packets / Sec(P - I)": "1,452.294"
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
        self.assertIsNone(self.res_helper.run_id)

    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'stop_running_tests')
    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'get_running_tests')
    def test_abort_running_tests_no_running_tests(self, mock_get_tests,
                                                  mock_stop_tests, *args):
        tests_data = [{'id': self.SUCCESS_RECORD_ID,
                       'testStateOrStep': 'COMPLETE'}]
        mock_get_tests.return_value = tests_data
        self.assertIsNone(self.res_helper.abort_running_tests())
        mock_stop_tests.assert_not_called()

    @mock.patch.object(time, 'sleep')
    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'stop_running_tests')
    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'get_running_tests')
    def test_abort_running_tests(self, mock_get_tests, mock_stop_tests, *args):
        test_states_seq = iter(['RUNNING', 'COMPLETE'])

        def configure_mock(*args):
            return [{'id': self.SUCCESS_RECORD_ID,
                     'testStateOrStep': next(test_states_seq)}]

        mock_get_tests.side_effect = configure_mock
        self.assertIsNone(self.res_helper.abort_running_tests())
        mock_stop_tests.assert_called_once_with(
            running_test_id=self.SUCCESS_RECORD_ID,
            force=True)
        self.assertEqual(2, mock_get_tests.call_count)

    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'stop_running_tests')
    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'get_running_tests')
    def test_abort_running_tests_error(self, mock_get_tests, mock_stop_tests,
                                       *args):
        tests_data = {'id': self.SUCCESS_RECORD_ID,
                      'testStateOrStep': 'RUNNING'}
        mock_get_tests.return_value = [tests_data]
        with self.assertRaises(RuntimeError):
            self.res_helper.abort_running_tests(timeout=1, delay=1)
        mock_stop_tests.assert_called_with(
            running_test_id=self.SUCCESS_RECORD_ID,
            force=True)

    def test__build_url(self, *args):
        resource = 'users'
        action = {'action': 'userCreate'}
        expected_url = ''.join([EXAMPLE_URL, 'users?action=userCreate'])
        self.assertEqual(expected_url,
                         self.res_helper._build_url(resource, action))

    def test__build_url_error(self, *args):
        resource = ''
        action = {'action': 'userCreate'}

        with self.assertRaises(ValueError):
            self.res_helper._build_url(resource, action)

    def test_get_response_params(self, *args):
        method = 'get'
        resource = 'users'
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.USERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        resp = self.res_helper.get_response_params(method, resource)
        self.assertTrue(resp)

    @mock.patch.object(tg_landslide.LandslideResourceHelper, '_get_users')
    @mock.patch.object(time, 'time')
    def test__create_user(self, mock_time, mock_get_users, *args):
        mock_time.strftime.return_value = self.EXPIRE_DATE
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session = mock.Mock(spec=requests.Session)
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertEqual(self.SUCCESS_RECORD_ID,
                         self.res_helper._create_user(self.AUTH_DATA))
        mock_get_users.assert_not_called()

    @mock.patch.object(tg_landslide.LandslideResourceHelper, '_modify_user')
    @mock.patch.object(time, 'time')
    def test__create_user_username_exists(self, mock_time, mock_modify_user,
                                          *args):
        mock_time.strftime.return_value = self.EXPIRE_DATE
        mock_modify_user.return_value = {'id': self.SUCCESS_RECORD_ID,
                                         'result': 'No changes requested'}
        post_resp_data = {
            'status_code': self.ERROR_CODE,
            'json.return_value': {'id': self.SUCCESS_OK_CODE,
                                  'apiCode': self.NOT_MODIFIED_CODE}}
        mock_session = mock.Mock(spec=requests.Session)
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper._create_user(self.AUTH_DATA)
        mock_modify_user.assert_called_once_with(TAS_INFO['user'],
                                                 {'isActive': 'true'})
        self.assertEqual(self.SUCCESS_RECORD_ID, res)

    @mock.patch.object(time, 'time')
    def test__create_user_error(self, mock_time, *args):
        mock_time.strftime.return_value = self.EXPIRE_DATE
        mock_session = mock.Mock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                          'json.return_value': {'apiCode': self.ERROR_CODE}}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        with self.assertRaises(exceptions.RestApiError):
            self.res_helper._create_user(self.AUTH_DATA)

    def test__modify_user(self, *args):
        post_data = {'username': 'test_user'}
        mock_session = mock.Mock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper._modify_user(username=self.TEST_USER,
                                           fields=post_data)
        self.assertEqual(self.SUCCESS_RECORD_ID, res['id'])

    def test__modify_user_rest_resp_fail(self, *args):
        post_data = {'non-existing-key': ''}
        mock_session = mock.Mock(spec=requests.Session)
        mock_session.post.ok = False
        self.res_helper.session = mock_session
        self.assertRaises(exceptions.RestApiError,
                          self.res_helper._modify_user,
                          username=self.TEST_USER, fields=post_data)
        mock_session.post.assert_called_once()

    def test__delete_user(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper._delete_user(
            username=self.TEST_USER))

    def test__get_users(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.USERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        self.assertEqual(self.USERS_DATA['users'],
                         self.res_helper._get_users())

    def test_exec_rest_request(self, *args):
        resource = 'testServers'
        action = {'action': 'modify'}
        expected_url = ''.join([EXAMPLE_URL, 'testServers?action=modify'])
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session = mock.Mock(spec=requests.Session)
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.res_helper.exec_rest_request('post', resource, action)
        self.res_helper.session.post.assert_called_once_with(expected_url,
                                                             json={})

    def test_exec_rest_request_unsupported_method_error(self, *args):
        resource = 'testServers'
        action = {'action': 'modify'}
        with self.assertRaises(ValueError):
            self.res_helper.exec_rest_request('patch', resource, action)

    def test_exec_rest_request_missed_action_arg(self, *args):
        resource = 'testServers'
        with self.assertRaises(ValueError):
            self.res_helper.exec_rest_request('post', resource)

    def test_exec_rest_request_raise_exc(self):
        resource = 'users'
        action = {'action': 'modify'}
        post_resp_data = {'status_code': self.ERROR_CODE,
                          'json.return_value': {
                              'status_code': self.ERROR_CODE}}
        mock_session = mock.Mock(spec=requests.Session)
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.assertRaises(exceptions.RestApiError,
                          self.res_helper.exec_rest_request,
                          'post', resource, action, raise_exc=True)

    @mock.patch.object(time, 'time')
    def test_connect(self, mock_time, *args):
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        mock_time.strftime.return_value = self.EXPIRE_DATE
        self.res_helper.vnfd_helper = vnfd

        self.res_helper._tcl = mock.Mock()
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session = mock.Mock(spec=requests.Session, headers={})
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertIsInstance(self.res_helper.connect(), requests.Session)
        self.res_helper._tcl.connect.assert_called_once_with(
            TAS_INFO['ip'],
            TAS_INFO['user'],
            TAS_INFO['password'])

    def test_disconnect(self, *args):
        self.res_helper._tcl = mock.Mock()
        self.assertIsNone(self.res_helper.disconnect())
        self.assertIsNone(self.res_helper.session)
        self.res_helper._tcl.disconnect.assert_called_once()

    def test_terminate(self, *args):
        self.assertIsNone(self.res_helper.terminate())
        self.assertEqual(self.TEST_TERMINATED,
                         self.res_helper._terminated.value)

    def test_create_dmf(self, *args):
        self.res_helper._tcl = mock.Mock()
        self.assertIsNone(self.res_helper.create_dmf(DMF_CFG))
        self.res_helper._tcl.create_dmf.assert_called_once_with(DMF_CFG)

    def test_create_dmf_as_list(self, *args):
        self.res_helper._tcl = mock.Mock()
        self.assertIsNone(self.res_helper.create_dmf([DMF_CFG]))
        self.res_helper._tcl.create_dmf.assert_called_once_with(DMF_CFG)

    def test_delete_dmf(self, *args):
        self.res_helper._tcl = mock.Mock()
        self.assertIsNone(self.res_helper.delete_dmf(DMF_CFG))
        self.res_helper._tcl.delete_dmf.assert_called_once_with(DMF_CFG)

    def test_delete_dmf_as_list(self, *args):
        self.res_helper._tcl = mock.Mock()
        self.assertIsNone(self.res_helper.delete_dmf([DMF_CFG]))
        self.res_helper._tcl.delete_dmf.assert_called_once_with(DMF_CFG)

    @mock.patch.object(tg_landslide.LandslideResourceHelper, 'configure_sut')
    def test_create_suts(self, mock_configure_sut, *args):
        mock_session = mock.Mock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.create_suts(TS1_SUTS))
        mock_configure_sut.assert_not_called()

    @mock.patch.object(tg_landslide.LandslideResourceHelper, 'configure_sut')
    def test_create_suts_sut_exists(self, mock_configure_sut, *args):
        sut_name = 'test_sut'
        suts = [
            {'name': sut_name,
             'role': 'SgwControlAddr',
             'managementIp': '12.0.1.1',
             'ip': '10.42.32.100'
             }
        ]
        mock_session = mock.Mock(spec=requests.Session)
        post_resp_data = {'status_code': self.NOT_MODIFIED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.create_suts(suts))
        mock_configure_sut.assert_called_once_with(
            sut_name=sut_name,
            json_data={k: v for k, v in suts[0].items()
                       if k not in {'phy', 'nextHop', 'role', 'name'}})

    def test_get_suts(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.SUTS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        self.assertIsInstance(self.res_helper.get_suts(), list)

    def test_get_suts_single_id(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.SUTS_DATA['suts'][0]}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        self.assertIsInstance(self.res_helper.get_suts(suts_id=2), dict)

    def test_configure_sut(self, *args):
        post_data = {'managementIp': '2.2.2.2'}
        mock_session = mock.Mock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.configure_sut('test_name',
                                                        post_data))
        mock_session.post.assert_called_once()

    def test_configure_sut_error(self, *args):
        post_data = {'managementIp': '2.2.2.2'}
        mock_session = mock.Mock(spec=requests.Session)
        post_resp_data = {'status_code': self.NOT_MODIFIED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        with self.assertRaises(exceptions.RestApiError):
            self.res_helper.configure_sut('test_name', post_data)

    def test_delete_suts(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.SUTS_DATA}
        delete_resp_data = {'status_code': self.SUCCESS_OK_CODE}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        mock_session.delete.return_value.configure_mock(**delete_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.delete_suts())
        mock_session.delete.assert_called_once()

    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'get_test_servers')
    def test__check_test_servers_state(self, mock_get_test_servers, *args):
        mock_get_test_servers.return_value = \
            self.TEST_SERVERS_DATA['testServers']
        self.res_helper._check_test_servers_state()
        mock_get_test_servers.assert_called_once()

    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'get_test_servers')
    def test__check_test_servers_state_server_not_ready(
            self, mock_get_test_servers, *args):
        test_servers_not_ready = [
            {
                "url": ''.join([EXAMPLE_URL, "testServers/1"]),
                "id": 1,
                "name": "TestServer_1",
                "state": "NOT_READY",
                "version": "16.4.0.10"
            }
        ]

        mock_get_test_servers.return_value = test_servers_not_ready
        with self.assertRaises(RuntimeError):
            self.res_helper._check_test_servers_state(timeout=1, delay=0)

    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       '_check_test_servers_state')
    def test_create_test_servers(self, mock_check_ts_state, *args):
        test_servers_ids = [
            ts['id'] for ts in self.TEST_SERVERS_DATA['testServers']]

        self.res_helper.license_data['lic_id'] = TAS_INFO['license']
        self.res_helper._tcl.create_test_server = mock.Mock()
        self.res_helper._tcl.create_test_server.side_effect = test_servers_ids
        self.assertIsNone(self.res_helper.create_test_servers(TEST_SERVERS))
        mock_check_ts_state.assert_called_once_with(test_servers_ids)

    @mock.patch.object(tg_landslide.LandslideTclClient,
                       'resolve_test_server_name')
    @mock.patch.object(tg_landslide.LsTclHandler, 'execute')
    def test_create_test_servers_error(self, mock_execute,
                                       mock_resolve_ts_name, *args):
        self.res_helper.license_data['lic_id'] = TAS_INFO['license']
        # Return message for case test server wasn't created
        mock_execute.return_value = 'TS not found'
        # Return message for case test server name wasn't resolved
        mock_resolve_ts_name.return_value = 'TS not found'
        with self.assertRaises(RuntimeError):
            self.res_helper.create_test_servers(TEST_SERVERS)

    def test_get_test_servers(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_SERVERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.get_test_servers()
        self.assertEqual(self.TEST_SERVERS_DATA['testServers'], res)

    def test_get_test_servers_by_id(self, *args):
        mock_session = mock.Mock(spec=requests.Session)

        _ts = self.TEST_SERVERS_DATA['testServers'][0]
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': _ts}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.get_test_servers(test_server_ids=[_ts['id']])
        self.assertEqual([_ts], res)

    def test_configure_test_servers(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_SERVERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.configure_test_servers(
            action={'action': 'recycle'})
        self.assertEqual(
            {x['id'] for x in self.TEST_SERVERS_DATA['testServers']},
            set(res))
        self.assertEqual(len(self.TEST_SERVERS_DATA['testServers']),
                         mock_session.post.call_count)

    def test_delete_test_servers(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_SERVERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.delete_test_servers())
        self.assertEqual(len(self.TEST_SERVERS_DATA['testServers']),
                         mock_session.delete.call_count)

    def test_create_test_session(self, *args):
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        self.res_helper._tcl = mock.Mock()
        test_session = {'name': 'test'}
        self.assertIsNone(self.res_helper.create_test_session(test_session))
        self.res_helper._tcl.create_test_session.assert_called_once_with(
            {'name': 'test', 'library': self.SUCCESS_RECORD_ID})

    @mock.patch.object(tg_landslide.LandslideTclClient,
                       'resolve_test_server_name',
                       return_value='Not Found')
    def test_create_test_session_ts_name_not_found(self, *args):
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        test_session = {
            'duration': 60,
            'description': 'UE default bearer creation test case',
            'name': 'default_bearer_capacity',
            'tsGroups': [{'testCases': [{'type': 'SGW_Node',
                                         'name': ''}],
                          'tsId': 'TestServer_3'}]
        }
        with self.assertRaises(RuntimeError):
            self.res_helper.create_test_session(test_session)

    def test_get_test_session(self, *args):
        test_session = {"name": self.TEST_SESSION_NAME}
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': test_session}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.get_test_session(self.TEST_SESSION_NAME)
        self.assertEqual(test_session, res)

    def test_configure_test_session(self, *args):
        test_session = {'name': self.TEST_SESSION_NAME}
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        self.res_helper.user_lib_uri = 'libraries/{{}}/{}'.format(
            self.res_helper.test_session_uri)
        mock_session = mock.Mock(spec=requests.Session)
        self.res_helper.session = mock_session
        res = self.res_helper.configure_test_session(self.TEST_SESSION_NAME,
                                                     test_session)
        self.assertIsNotNone(res)
        mock_session.post.assert_called_once()

    def test_delete_test_session(self, *args):
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        self.res_helper.user_lib_uri = 'libraries/{{}}/{}'.format(
            self.res_helper.test_session_uri)
        mock_session = mock.Mock(spec=requests.Session)
        self.res_helper.session = mock_session
        res = self.res_helper.delete_test_session(self.TEST_SESSION_NAME)
        self.assertIsNotNone(res)
        mock_session.delete.assert_called_once()

    def test_create_running_tests(self, *args):
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        test_session = {'id': self.SUCCESS_RECORD_ID}
        mock_session = mock.Mock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': test_session}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.res_helper.create_running_tests(self.TEST_SESSION_NAME)
        self.assertEqual(self.SUCCESS_RECORD_ID, self.res_helper.run_id)

    def test_create_running_tests_error(self, *args):
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        mock_session = mock.Mock(spec=requests.Session)
        post_resp_data = {'status_code': self.NOT_MODIFIED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        with self.assertRaises(exceptions.RestApiError):
            self.res_helper.create_running_tests(self.TEST_SESSION_NAME)

    def test_get_running_tests(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.RUNNING_TESTS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.get_running_tests()
        self.assertEqual(self.RUNNING_TESTS_DATA['runningTests'], res)

    def test_delete_running_tests(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        delete_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                            'json.return_value': self.RUNNING_TESTS_DATA}
        mock_session.delete.return_value.configure_mock(**delete_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.delete_running_tests())

    def test__running_tests_action(self, *args):
        action = 'abort'
        mock_session = mock.Mock(spec=requests.Session)
        self.res_helper.session = mock_session
        res = self.res_helper._running_tests_action(self.SUCCESS_RECORD_ID,
                                                    action)
        self.assertIsNone(res)

    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       '_running_tests_action')
    def test_stop_running_tests(self, mock_tests_action, *args):
        res = self.res_helper.stop_running_tests(self.SUCCESS_RECORD_ID)
        self.assertIsNone(res)
        mock_tests_action.assert_called_once()

    def test_check_running_test_state(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {
            'status_code': self.SUCCESS_OK_CODE,
            'json.return_value': self.RUNNING_TESTS_DATA["runningTests"][0]}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.check_running_test_state(self.SUCCESS_RECORD_ID)
        self.assertEqual(
            self.RUNNING_TESTS_DATA["runningTests"][0]['testStateOrStep'],
            res)

    def test_get_running_tests_results(self, *args):
        mock_session = mock.Mock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_RESULTS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.get_running_tests_results(
            self.SUCCESS_RECORD_ID)
        self.assertEqual(self.TEST_RESULTS_DATA, res)

    def test__write_results(self, *args):
        self.maxDiff = None
        res = self.res_helper._write_results(self.TEST_RESULTS_DATA)
        exp_res = {
            "Test Summary::Actual Dedicated Bearer Session Connects": 100.0,
            "Test Summary::Actual Dedicated Bearer Session Disconnects": 100.0,
            "Test Summary::Actual Disconnect Rate(Sessions / Second)(P - I)": 164.804,
            "Test Summary::Average Session Disconnect Time(P - I)": 5.024,
            "Test Summary::Total Data Sent + Received Packets / Sec(P - I)": 1452.294
        }
        self.assertEqual(exp_res, res)

    def test__write_results_no_tabs(self, *args):
        _res_data = copy.deepcopy(self.TEST_RESULTS_DATA)
        del _res_data['tabs']
        # Return None if tabs not found in test results dict
        self.assertIsNone(self.res_helper._write_results(_res_data))

    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'check_running_test_state')
    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'get_running_tests_results')
    def test_collect_kpi_test_running(self, mock_tests_results,
                                      mock_tests_state, *args):
        self.res_helper.run_id = self.SUCCESS_RECORD_ID
        mock_tests_state.return_value = 'RUNNING'
        mock_tests_results.return_value = self.TEST_RESULTS_DATA
        res = self.res_helper.collect_kpi()
        self.assertNotIn('done', res)
        mock_tests_state.assert_called_once_with(self.res_helper.run_id)
        mock_tests_results.assert_called_once_with(self.res_helper.run_id)

    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'check_running_test_state')
    @mock.patch.object(tg_landslide.LandslideResourceHelper,
                       'get_running_tests_results')
    def test_collect_kpi_test_completed(self, mock_tests_results,
                                        mock_tests_state, *args):
        self.res_helper.run_id = self.SUCCESS_RECORD_ID
        mock_tests_state.return_value = 'COMPLETE'
        res = self.res_helper.collect_kpi()
        self.assertIsNotNone(res)
        mock_tests_state.assert_called_once_with(self.res_helper.run_id)
        mock_tests_results.assert_not_called()
        self.assertDictContainsSubset({'done': True}, res)


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
        self.mock_tcl_handler.execute.assert_called_once()
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
        _session_profile = copy.deepcopy(SESSION_PROFILE)
        self.ls_tcl_client._save_test_session = mock.Mock()
        self.ls_tcl_client._configure_ts_group = mock.Mock()
        self.ls_tcl_client.create_test_session(_session_profile)
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
        _options = {'format': 'CSV', 'PerInterval': 'false'}
        self.ls_tcl_client._configure_report_options(_options)
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)

    def test___configure_ts_group(self, *args):
        _ts_group = copy.deepcopy(SESSION_PROFILE['tsGroups'][0])
        self.ls_tcl_client._configure_tc_type = mock.Mock()
        self.ls_tcl_client._configure_preresolved_arp = mock.Mock()
        self.ls_tcl_client.resolve_test_server_name = mock.Mock(
            return_value='2')
        self.ls_tcl_client._configure_ts_group(_ts_group, 0)
        self.mock_tcl_handler.execute.assert_called_once()

    def test___configure_ts_group_resolve_ts_fail(self, *args):
        _ts_group = copy.deepcopy(SESSION_PROFILE['tsGroups'][0])
        self.ls_tcl_client._configure_tc_type = mock.Mock()
        self.ls_tcl_client._configure_preresolved_arp = mock.Mock()
        self.ls_tcl_client.resolve_test_server_name = mock.Mock(
            return_value='TS Not Found')
        self.assertRaises(RuntimeError, self.ls_tcl_client._configure_ts_group,
                          _ts_group, 0)
        self.mock_tcl_handler.execute.assert_not_called()

    def test__configure_tc_type(self):
        _tc = copy.deepcopy(SESSION_PROFILE['tsGroups'][0]['testCases'][0])
        self.mock_tcl_handler.execute.return_value = TCL_SUCCESS_RESPONSE
        self.ls_tcl_client._configure_parameters = mock.Mock()
        self.ls_tcl_client._configure_tc_type(_tc, 0)
        self.assertEqual(7, self.mock_tcl_handler.execute.call_count)

    def test__configure_tc_type_optional_param_omitted(self):
        _tc = copy.deepcopy(SESSION_PROFILE['tsGroups'][0]['testCases'][0])
        del _tc['linked']
        self.mock_tcl_handler.execute.return_value = TCL_SUCCESS_RESPONSE
        self.ls_tcl_client._configure_parameters = mock.Mock()
        self.ls_tcl_client._configure_tc_type(_tc, 0)
        self.assertEqual(6, self.mock_tcl_handler.execute.call_count)

    def test__configure_tc_type_wrong_type(self):
        _tc = copy.deepcopy(SESSION_PROFILE['tsGroups'][0]['testCases'][0])
        _tc['type'] = 'not_supported'
        self.ls_tcl_client._configure_parameters = mock.Mock()
        self.assertRaises(RuntimeError,
                          self.ls_tcl_client._configure_tc_type,
                          _tc, 0)

    def test__configure_tc_type_not_found_basic_lib(self):
        _tc = copy.deepcopy(SESSION_PROFILE['tsGroups'][0]['testCases'][0])
        self.ls_tcl_client._configure_parameters = mock.Mock()
        self.mock_tcl_handler.execute.return_value = 'Invalid'
        self.assertRaises(RuntimeError,
                          self.ls_tcl_client._configure_tc_type,
                          _tc, 0)

    def test__configure_parameters(self):
        _params = copy.deepcopy(
            SESSION_PROFILE['tsGroups'][0]['testCases'][0]['parameters'])
        self.ls_tcl_client._configure_parameters(_params)
        self.assertEqual(16, self.mock_tcl_handler.execute.call_count)

    def test__configure_array_param(self):
        _array = {"class": "Array",
                  "array": ["0"]}
        self.ls_tcl_client._configure_array_param('name', _array)
        self.assertEqual(2, self.mock_tcl_handler.execute.call_count)

    def test__configure_test_node_param(self):
        _params = copy.deepcopy(
            SESSION_PROFILE['tsGroups'][0]['testCases'][0]['parameters'])
        self.ls_tcl_client._configure_test_node_param('SgwUserAddr',
                                                      _params['SgwUserAddr'])
        self.mock_tcl_handler.execute.assert_called_once()

    def test__configure_sut_param(self):
        _params = {'name': 'name'}
        self.ls_tcl_client._configure_sut_param('name', _params)
        self.mock_tcl_handler.execute.assert_called_once()

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
        _reservation = copy.deepcopy(SESSION_PROFILE['reservations'][0])
        self.ls_tcl_client.resolve_test_server_name = mock.Mock(
            return_value='2')
        res = self.ls_tcl_client._configure_reservation(_reservation)
        self.assertIsNone(res)
        self.assertEqual(6, self.mock_tcl_handler.execute.call_count)

    def test__configure_preresolved_arp(self):
        _arp = [{'StartingAddress': '10.81.1.10',
                 'NumNodes': 1}]
        res = self.ls_tcl_client._configure_preresolved_arp(_arp)
        self.mock_tcl_handler.execute.assert_called_once()
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
        self.mock_tcl_handler.execute.return_value = '111'
        res = self.ls_tcl_client._get_library_id('name')
        self.mock_tcl_handler.execute.assert_called_once()
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
