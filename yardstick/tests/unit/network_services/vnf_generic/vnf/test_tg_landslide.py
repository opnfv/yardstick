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
import unittest
import uuid

from yardstick.benchmark.contexts import base as ctx_base
from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh
from yardstick.tests import STL_MOCKS

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.tg_landslide import LandslideTrafficGen
    from yardstick.network_services.vnf_generic.vnf.tg_landslide import LandslideResourceHelper, \
        LandslideTclClient, LsTclHandler, RestApiError
    from yardstick.network_services.traffic_profile.landslide_profile import LandslideProfile


SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'
NAME = "tg__0"

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

VNFD = {'vnfd:vnfd-catalog': {
    'vnfd': [
        {
            'short-name': 'landslide',
            'vdu': [
                {
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


@mock.patch("yardstick.network_services.vnf_generic.vnf.tg_landslide.LsApi")
class TestLandslideTrafficGen(unittest.TestCase):

    SCENARIO_CFG = {
        'session_profile': '/traffic_profiles/landslide/landslide_session_default_bearer.yaml',
        'task_path': '',
        'runner':
            {
                'type': 'Iteration',
                'iterations': 1
            },
        'nodes':
            {'tg__0': 'tg__0.traffic_gen',
             'vnf__0': 'vnf__0.vnf_epc'
             },
        'topology': 'landslide_tg_topology.yaml',
        'type': 'NSPerf',
        'traffic_profile': '../../traffic_profiles/landslide/landslide_dmf_udp.yaml',
        'options':
            {
                'test_cases': [
                    {
                        'BearerAddrPool': '2002::2',
                        'type': 'SGW_Node',
                        'BearerV4AddrPool': '2.0.0.2',
                        'Sessions': '90000'
                    },
                    {
                        'StartRate': '900.0',
                        'type': 'SGW_Nodal',
                        'DisconnectRate': '900.0',
                        'Sessions': '90000'
                    }
                ],
                'dmf':
                    {
                        'transactionRate': 1000,
                        'packetSize': 512
                    }
            }
    }

    CONTEXT_CFG = {
        'contexts': [
            {
                'type': 'Node',
                'name': 'traffic_gen',
                'file': '/etc/yardstick/nodes/pod_landslide.yaml'
            },
            {
                'type': 'Node',
                'name': 'vnf_epc',
                'file': '/etc/yardstick/nodes/pod_vepc_sut.yaml'
            }
        ]
    }

    SESSION_PROFILE = {
        'keywords': '',
        'duration': 60,
        'description': 'UE default bearer creation test case',
        'name': 'default_bearer_capacity',
        'tsGroups': [
            {
                'testCases': [
                    {
                        'type': 'SGW_Node',
                        'name': '',
                        'parameters':
                            {
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
                                'SgwUserAddr':
                                    {
                                        'numLinksOrNodes': 1,
                                        'phy': 'eth1',
                                        'forcedEthInterface': '',
                                        'ip': 'SGW_USER_IP',
                                        'class': 'TestNode',
                                        'ethStatsEnabled': False,
                                        'mtu': 1500
                                    },
                                'SgwControlAddr':
                                    {
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
                    }
                ],
                'tsId': 'SGW_NODE_TS_NAME'
            },
            {
                'testCases': [
                    {
                        'type': 'SGW_Nodal',
                        'name': '',
                        'parameters':
                            {
                                'DataTraffic': 'Continuous',
                                'TrafficStartType': 'When All Sessions Established',
                                'NetworkHost': 'Local',
                                'Gtp2Imsi': '505024101215074',
                                'Dmf':
                                    {
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
                                'MmeControlAddr':
                                    {
                                        'numLinksOrNodes': 1,
                                        'phy': 'eth1',
                                        'forcedEthInterface': '',
                                        'ip': 'MME_CONTROL_IP',
                                        'class': 'TestNode',
                                        'ethStatsEnabled': False,
                                        'mtu': 1500
                                    },
                                'SgwUserSut':
                                    {
                                        'class': 'Sut',
                                        'name': 'SGW_USER_NAME'
                                    },
                                'TestActivity': 'Capacity Test',
                                'NetworkHostAddrLocal':
                                    {
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
                                'SgwSut':
                                    {
                                        'class': 'Sut',
                                        'name': 'SGW_CONTROL_NAME'
                                    },
                                'TrafficMtu': '1500',
                                'Gtp2Version': '13.6.0',
                                'Gtp2Imei': '50502410121507',
                                'PgwNodeEn': 'false',
                                'StartRate': '1000.0',
                                'PgwV4Sut':
                                    {
                                        'class': 'Sut',
                                        'name': 'PGW_SUT_NAME'
                                    },
                                'DefaultBearers': '1',
                                'EnbUserAddr':
                                    {
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
                    }
                ],
                'tsId': 'SGW_NODAL_TS_NAME'
            }
        ]
    }

    TRAFFIC_PROFILE = {
        "schema": "nsb:traffic_profile:0.1",
        "name": "LandslideProfile",
        "description": "Spirent Landslide traffic profile",
        "traffic_profile":
            {
                "traffic_type": "LandslideProfile"},
        "dmf_config": {
            "dmf": {
                "library": "test",
                "name": "Basic UDP"
                },
            "description": "Basic data flow using UDP/IP",
            "keywords": "UDP",
            "dataProtocol": "udp"
            }
        }

    RESERVATIONS = [
        {'tsName': 'TestServer_1',
         'phySubnets': [
             {'numIps': 20,
              'base': '10.42.32.100',
              'mask': '/24',
              'name': 'eth1'}],
         'tsId': 'TestServer_1',
         'tsIndex': 0},
        {'tsName': 'TestServer_2',
         'phySubnets': [
             {'numIps': 100,
              'base': '10.42.32.1',
              'mask': '/24',
              'name': 'eth1'},
             {'numIps': 100,
              'base': '10.42.33.1',
              'mask': '/24',
              'name': 'eth2'}],
         'tsId': 'TestServer_2',
         'tsIndex': 1}]

    EXAMPLE_URL = 'http://example.com/'
    SUCCESS_CREATED_CODE = 201
    SUCCESS_OK_CODE = 200
    SUCCESS_RECORD_ID = 5
    TEST_USER_ID = 11

    def setUp(self):
        self._id = uuid.uuid1().int

    @mock.patch(SSH_HELPER)
    def test___init__(self, ssh, *args):
        mock_ssh(ssh)
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        self.assertIsInstance(ls_traffic_gen.resource_helper, LandslideResourceHelper)

    @mock.patch.object(LandslideResourceHelper, 'get_running_tests')
    @mock.patch(SSH_HELPER)
    def test_run_traffic(self, ssh, mock_get_tests, *args):
        mock_ssh(ssh)
        session_profile = copy.deepcopy(self.SESSION_PROFILE)
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        ls_traffic_gen.resource_helper._url = self.EXAMPLE_URL
        ls_traffic_gen.scenario_helper.scenario_cfg = self.SCENARIO_CFG
        ls_traffic_gen.session_profile = session_profile
        mock_traffic_profile = mock.Mock(spec=LandslideProfile)
        mock_traffic_profile.dmf_config = {'keywords': 'UDP', 'dataProtocol': 'udp'}
        mock_traffic_profile.params = self.TRAFFIC_PROFILE
        ls_traffic_gen.resource_helper._user_id = self.TEST_USER_ID
        mock_get_tests.return_value = [{'id': self.SUCCESS_RECORD_ID,
                                        'testStateOrStep': 'COMPLETE'}]
        mock_post = mock.Mock()
        mock_post.status_code = self.SUCCESS_CREATED_CODE
        mock_post.json.return_value = {'id': self.SUCCESS_RECORD_ID}
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.post.return_value = mock_post
        ls_traffic_gen.resource_helper.session = mock_session
        ls_traffic_gen.resource_helper._tcl = mock.Mock()
        self.assertIsNone(ls_traffic_gen.run_traffic(mock_traffic_profile))
        self.assertEqual(ls_traffic_gen.resource_helper.run_id, self.SUCCESS_RECORD_ID)
        mock_traffic_profile.update_dmf.assert_called_with(
            ls_traffic_gen.scenario_helper.all_options)
        ls_traffic_gen.resource_helper._tcl.create_dmf.assert_called_with(
            mock_traffic_profile.dmf_config)
        ls_traffic_gen.resource_helper._tcl.create_test_session.assert_called_with(
            session_profile)

    @mock.patch.object(LandslideResourceHelper, 'check_running_test_state')
    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, mock_check_running_test_state, *args):
        mock_ssh(ssh)
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        ls_traffic_gen.resource_helper.run_id = self.SUCCESS_RECORD_ID
        mock_check_running_test_state.return_value = 'COMPLETE'
        self.assertEqual(ls_traffic_gen.collect_kpi(), {'done': True})
        mock_check_running_test_state.assert_called_once()

    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, *args):
        mock_ssh(ssh)
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        ls_traffic_gen.resource_helper._tcl = mock.Mock()
        self.assertIsNone(ls_traffic_gen.terminate())
        ls_traffic_gen.resource_helper._tcl.disconnect.assert_called_once()

    @mock.patch(SSH_HELPER)
    def test__update_session_suts(self, ssh, *args):

        def get_testnode_param(role, key, session_prof):
            for group in session_prof['tsGroups']:
                for tc in group['testCases']:
                    tc_params = tc['parameters']
                    if tc_params.get(role):
                        return tc_params[role][key]

        def get_sut_param(role, key, suts):
            for sut in suts:
                if sut.get('role') == role:
                    return sut[key]

        # TestNode to verify
        testnode_role = 'SgwControlAddr'
        # SUT to verify
        sut_role = 'SgwUserSut'

        mock_ssh(ssh)
        session_profile = copy.deepcopy(self.SESSION_PROFILE)
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        ls_traffic_gen.session_profile = session_profile
        session_tcs = [_tc for _ts_group in ls_traffic_gen.session_profile['tsGroups']
                       for _tc in _ts_group['testCases']]
        config_suts = [config['suts'] for config in vnfd['config']]
        for suts, tc in zip(config_suts, session_tcs):
            self.assertEqual(tc, ls_traffic_gen._update_session_suts(suts, tc))

        # Verify TestNode class objects keys were updated
        for _key in {'ip', 'phy', 'nextHop'}:
            self.assertEqual(
                get_testnode_param(testnode_role, _key, ls_traffic_gen.session_profile),
                get_sut_param(testnode_role, _key, TS1_SUTS))
        # Verify Sut class objects name was updated
        self.assertEqual(
            get_testnode_param(sut_role, 'name', ls_traffic_gen.session_profile),
            get_sut_param(sut_role, 'name', TS2_SUTS))

    @mock.patch(SSH_HELPER)
    def test__update_session_test_servers(self, ssh, *args):
        mock_ssh(ssh)
        session_profile = copy.deepcopy(self.SESSION_PROFILE)
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        ls_traffic_gen.session_profile = session_profile
        for ts_index, ts in enumerate(TEST_SERVERS):
            self.assertIsNone(ls_traffic_gen._update_session_test_servers(ts, ts_index))
        # Verify preResolvedArpAddress key was added
        self.assertTrue(any(_item.get('preResolvedArpAddress')
                            for _item in ls_traffic_gen.session_profile['tsGroups']))
        # Verify reservations key was added to session profile
        self.assertIsNotNone(ls_traffic_gen.session_profile.get("reservations"))
        self.assertEqual(self.RESERVATIONS, ls_traffic_gen.session_profile["reservations"])
        self.assertEqual('true', ls_traffic_gen.session_profile.get("reservePorts"))

    @mock.patch(SSH_HELPER)
    def test__update_session_tc_params(self, ssh, *args):

        def get_session_tc_param_value(param, tc_type, session_prof):
            for test_group in session_prof['tsGroups']:
                session_tc = test_group['testCases'][0]
                if session_tc['type'] == tc_type:
                    return session_tc['parameters'].get(param)

        mock_ssh(ssh)
        session_profile = copy.deepcopy(self.SESSION_PROFILE)
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        ls_traffic_gen.session_profile = session_profile
        session_tcs = [_tc for _ts_group in ls_traffic_gen.session_profile['tsGroups']
                       for _tc in _ts_group['testCases']]
        scenario_tcs = [_tc for _tc in self.SCENARIO_CFG['options']['test_cases']]
        for tc_options, tc in zip(scenario_tcs, session_tcs):
            self.assertEqual(tc, ls_traffic_gen._update_session_tc_params(tc_options, tc))

        # Verify that each test case parameter was updated
        for _tc in self.SCENARIO_CFG['options']['test_cases']:
            for _key, _val in _tc.items():
                if _key != 'type':
                    self.assertEqual(get_session_tc_param_value(
                        _key, _tc.get('type'), ls_traffic_gen.session_profile), _val)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.open_relative_file')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.yaml_load')
    @mock.patch.object(LandslideTrafficGen, '_update_session_test_servers')
    @mock.patch.object(LandslideTrafficGen, '_update_session_suts')
    @mock.patch.object(LandslideTrafficGen, '_update_session_tc_params')
    @mock.patch(SSH_HELPER)
    def test__load_session_profile(self, ssh, mock_upd_ses_tc_params, mock_upd_ses_suts,
                                   mock_upd_ses_ts, mock_yaml_load, *args):
        mock_ssh(ssh)
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        ls_traffic_gen.scenario_helper.scenario_cfg = self.SCENARIO_CFG
        mock_yaml_load.return_value = self.SESSION_PROFILE
        self.assertIsNone(ls_traffic_gen._load_session_profile())
        self.assertIsNotNone(ls_traffic_gen.session_profile)
        # Number of blocks in configuration files
        # Number of test servers, suts and tc params blocks should be equal
        _config_files_blocks_num = len([item['test_server'] for item in vnfd['config']])
        self.assertEqual(_config_files_blocks_num, mock_upd_ses_ts.call_count)
        self.assertEqual(_config_files_blocks_num, mock_upd_ses_suts.call_count)
        self.assertEqual(_config_files_blocks_num, mock_upd_ses_tc_params.call_count)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.open_relative_file')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.yaml_load')
    @mock.patch(SSH_HELPER)
    def test__load_session_profile_unequal_num_of_cfg_blocks(self, ssh, mock_yaml_load, *args):
        mock_ssh(ssh)
        vnfd = copy.deepcopy(VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        ls_traffic_gen.scenario_helper.scenario_cfg = self.SCENARIO_CFG
        mock_yaml_load.return_value = self.SESSION_PROFILE
        # Delete test_servers item from pod file to make it not valid
        ls_traffic_gen.vnfd_helper['config'].pop()
        with self.assertRaises(RuntimeError):
            ls_traffic_gen._load_session_profile()

    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.open_relative_file')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.yaml_load')
    @mock.patch(SSH_HELPER)
    def test__load_session_profile_test_type_mismatch(self, ssh, mock_yaml_load, *args):
        mock_ssh(ssh)
        vnfd = copy.deepcopy(VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        # Swap test servers data in pod file
        vnfd['config'][0], vnfd['config'][1] = vnfd['config'][1], vnfd['config'][0]
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        ls_traffic_gen.scenario_helper.scenario_cfg = self.SCENARIO_CFG
        mock_yaml_load.return_value = self.SESSION_PROFILE
        with self.assertRaises(RuntimeError):
            ls_traffic_gen._load_session_profile()

    @mock.patch.object(ctx_base.Context, 'get_context_from_server', return_value='fake_context')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.Process')
    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh, *args):
        mock_ssh(ssh)
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ls_traffic_gen = LandslideTrafficGen(NAME, vnfd, self._id)
        ls_traffic_gen._tg_process = mock.MagicMock()
        ls_traffic_gen._tg_process.start = mock.Mock()
        ls_traffic_gen.resource_helper.connect = mock.Mock()
        ls_traffic_gen.resource_helper.create_test_servers = mock.Mock()
        ls_traffic_gen.resource_helper.create_suts = mock.Mock()
        ls_traffic_gen._load_session_profile = mock.Mock()
        self.assertIsNone(ls_traffic_gen.instantiate(self.SCENARIO_CFG, self.CONTEXT_CFG))
        ls_traffic_gen.resource_helper.connect.assert_called_once()
        ls_traffic_gen.resource_helper.create_test_servers.assert_called_once()
        _suts_blocks_num = len([item['suts'] for item in vnfd['config']])
        self.assertEqual(_suts_blocks_num,
                         ls_traffic_gen.resource_helper.create_suts.call_count)
        ls_traffic_gen._load_session_profile.assert_called_once()


@mock.patch("yardstick.network_services.vnf_generic.vnf.tg_landslide.LsApi")
@mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.SetupEnvHelper')
class TestLandslideResourceHelper(unittest.TestCase):

    DMF_CFG = {
        "dmf": {
            "library": "test",
            "name": "Basic UDP"
            }
    }

    TAS_INFO = VNFD['vnfd:vnfd-catalog']['vnfd'][0]['mgmt-interface']
    PROTO = 8080 if TAS_INFO['proto'] == 'http' else 8181

    EXAMPLE_URL = ''.join([TAS_INFO['proto'], '://', TAS_INFO['ip'], ':', str(PROTO), '/api/'])
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
        "users": [
            {
                "url": ''.join([EXAMPLE_URL, 'users/', str(SUCCESS_RECORD_ID)]),
                "id": SUCCESS_RECORD_ID,
                "level": 1,
                "username": TEST_USER
            }
        ]
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

    RUNNING_TESTS_DATA = {
        "runningTests": [
            {
                "url": ''.join([EXAMPLE_URL, "runningTests/3"]),
                "measurementsUrl": ''.join([EXAMPLE_URL, "runningTests/3/measurements"]),
                "criteriaUrl": ''.join([EXAMPLE_URL, "runningTests/3/criteria"]),
                "noteToUser": "",
                "id": 3,
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

    def test___init__(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        self.assertIsInstance(ls_resource_helper, LandslideResourceHelper)
        self.assertIsNone(ls_resource_helper.run_id)

    @mock.patch.object(LandslideResourceHelper, 'stop_running_tests')
    @mock.patch.object(LandslideResourceHelper, 'get_running_tests')
    def test_abort_running_tests_no_running_tests(self, mock_get_tests, mock_stop_tests,
                                                  env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        tests_data = [{'id': self.SUCCESS_RECORD_ID, 'testStateOrStep': 'COMPLETE'}]
        mock_get_tests.return_value = tests_data
        self.assertIsNone(ls_resource_helper.abort_running_tests())
        mock_stop_tests.assert_not_called()

    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.time.sleep')
    @mock.patch.object(LandslideResourceHelper, 'stop_running_tests')
    @mock.patch.object(LandslideResourceHelper, 'get_running_tests')
    def test_abort_running_tests(self, mock_get_tests, mock_stop_tests, env_helper_mock, *args):
        test_states_seq = iter(['RUNNING', 'COMPLETE'])

        def configure_mock(*args, **kwargs):
            return [{'id': self.SUCCESS_RECORD_ID,
                    'testStateOrStep': next(test_states_seq)}]

        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        mock_get_tests.side_effect = configure_mock
        self.assertIsNone(ls_resource_helper.abort_running_tests())
        mock_stop_tests.assert_called_once_with(running_test_id=self.SUCCESS_RECORD_ID,
                                                force=True)
        self.assertEquals(2, mock_get_tests.call_count)

    @mock.patch.object(LandslideResourceHelper, 'stop_running_tests')
    @mock.patch.object(LandslideResourceHelper, 'get_running_tests')
    def test_abort_running_tests_error(self, mock_get_tests, mock_stop_tests,
                                       env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        tests_data = {'id': self.SUCCESS_RECORD_ID, 'testStateOrStep': 'RUNNING'}
        mock_get_tests.return_value = [tests_data]
        with self.assertRaises(RuntimeError):
            ls_resource_helper.abort_running_tests(timeout=1, delay=1)
        mock_stop_tests.assert_called_with(running_test_id=self.SUCCESS_RECORD_ID, force=True)

    def test__build_url(self, env_helper_mock, *args):
        resource = 'users'
        action = {'action': 'userCreate'}
        expected_url = ''.join([self.EXAMPLE_URL, 'users?action=userCreate'])
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        self.assertEqual(expected_url, ls_resource_helper._build_url(resource, action))

    def test__build_url_error(self, env_helper_mock, *args):
        resource = ''
        action = {'action': 'userCreate'}
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        with self.assertRaises(ValueError):
            ls_resource_helper._build_url(resource, action)

    def test_get_response_params(self, env_helper_mock, *args):
        method = 'get'
        resource = 'users'
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.USERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        ls_resource_helper.session = mock_session
        resp = ls_resource_helper.get_response_params(method, resource)
        self.assertTrue(resp)

    @mock.patch.object(LandslideResourceHelper, '_get_users')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.time')
    def test__create_user(self, mock_time, mock_get_users, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_time.strftime.return_value = self.EXPIRE_DATE
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        self.assertEqual(self.SUCCESS_RECORD_ID,
                         ls_resource_helper._create_user(self.AUTH_DATA))
        mock_get_users.assert_not_called()

    @mock.patch.object(LandslideResourceHelper, '_get_users')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.time')
    def test__create_user_username_exists(self, mock_time, mock_get_users,
                                          env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_time.strftime.return_value = self.EXPIRE_DATE
        mock_get_users.return_value = self.USERS_DATA['users']
        post_resp_data = {'status_code': self.ERROR_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID,
                                                'apiCode': self.NOT_MODIFIED_CODE}}
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper._create_user(self.AUTH_DATA)
        mock_get_users.assert_called_once_with(self.TAS_INFO['user'])
        self.assertEqual(res, self.SUCCESS_RECORD_ID)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.time')
    def test__create_user_error(self, mock_time, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_time.strftime.return_value = self.EXPIRE_DATE
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                          'json.return_value': {'apiCode': self.ERROR_CODE}}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        with self.assertRaises(RestApiError):
            ls_resource_helper._create_user(self.AUTH_DATA)

    def test__modify_user(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        post_data = {'username': 'test_user'}
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper._modify_user(username=self.TEST_USER, fields=post_data)
        self.assertEquals(self.SUCCESS_RECORD_ID, res)

    def test__delete_user(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        ls_resource_helper.session = mock_session
        self.assertIsNone(ls_resource_helper._delete_user(username=self.TEST_USER))

    def test__get_users(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.USERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        ls_resource_helper.session = mock_session
        self.assertEqual(self.USERS_DATA['users'], ls_resource_helper._get_users())

    def test_exec_rest_request(self, env_helper_mock, *args):
        resource = 'testServers'
        action = {'action': 'modify'}
        expected_url = ''.join([self.EXAMPLE_URL, 'testServers?action=modify'])
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        self.assertIsNotNone(ls_resource_helper.exec_rest_request('post', resource, action))
        ls_resource_helper.session.post.assert_called_once_with(expected_url, json={})

    def test_exec_rest_request_unsupported_method_error(self, env_helper_mock, *args):
        resource = 'testServers'
        action = {'action': 'modify'}
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        with self.assertRaises(ValueError):
            ls_resource_helper.exec_rest_request('patch', resource, action)

    def test_exec_rest_request_missed_action_arg(self, env_helper_mock, *args):
        resource = 'testServers'
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        with self.assertRaises(ValueError):
            ls_resource_helper.exec_rest_request('post', resource)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_landslide.time')
    def test_connect(self, mock_time, env_helper_mock, *args):
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        mock_time.strftime.return_value = self.EXPIRE_DATE
        env_helper_mock.vnfd_helper = vnfd
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._tcl = mock.Mock()
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session = mock.MagicMock(spec=requests.Session, headers={})
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        self.assertIsInstance(ls_resource_helper.connect(), requests.Session)
        ls_resource_helper._tcl.connect.assert_called_once_with(
            self.TAS_INFO['ip'], (self.TAS_INFO['user'], self.TAS_INFO['password']))

    def test_disconnect(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._tcl = mock.Mock()
        self.assertIsNone(ls_resource_helper.disconnect())
        self.assertIsNone(ls_resource_helper.session)
        ls_resource_helper._tcl.disconnect.assert_called_once()

    def test_terminate(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        self.assertIsNone(ls_resource_helper.terminate())
        self.assertEqual(self.TEST_TERMINATED, ls_resource_helper._terminated.value)

    def test_create_dmf(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._tcl = mock.Mock()
        self.assertIsNone(ls_resource_helper.create_dmf(self.DMF_CFG))
        ls_resource_helper._tcl.create_dmf.assert_called_once_with(self.DMF_CFG)

    def test_delete_dmf(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._tcl = mock.Mock()
        self.assertIsNone(ls_resource_helper.delete_dmf(self.DMF_CFG))
        ls_resource_helper._tcl.delete_dmf.assert_called_once_with(self.DMF_CFG)

    @mock.patch.object(LandslideResourceHelper, 'configure_sut')
    def test_create_suts(self, mock_configure_sut, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        self.assertIsNone(ls_resource_helper.create_suts(TS1_SUTS))
        mock_configure_sut.assert_not_called()

    @mock.patch.object(LandslideResourceHelper, 'configure_sut')
    def test_create_suts_sut_exists(self, mock_configure_sut, env_helper_mock, *args):
        sut_name = 'test_sut'
        suts = [
            {'name': sut_name,
             'role': 'SgwControlAddr',
             'managementIp': '12.0.1.1',
             'ip': '10.42.32.100'
             }
        ]

        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.NOT_MODIFIED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        self.assertIsNone(ls_resource_helper.create_suts(suts))
        mock_configure_sut.assert_called_once_with(
            sut_name=sut_name,
            json_data={k: v for k, v in suts[0].items()
                       if k not in {'phy', 'nextHop', 'role', 'name'}})

    def test_get_suts(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.SUTS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        ls_resource_helper.session = mock_session
        self.assertIsNotNone(ls_resource_helper.get_suts())

    def test_configure_sut(self, env_helper_mock, *args):
        post_data = {'managementIp': '2.2.2.2'}
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                          'json.return_value': {'id': self.SUCCESS_RECORD_ID}}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        self.assertIsNone(ls_resource_helper.configure_sut('test_name', post_data))
        mock_session.post.assert_called_once()

    def test_configure_sut_error(self, env_helper_mock, *args):
        post_data = {'managementIp': '2.2.2.2'}
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.NOT_MODIFIED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        with self.assertRaises(RestApiError):
            ls_resource_helper.configure_sut('test_name', post_data)

    def test_delete_suts(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.SUTS_DATA}
        delete_resp_data = {'status_code': self.SUCCESS_OK_CODE}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        mock_session.delete.return_value.configure_mock(**delete_resp_data)
        ls_resource_helper.session = mock_session
        self.assertIsNone(ls_resource_helper.delete_suts())
        mock_session.delete.assert_called_once()

    @mock.patch.object(LandslideResourceHelper, 'get_test_servers')
    def test__check_test_servers_state(self, mock_get_test_servers, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        mock_get_test_servers.return_value = self.TEST_SERVERS_DATA['testServers']
        self.assertIsNone(ls_resource_helper._check_test_servers_state())
        mock_get_test_servers.assert_called_once()

    @mock.patch.object(LandslideResourceHelper, 'get_test_servers')
    def test__check_test_servers_state_server_not_ready(self, mock_get_test_servers,
                                                        env_helper_mock, *args):
        test_servers_not_ready = [
            {
                "url": ''.join([self.EXAMPLE_URL, "testServers/1"]),
                "id": 1,
                "name": "TestServer_1",
                "state": "NOT_READY",
                "version": "16.4.0.10"
            }
        ]

        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        mock_get_test_servers.return_value = test_servers_not_ready
        with self.assertRaises(RuntimeError):
            ls_resource_helper._check_test_servers_state(timeout=1, delay=0)

    @mock.patch.object(LandslideResourceHelper, '_check_test_servers_state')
    def test_create_test_servers(self, mock_check_ts_state, env_helper_mock, *args):
        test_servers_ids = [ts['id'] for ts in self.TEST_SERVERS_DATA['testServers']]
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper.license_data['lic_id'] = self.TAS_INFO['license']
        ls_resource_helper._tcl.create_test_server = mock.Mock()
        ls_resource_helper._tcl.create_test_server.side_effect = test_servers_ids
        self.assertIsNone(ls_resource_helper.create_test_servers(TEST_SERVERS))
        mock_check_ts_state.assert_called_once_with(test_servers_ids)

    @mock.patch.object(LandslideTclClient, 'resolve_test_server_name')
    @mock.patch.object(LsTclHandler, 'execute')
    def test_create_test_servers_error(self, mock_execute, mock_resolve_ts_name,
                                       env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper.license_data['lic_id'] = self.TAS_INFO['license']
        # Return message for case test server wasn't created
        mock_execute.return_value = 'TS not found'
        # Return message for case test server name wasn't resolved
        mock_resolve_ts_name.return_value = 'TS not found'
        with self.assertRaises(RuntimeError):
            ls_resource_helper.create_test_servers(TEST_SERVERS)

    def test_get_test_servers(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_SERVERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper.get_test_servers()
        self.assertEqual(res, self.TEST_SERVERS_DATA['testServers'])

    def test_configure_test_servers(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_SERVERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper.configure_test_servers(action={'action': 'recycle'})
        self.assertIsNotNone(res)
        self.assertEquals(mock_session.post.call_count,
                          len(self.TEST_SERVERS_DATA['testServers']))

    def test_delete_test_servers(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_SERVERS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        ls_resource_helper.session = mock_session
        self.assertIsNone(ls_resource_helper.delete_test_servers())
        self.assertEquals(mock_session.delete.call_count,
                          len(self.TEST_SERVERS_DATA['testServers']))

    def test_create_test_session(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._user_id = self.SUCCESS_RECORD_ID
        ls_resource_helper._tcl = mock.Mock()
        test_session = {'name': 'test'}
        self.assertIsNone(ls_resource_helper.create_test_session(test_session))
        ls_resource_helper._tcl.create_test_session.assert_called_once_with(
            {'name': 'test', 'library': self.SUCCESS_RECORD_ID})

    @mock.patch.object(LandslideTclClient, 'resolve_test_server_name', return_value='Not Found')
    def test_create_test_session_ts_name_not_found(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._user_id = self.SUCCESS_RECORD_ID
        test_session = {
            'duration': 60,
            'description': 'UE default bearer creation test case',
            'name': 'default_bearer_capacity',
            'tsGroups': [{'testCases': [{'type': 'SGW_Node',
                                         'name': ''}],
                          'tsId': 'TestServer_3'}]
            }
        with self.assertRaises(RuntimeError):
            ls_resource_helper.create_test_session(test_session)

    def test_get_test_session(self, env_helper_mock, *args):
        test_session = {"name": self.TEST_SESSION_NAME}
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        ls_resource_helper._user_id = self.SUCCESS_RECORD_ID
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': test_session}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper.get_test_session(self.TEST_SESSION_NAME)
        self.assertEquals(test_session, res)

    def test_configure_test_session(self, env_helper_mock, *args):
        test_session = {'name': self.TEST_SESSION_NAME}
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        ls_resource_helper._user_id = self.SUCCESS_RECORD_ID
        ls_resource_helper.user_lib_uri = 'libraries/{{}}/{}'.format(
            ls_resource_helper.test_session_uri)
        mock_session = mock.MagicMock(spec=requests.Session)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper.configure_test_session(self.TEST_SESSION_NAME, test_session)
        self.assertIsNotNone(res)
        mock_session.post.assert_called_once()

    def test_delete_test_session(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        ls_resource_helper._user_id = self.SUCCESS_RECORD_ID
        ls_resource_helper.user_lib_uri = 'libraries/{{}}/{}'.format(
            ls_resource_helper.test_session_uri)
        mock_session = mock.MagicMock(spec=requests.Session)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper.delete_test_session(self.TEST_SESSION_NAME)
        self.assertIsNotNone(res)
        mock_session.delete.assert_called_once()

    def test_create_running_tests(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        ls_resource_helper._user_id = self.SUCCESS_RECORD_ID
        test_session = {'id': self.SUCCESS_RECORD_ID}
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.SUCCESS_CREATED_CODE,
                          'json.return_value': test_session}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        ls_resource_helper.create_running_tests(self.TEST_SESSION_NAME)
        self.assertEquals(self.SUCCESS_RECORD_ID, ls_resource_helper.run_id)

    def test_create_running_tests_error(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        ls_resource_helper._user_id = self.SUCCESS_RECORD_ID
        mock_session = mock.MagicMock(spec=requests.Session)
        post_resp_data = {'status_code': self.NOT_MODIFIED_CODE}
        mock_session.post.return_value.configure_mock(**post_resp_data)
        ls_resource_helper.session = mock_session
        with self.assertRaises(RestApiError):
            ls_resource_helper.create_running_tests(self.TEST_SESSION_NAME)

    def test_get_running_tests(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.RUNNING_TESTS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper.get_running_tests()
        self.assertEquals(self.RUNNING_TESTS_DATA['runningTests'], res)

    def test_delete_running_tests(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        delete_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                            'json.return_value': self.RUNNING_TESTS_DATA}
        mock_session.delete.return_value.configure_mock(**delete_resp_data)
        ls_resource_helper.session = mock_session
        self.assertIsNone(ls_resource_helper.delete_running_tests())

    def test__running_tests_action(self, env_helper_mock, *args):
        action = 'abort'
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper._running_tests_action(self.SUCCESS_RECORD_ID, action)
        self.assertIsNone(res)

    @mock.patch.object(LandslideResourceHelper, '_running_tests_action')
    def test_stop_running_tests(self, mock_tests_action, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        res = ls_resource_helper.stop_running_tests(self.SUCCESS_RECORD_ID)
        self.assertIsNone(res)
        mock_tests_action.assert_called_once()

    def test_check_running_test_state(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.RUNNING_TESTS_DATA["runningTests"][0]}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper.check_running_test_state(self.SUCCESS_RECORD_ID)
        self.assertEquals(self.RUNNING_TESTS_DATA["runningTests"][0]['testStateOrStep'], res)

    def test_get_running_tests_results(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper._url = self.EXAMPLE_URL
        mock_session = mock.MagicMock(spec=requests.Session)
        get_resp_data = {'status_code': self.SUCCESS_OK_CODE,
                         'json.return_value': self.TEST_RESULTS_DATA}
        mock_session.get.return_value.configure_mock(**get_resp_data)
        ls_resource_helper.session = mock_session
        res = ls_resource_helper.get_running_tests_results(self.SUCCESS_RECORD_ID)
        self.assertEquals(self.TEST_RESULTS_DATA, res)

    def test__write_results(self, env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        res = ls_resource_helper._write_results(self.TEST_RESULTS_DATA)
        self.assertIsNotNone(res)

    @mock.patch.object(LandslideResourceHelper, 'check_running_test_state')
    @mock.patch.object(LandslideResourceHelper, 'get_running_tests_results')
    def test_collect_kpi_test_running(self, mock_tests_results, mock_tests_state,
                                      env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper.run_id = self.SUCCESS_RECORD_ID
        mock_tests_state.return_value = 'RUNNING'
        mock_tests_results.return_value = self.TEST_RESULTS_DATA
        res = ls_resource_helper.collect_kpi()
        self.assertNotIn('done', res)
        mock_tests_state.assert_called_once_with(ls_resource_helper.run_id)
        mock_tests_results.assert_called_once_with(ls_resource_helper.run_id)

    @mock.patch.object(LandslideResourceHelper, 'check_running_test_state')
    @mock.patch.object(LandslideResourceHelper, 'get_running_tests_results')
    def test_collect_kpi_test_completed(self, mock_tests_results, mock_tests_state,
                                        env_helper_mock, *args):
        ls_resource_helper = LandslideResourceHelper(env_helper_mock)
        ls_resource_helper.run_id = self.SUCCESS_RECORD_ID
        mock_tests_state.return_value = 'COMPLETE'
        res = ls_resource_helper.collect_kpi()
        self.assertIsNotNone(res)
        mock_tests_state.assert_called_once_with(ls_resource_helper.run_id)
        mock_tests_results.assert_not_called()
        self.assertDictContainsSubset({'done': True}, res)


if __name__ == '__main__':
    unittest.main()
