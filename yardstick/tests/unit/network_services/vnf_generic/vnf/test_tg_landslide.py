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
import requests
import time
import unittest

from yardstick.network_services.vnf_generic.vnf import sample_vnf
from yardstick.network_services.vnf_generic.vnf import tg_landslide

from yardstick.network_services.vnf_generic.vnf.tg_landslide import \
    LandslideResourceHelper, LandslideTclClient, \
    LsTclHandler
from yardstick.common.exceptions import RestApiError, LandslideTclException


EXAMPLE_URL = 'http://example.com/'

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


class TestLandslideResourceHelper(unittest.TestCase):

    DMF_CFG = {
        "dmf": {
            "library": "test",
            "name": "Basic UDP"
            }
    }

    TAS_INFO = VNFD['vnfd:vnfd-catalog']['vnfd'][0]['mgmt-interface']
    PROTO_PORT = 8080

    EXAMPLE_URL = ''.join([TAS_INFO['proto'], '://', TAS_INFO['ip'], ':',
                           str(PROTO_PORT), '/api/'])
    SUCCESS_CREATED_CODE = 201
    SUCCESS_OK_CODE = 200
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
                "name": "TestServer_1",
                "state": "READY",
                "version": "16.4.0.10"
            },
            {
                "url": ''.join([EXAMPLE_URL, "testServers/2"]),
                "id": 2,
                "name": "TestServer_2",
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
                "Attempted Dedicated Bearer Session Connects": "0",
                "Attempted Dedicated Bearer Session Disconnects": "0",
                "Actual Dedicated Bearer Session Connects": "0",
                "Actual Dedicated Bearer Session Disconnects": "0",
                "Dedicated Bearer Sessions Pending": "0",
                "Dedicated Bearer Sessions Established": "0"
            }}}

    @mock.patch.object(sample_vnf, 'SetupEnvHelper')
    def setUp(self, mock_env_helper):
        self.mock_lsapi = mock.patch.object(tg_landslide, 'LsApi')
        self.mock_lsapi.start()
        self.res_helper = LandslideResourceHelper(mock_env_helper)

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.mock_lsapi.stop()

    def test___init__(self, *args):
        self.assertIsInstance(self.res_helper, LandslideResourceHelper)
        self.assertIsNone(self.res_helper.run_id)

    @mock.patch.object(LandslideResourceHelper, 'stop_running_tests')
    @mock.patch.object(LandslideResourceHelper, 'get_running_tests')
    def test_abort_running_tests_no_running_tests(self, mock_get_tests,
                                                  mock_stop_tests, *args):
        tests_data = [{'id': self.SUCCESS_RECORD_ID,
                       'testStateOrStep': 'COMPLETE'}]
        mock_get_tests.return_value = tests_data
        self.assertIsNone(self.res_helper.abort_running_tests())
        mock_stop_tests.assert_not_called()

    @mock.patch.object(time, 'sleep')
    @mock.patch.object(LandslideResourceHelper, 'stop_running_tests')
    @mock.patch.object(LandslideResourceHelper, 'get_running_tests')
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
        self.assertEquals(2, mock_get_tests.call_count)

    @mock.patch.object(LandslideResourceHelper, 'stop_running_tests')
    @mock.patch.object(LandslideResourceHelper, 'get_running_tests')
    def test_abort_running_tests_error(self, mock_get_tests, mock_stop_tests,
                                       *args):

        self.res_helper._url = EXAMPLE_URL
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

        self.res_helper._url = EXAMPLE_URL
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

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.USERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        resp = self.res_helper.get_response_params(method, resource)
        self.assertTrue(resp)

    @mock.patch.object(LandslideResourceHelper, '_get_users')
    @mock.patch.object(time, 'time')
    def test__create_user(self, mock_time, mock_get_users, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_time.strftime.return_value = self.EXPIRE_DATE
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertEqual(self.SUCCESS_RECORD_ID,
                         self.res_helper._create_user(self.AUTH_DATA))
        mock_get_users.assert_not_called()

    @mock.patch.object(LandslideResourceHelper, '_modify_user')
    @mock.patch.object(time, 'time')
    def test__create_user_username_exists(self, mock_time, mock_modify_user,
                                          *args):

        self.res_helper._url = EXAMPLE_URL
        mock_time.strftime.return_value = self.EXPIRE_DATE
        mock_modify_user.return_value = {'id': self.SUCCESS_RECORD_ID,
                                         'result': 'No changes requested'}
        post_resp_data = {
            'status_code': self.ERROR_CODE,
            'json.return_value': {'id': self.SUCCESS_OK_CODE,
                                  'apiCode': self.NOT_MODIFIED_CODE}}
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper._create_user(self.AUTH_DATA)
        mock_modify_user.assert_called_once_with(self.TAS_INFO['user'],
                                                 {'isActive': 'true'})
        self.assertEqual(res, self.SUCCESS_RECORD_ID)

    @mock.patch.object(time, 'time')
    def test__create_user_error(self, mock_time, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_time.strftime.return_value = self.EXPIRE_DATE
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                          'json.return_value': {'apiCode': self.ERROR_CODE}}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        with self.assertRaises(RestApiError):
            self.res_helper._create_user(self.AUTH_DATA)

    def test__modify_user(self, *args):

        self.res_helper._url = EXAMPLE_URL
        post_data = {'username': 'test_user'}
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper._modify_user(username=self.TEST_USER,
                                           fields=post_data)
        self.assertEqual(res['id'], self.SUCCESS_RECORD_ID)

    def test__delete_user(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper._delete_user(
            username=self.TEST_USER))

    def test__get_users(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
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

        self.res_helper._url = EXAMPLE_URL
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNotNone(self.res_helper.exec_rest_request(
            'post', resource, action))
        self.res_helper.session.post.assert_called_once_with(expected_url,
                                                             json={})

    def test_exec_rest_request_unsupported_method_error(self, *args):
        resource = 'testServers'
        action = {'action': 'modify'}

        self.res_helper._url = EXAMPLE_URL
        with self.assertRaises(ValueError):
            self.res_helper.exec_rest_request('patch', resource, action)

    def test_exec_rest_request_missed_action_arg(self, *args):
        resource = 'testServers'

        self.res_helper._url = EXAMPLE_URL
        with self.assertRaises(ValueError):
            self.res_helper.exec_rest_request('post', resource)

    @mock.patch.object(time, 'time')
    def test_connect(self, mock_time, *args):
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        mock_time.strftime.return_value = self.EXPIRE_DATE
        self.res_helper.vnfd_helper = vnfd

        self.res_helper._tcl = mock.Mock()
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session = mock.MagicMock(spec=requests.Session, headers={})
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertIsInstance(self.res_helper.connect(), requests.Session)
        self.res_helper._tcl.connect.assert_called_once_with(
            self.TAS_INFO['ip'],
            (self.TAS_INFO['user'], self.TAS_INFO['password']))

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
        self.assertIsNone(self.res_helper.create_dmf(self.DMF_CFG))
        self.res_helper._tcl.create_dmf.assert_called_once_with(
            self.DMF_CFG)

    def test_delete_dmf(self, *args):

        self.res_helper._tcl = mock.Mock()
        self.assertIsNone(self.res_helper.delete_dmf(self.DMF_CFG))
        self.res_helper._tcl.delete_dmf.assert_called_once_with(
            self.DMF_CFG)

    @mock.patch.object(LandslideResourceHelper, 'configure_sut')
    def test_create_suts(self, mock_configure_sut, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.create_suts(TS1_SUTS))
        mock_configure_sut.assert_not_called()

    @mock.patch.object(LandslideResourceHelper, 'configure_sut')
    def test_create_suts_sut_exists(self, mock_configure_sut, *args):
        sut_name = 'test_sut'
        suts = [
            {'name': sut_name,
             'role': 'SgwControlAddr',
             'managementIp': '12.0.1.1',
             'ip': '10.42.32.100'
             }
        ]

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.NOT_MODIFIED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.create_suts(suts))
        mock_configure_sut.assert_called_once_with(
            sut_name=sut_name,
            json_data={k: v for k, v in suts[0].items()
                       if k not in {'phy', 'nextHop', 'role', 'name'}})

    def test_get_suts(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.SUTS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNotNone(self.res_helper.get_suts())

    def test_configure_sut(self, *args):
        post_data = {'managementIp': '2.2.2.2'}

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.configure_sut('test_name',
                                                        post_data))
        mock_session.post.assert_called_once()

    def test_configure_sut_error(self, *args):
        post_data = {'managementIp': '2.2.2.2'}

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.NOT_MODIFIED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        with self.assertRaises(RestApiError):
            self.res_helper.configure_sut('test_name', post_data)

    def test_delete_suts(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.SUTS_DATA}
        delete_resp_data = {'status_code': self.SUCCESS_OK_CODE}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        mock_session.delete.return_value.configure_mock(**delete_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.delete_suts())
        mock_session.delete.assert_called_once()

    @mock.patch.object(LandslideResourceHelper, 'get_test_servers')
    def test__check_test_servers_state(self, mock_get_test_servers,
                                       *args):

        mock_get_test_servers.return_value = \
            self.TEST_SERVERS_DATA['testServers']
        self.assertIsNone(self.res_helper._check_test_servers_state())
        mock_get_test_servers.assert_called_once()

    @mock.patch.object(LandslideResourceHelper, 'get_test_servers')
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

    @mock.patch.object(LandslideResourceHelper, '_check_test_servers_state')
    def test_create_test_servers(self, mock_check_ts_state, *args):
        test_servers_ids = [
            ts['id'] for ts in self.TEST_SERVERS_DATA['testServers']]

        self.res_helper.license_data['lic_id'] = self.TAS_INFO['license']
        self.res_helper._tcl.create_test_server = mock.Mock()
        self.res_helper._tcl.create_test_server.side_effect = test_servers_ids
        self.assertIsNone(self.res_helper.create_test_servers(TEST_SERVERS))
        mock_check_ts_state.assert_called_once_with(test_servers_ids)

    @mock.patch.object(LandslideTclClient, 'resolve_test_server_name')
    @mock.patch.object(LsTclHandler, 'execute')
    def test_create_test_servers_error(self, mock_execute,
                                       mock_resolve_ts_name, *args):

        self.res_helper.license_data['lic_id'] = self.TAS_INFO['license']
        # Return message for case test server wasn't created
        mock_execute.return_value = 'TS not found'
        # Return message for case test server name wasn't resolved
        mock_resolve_ts_name.return_value = 'TS not found'
        with self.assertRaises(RuntimeError):
            self.res_helper.create_test_servers(TEST_SERVERS)

    def test_get_test_servers(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_SERVERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.get_test_servers()
        self.assertEqual(res, self.TEST_SERVERS_DATA['testServers'])

    def test_configure_test_servers(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_SERVERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.configure_test_servers(
            action={'action': 'recycle'})
        self.assertIsNotNone(res)
        self.assertEquals(mock_session.post.call_count,
                          len(self.TEST_SERVERS_DATA['testServers']))

    def test_delete_test_servers(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_SERVERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.delete_test_servers())
        self.assertEquals(mock_session.delete.call_count,
                          len(self.TEST_SERVERS_DATA['testServers']))

    def test_create_test_session(self, *args):

        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        self.res_helper._tcl = mock.Mock()
        test_session = {'name': 'test'}
        self.assertIsNone(self.res_helper.create_test_session(test_session))
        self.res_helper._tcl.create_test_session.assert_called_once_with(
            {'name': 'test', 'library': self.SUCCESS_RECORD_ID})

    @mock.patch.object(LandslideTclClient, 'resolve_test_server_name',
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

        self.res_helper._url = EXAMPLE_URL
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': test_session}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.get_test_session(self.TEST_SESSION_NAME)
        self.assertEquals(test_session, res)

    def test_configure_test_session(self, *args):
        test_session = {'name': self.TEST_SESSION_NAME}

        self.res_helper._url = EXAMPLE_URL
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        self.res_helper.user_lib_uri = 'libraries/{{}}/{}'.format(
            self.res_helper.test_session_uri)
        mock_session = mock.MagicMock(spec=requests.Session)
        self.res_helper.session = mock_session
        res = self.res_helper.configure_test_session(self.TEST_SESSION_NAME,
                                                     test_session)
        self.assertIsNotNone(res)
        mock_session.post.assert_called_once()

    def test_delete_test_session(self, *args):

        self.res_helper._url = EXAMPLE_URL
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        self.res_helper.user_lib_uri = 'libraries/{{}}/{}'.format(
            self.res_helper.test_session_uri)
        mock_session = mock.MagicMock(spec=requests.Session)
        self.res_helper.session = mock_session
        res = self.res_helper.delete_test_session(self.TEST_SESSION_NAME)
        self.assertIsNotNone(res)
        mock_session.delete.assert_called_once()

    def test_create_running_tests(self, *args):

        self.res_helper._url = EXAMPLE_URL
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        test_session = {'id': self.SUCCESS_RECORD_ID}
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': test_session}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        self.res_helper.create_running_tests(self.TEST_SESSION_NAME)
        self.assertEquals(self.SUCCESS_RECORD_ID, self.res_helper.run_id)

    def test_create_running_tests_error(self, *args):

        self.res_helper._url = EXAMPLE_URL
        self.res_helper._user_id = self.SUCCESS_RECORD_ID
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.NOT_MODIFIED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        self.res_helper.session = mock_session
        with self.assertRaises(RestApiError):
            self.res_helper.create_running_tests(self.TEST_SESSION_NAME)

    def test_get_running_tests(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.RUNNING_TESTS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.get_running_tests()
        self.assertEquals(self.RUNNING_TESTS_DATA['runningTests'], res)

    def test_delete_running_tests(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        delete_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                            'json.return_value': self.RUNNING_TESTS_DATA}
        mock_session.delete.return_value.configure_mock(**delete_resp_data)
        self.res_helper.session = mock_session
        self.assertIsNone(self.res_helper.delete_running_tests())

    def test__running_tests_action(self, *args):
        action = 'abort'

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        self.res_helper.session = mock_session
        res = self.res_helper._running_tests_action(self.SUCCESS_RECORD_ID,
                                                    action)
        self.assertIsNone(res)

    @mock.patch.object(LandslideResourceHelper, '_running_tests_action')
    def test_stop_running_tests(self, mock_tests_action, *args):

        res = self.res_helper.stop_running_tests(self.SUCCESS_RECORD_ID)
        self.assertIsNone(res)
        mock_tests_action.assert_called_once()

    def test_check_running_test_state(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {
            'status_code': self.SUCCESS_OK_CODE,
            'json.return_value': self.RUNNING_TESTS_DATA["runningTests"][0]}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.check_running_test_state(self.SUCCESS_RECORD_ID)
        self.assertEquals(
            self.RUNNING_TESTS_DATA["runningTests"][0]['testStateOrStep'],
            res)

    def test_get_running_tests_results(self, *args):

        self.res_helper._url = EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_RESULTS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        self.res_helper.session = mock_session
        res = self.res_helper.get_running_tests_results(
            self.SUCCESS_RECORD_ID)
        self.assertEquals(self.TEST_RESULTS_DATA, res)

    def test__write_results(self, *args):

        res = self.res_helper._write_results(self.TEST_RESULTS_DATA)
        self.assertIsNotNone(res)

    @mock.patch.object(LandslideResourceHelper, 'check_running_test_state')
    @mock.patch.object(LandslideResourceHelper, 'get_running_tests_results')
    def test_collect_kpi_test_running(self, mock_tests_results,
                                      mock_tests_state, *args):

        self.res_helper.run_id = self.SUCCESS_RECORD_ID
        mock_tests_state.return_value = 'RUNNING'
        mock_tests_results.return_value = self.TEST_RESULTS_DATA
        res = self.res_helper.collect_kpi()
        self.assertNotIn('done', res)
        mock_tests_state.assert_called_once_with(self.res_helper.run_id)
        mock_tests_results.assert_called_once_with(self.res_helper.run_id)

    @mock.patch.object(LandslideResourceHelper, 'check_running_test_state')
    @mock.patch.object(LandslideResourceHelper, 'get_running_tests_results')
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
        self.mock_tcl_handler = mock.MagicMock(spec=LsTclHandler)

        self.ls_res_helper = mock.MagicMock(spec=LandslideResourceHelper)

    def test___init__(self, *args):
        ls_tcl_client = LandslideTclClient(self.mock_tcl_handler,
                                           self.ls_res_helper)
        self.assertIsNone(ls_tcl_client._url)
        self.assertIsNone(ls_tcl_client._user)
        self.assertIsNone(ls_tcl_client._library_id)
        self.assertIsNone(ls_tcl_client._basic_library_id)
        self.assertEqual(ls_tcl_client.ts_ids, set())
        self.assertIsInstance(ls_tcl_client._tc_types, set)
        self.assertIsNotNone(ls_tcl_client._tc_types)

    def test_connect_login_success(self, *args):
        lib_id = '123'
        exec_responses = ['java0x2', lib_id, lib_id]
        auth = ('user', 'password')
        ls_tcl_client = LandslideTclClient(self.mock_tcl_handler,
                                           self.ls_res_helper)
        # First execute call returns a login handle
        # Second one represents library id returned by _get_library_id()
        self.mock_tcl_handler.execute.side_effect = exec_responses
        ls_tcl_client.connect(EXAMPLE_URL, auth)
        self.assertEqual(ls_tcl_client._library_id, lib_id)
        self.assertEqual(ls_tcl_client._basic_library_id, lib_id)
        self.assertEqual(ls_tcl_client._url, EXAMPLE_URL)
        self.assertEqual(ls_tcl_client._user, auth[0])
        self.assertEqual(self.mock_tcl_handler.execute.call_count,
                         len(exec_responses))

    def test_connect_login_failed(self, *args):
        exec_responses = ['Login failed']
        auth = ('user', 'password')
        ls_tcl_client = LandslideTclClient(self.mock_tcl_handler,
                                           self.ls_res_helper)
        # First execute call returns a login handle
        # Second one represents library id returned by _get_library_id()
        self.mock_tcl_handler.execute.side_effect = exec_responses
        # with LandslideTclException:
        #     ls_tcl_client.connect(EXAMPLE_URL, auth)
        self.assertRaises(LandslideTclException, ls_tcl_client.connect,
                          EXAMPLE_URL, auth)
        self.assertIsNone(ls_tcl_client._library_id)
        self.assertIsNone(ls_tcl_client._basic_library_id)
        self.assertIsNone(ls_tcl_client._url)
        self.assertIsNone(ls_tcl_client._user)
        self.assertEqual(self.mock_tcl_handler.execute.call_count,
                         len(exec_responses))

    def test_disconnect(self, *args):
        ls_tcl_client = LandslideTclClient(self.mock_tcl_handler,
                                           self.ls_res_helper)
        ls_tcl_client.disconnect()
        self.assertEqual(self.mock_tcl_handler.execute.call_count, 1)
        self.assertIsNone(ls_tcl_client._url)
        self.assertIsNone(ls_tcl_client._user)
        self.assertIsNone(ls_tcl_client._library_id)
        self.assertIsNone(ls_tcl_client._basic_library_id)


class TestLsTclHandler(unittest.TestCase):

    def setUp(self):
        self.mock_lsapi = mock.patch.object(tg_landslide, 'LsApi')
        self.mock_lsapi.start()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.mock_lsapi.stop()

    def test___init__(self, *args):
        self.ls_tcl_handler = LsTclHandler()
        self.assertEquals(self.ls_tcl_handler.tcl_cmds, {})
        self.ls_tcl_handler._ls.tcl.assert_called_once()

    def test_execute(self, *args):
        self.ls_tcl_handler = LsTclHandler()
        self.ls_tcl_handler.execute('command')
        self.assertIn('command', self.ls_tcl_handler.tcl_cmds)
