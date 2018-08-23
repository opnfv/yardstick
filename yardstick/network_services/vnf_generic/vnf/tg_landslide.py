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

from __future__ import absolute_import
import logging
import requests
import time
from collections import Mapping

import multiprocessing

from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.vnf_generic.vnf.sample_vnf import \
    ClientResourceHelper
from yardstick.common import utils
from yardstick.common.exceptions import LandslideTclException, RestApiError

try:
    from lsapi import LsApi
except ImportError:
    LsApi = utils.ErrorClass

LOG = logging.getLogger(__name__)


class LandslideResourceHelper(ClientResourceHelper):
    """Landslide TG helper class"""

    REST_STATUS_CODES = {'OK': 200, 'CREATED': 201, 'NO CHANGE': 409}
    REST_API_CODES = {'NOT MODIFIED': 500810}

    def __init__(self, setup_helper):
        super(LandslideResourceHelper, self).__init__(setup_helper)
        self._queue = multiprocessing.Queue()
        self._result = {}
        self._terminated = multiprocessing.Value('i', 0)
        self.vnfd_helper = setup_helper.vnfd_helper
        self.scenario_helper = setup_helper.scenario_helper

        # TAS Manager config initialization
        self._url = None
        self._user_id = None
        self.session = None
        self.license_data = {}

        # TCL session initialization
        self._tcl = LandslideTclClient(LsTclHandler(), self)

        self.session = requests.Session()
        self.running_tests_uri = 'runningTests'
        self.test_session_uri = 'testSessions'
        self.test_serv_uri = 'testServers'
        self.suts_uri = 'suts'
        self.users_uri = 'users'
        self.user_lib_uri = None
        self.run_id = None

    def abort_running_tests(self, timeout=60, delay=5):
        """ Abort running test sessions, if any """
        _start_time = time.time()
        while time.time() < _start_time + timeout:
            run_tests_states = {x['id']: x['testStateOrStep']
                                for x in self.get_running_tests()}
            if not set(run_tests_states.values()).difference(
                    {'COMPLETE', 'COMPLETE_ERROR'}):
                break
            else:
                [self.stop_running_tests(running_test_id=_id, force=True)
                 for _id, _state in run_tests_states.items()
                 if 'COMPLETE' not in _state]
            time.sleep(delay)
        else:
            raise RuntimeError(
                'Some test runs not stopped during {} seconds'.format(timeout))

    def _build_url(self, resource, action=None):
        """ Build URL string

        :param resource: REST API resource name
        :type resource: str
        :param action: actions name and value
        :type action: dict('name': <str>, 'value': <str>)
        :returns str: REST API resource name with optional action info
        """
        # Action is optional and accepted only in presence of resource param
        if action and not resource:
            raise ValueError("Resource name not provided")
        # Concatenate actions
        _action = ''.join(['?{}={}'.format(k, v) for k, v in
                           action.items()]) if action else ''

        return ''.join([self._url, resource, _action])

    def get_response_params(self, method, resource, params=None):
        """ Retrieve params from JSON response of specific resource URL

        :param method: one of supported REST API methods
        :type method: str
        :param resource: URI, requested resource name
        :type resource: str
        :param params: attributes to be found in JSON response
        :type params: list(str)
        """
        _res = []
        params = params if params else []
        response = self.exec_rest_request(method, resource)
        # Get substring between last slash sign and question mark (if any)
        url_last_part = resource.rsplit('/', 1)[-1].rsplit('?', 1)[0]
        _response_json = response.json()
        # Expect dict(), if URL last part and top dict key don't match
        # Else, if they match, expect list()
        k, v = list(_response_json.items())[0]
        if k != url_last_part:
            v = [v]  # v: list(dict(str: str))
        # Extract params, or whole list of dicts (without top level key)
        for x in v:
            _res.append({param: x[param] for param in params} if params else x)
        return _res

    def _create_user(self, auth, level=1):
        """ Create new user

        :param auth: data to create user account on REST server
        :type auth: dict
        :param level: Landslide user permissions level
        :type level: int
        :returns int: user id
        """
        # Set expiration date in two years since account creation date
        _exp_date = time.strftime(
            '{}/%m/%d %H:%M %Z'.format(time.gmtime().tm_year + 2))
        _username = auth['user']
        _fields = {"contactInformation": "", "expiresOn": _exp_date,
                   "fullName": "Test User",
                   "isActive": "true", "level": level,
                   "password": auth['password'],
                   "username": _username}
        _response = self.exec_rest_request('post', self.users_uri,
                                           json_data=_fields, raise_exc=False)
        _resp_json = _response.json()
        if _response.status_code == self.REST_STATUS_CODES['CREATED']:
            # New user created
            _id = _resp_json['id']
            LOG.info("New user created: username='%s', id='%s'", _username,
                     _id)
        elif _resp_json.get('apiCode') == self.REST_API_CODES['NOT MODIFIED']:
            # User already exists
            LOG.info("Account '%s' already exists.", _username)
            # Get user id
            _id = self._modify_user(_username, {"isActive": "true"})['id']
        else:
            raise RestApiError(
                'Error during new user "{}" creation'.format(_username))
        return _id

    def _modify_user(self, username, fields):
        """ Modify information about existing user

        :param username: user name of account to be modified
        :type username: str
        :param fields: data to modify user account on REST server
        :type fields: dict
        :returns dict: user info
        """
        _response = self.exec_rest_request('post', self.users_uri,
                                           action={'username': username},
                                           json_data=fields, raise_exc=False)
        if _response.status_code == self.REST_STATUS_CODES['OK']:
            _response = _response.json()
        else:
            raise RestApiError('Error during user "{}" data update: {}'.format(
                username,
                _response.status_code))
        LOG.info("User account '%s' modified: '%s'", username, _response)
        return _response

    def _delete_user(self, username):
        """ Delete user account

        :param username: username field
        :type username: str
        :returns bool: True if succeeded
        """
        self.exec_rest_request('delete', self.users_uri,
                               action={'username': username})

    def _get_users(self, username=None):
        """ Get user records from REST server

        :param username: username field
        :type username: None|str
        :returns list(dict): empty list, or user record, or list of all users
        """
        _response = self.get_response_params('get', self.users_uri)
        _res = [u for u in _response if
                u['username'] == username] if username else _response
        return _res

    def exec_rest_request(self, method, resource, action=None, json_data=None,
                          logs=True, raise_exc=True):
        """ Execute REST API request, return response object

        :param method: one of supported requests ('post', 'get', 'delete')
        :type method: str
        :param resource: URL of resource
        :type resource: str
        :param action: data used to provide URI located after question mark
        :type action: dict
        :param json_data: mandatory only for 'post' method
        :type json_data: dict
        :param logs: debug logs display flag
        :type raise_exc: bool
        :param raise_exc: if True, raise exception on REST API call error
        :returns requests.Response(): REST API call response object
        """
        json_data = json_data if json_data else {}
        action = action if action else {}
        _method = method.upper()
        method = method.lower()
        if method not in ('post', 'get', 'delete'):
            raise ValueError("Method '{}' not supported".format(_method))

        if method == 'post' and not action:
            if not (json_data and isinstance(json_data, Mapping)):
                raise ValueError(
                    'JSON data missing in {} request'.format(_method))

        r = getattr(self.session, method)(self._build_url(resource, action),
                                          json=json_data)
        if raise_exc and not r.ok:
            msg = 'Failed to "{}" resource "{}". Reason: "{}"'.format(
                method, self._build_url(resource, action), r.reason)
            raise RestApiError(msg)

        if logs:
            LOG.debug("RC: %s | Request: %s | URL: %s", r.status_code, method,
                      r.request.url)
            LOG.debug("Response: %s", r.json())
        return r

    def connect(self):
        """Connect to RESTful server using test user account"""
        tas_info = self.vnfd_helper['mgmt-interface']
        # Supported REST Server ports: HTTP - 8080, HTTPS - 8181
        _port = '8080' if tas_info['proto'] == 'http' else '8181'
        tas_info.update({'port': _port})
        self._url = '{proto}://{ip}:{port}/api/'.format(**tas_info)
        self.session.headers.update({'Accept': 'application/json',
                                     'Content-type': 'application/json'})
        # Login with super user to create test user
        self.session.auth = (
            tas_info['super-user'], tas_info['super-user-password'])
        LOG.info("Connect using superuser: server='%s'", self._url)
        auth = {x: tas_info[x] for x in ('user', 'password')}
        self._user_id = self._create_user(auth)
        # Login with test user
        self.session.auth = auth['user'], auth['password']
        # Test user validity
        self.exec_rest_request('get', '')

        self.user_lib_uri = 'libraries/{{}}/{}'.format(self.test_session_uri)
        LOG.info("Login with test user: server='%s'", self._url)
        # Read existing license
        self.license_data['lic_id'] = tas_info['license']

        # Tcl client init
        self._tcl.connect(tas_info['ip'], self.session.auth)

        return self.session

    def disconnect(self):
        self.session = None
        self._tcl.disconnect()

    def terminate(self):
        self._terminated.value = 1

    def create_dmf(self, dmf):
        if isinstance(dmf, list):
            for _dmf in dmf:
                self._tcl.create_dmf(_dmf)
        else:
            self._tcl.create_dmf(dmf)

    def delete_dmf(self, dmf):
        if isinstance(dmf, list):
            for _dmf in dmf:
                self._tcl.delete_dmf(_dmf)
        else:
            self._tcl.delete_dmf(dmf)

    def create_suts(self, suts):
        # Keep only supported keys in suts object
        for _sut in suts:
            sut_entry = {k: v for k, v in _sut.items()
                         if k not in {'phy', 'nextHop', 'role'}}
            _response = self.exec_rest_request(
                'post', self.suts_uri, json_data=sut_entry,
                logs=False, raise_exc=False)
            if _response.status_code != self.REST_STATUS_CODES['CREATED']:
                LOG.info(_response.reason)  # Failed to create
                _name = sut_entry.pop('name')
                # Modify existing SUT
                self.configure_sut(sut_name=_name, json_data=sut_entry)
            else:
                LOG.info("SUT created: %s", sut_entry)

    def get_suts(self, suts_id=None):
        if suts_id:
            _suts = self.exec_rest_request(
                'get', '{}/{}'.format(self.suts_uri, suts_id)).json()
        else:
            _suts = self.get_response_params('get', self.suts_uri)

        return _suts

    def configure_sut(self, sut_name, json_data):
        """ Modify information of specific SUTs

        :param sut_name: name of existing SUT
        :type sut_name: str
        :param json_data: SUT settings
        :type json_data: dict()
        """
        LOG.info("Modifying SUT information...")
        _response = self.exec_rest_request('post',
                                           self.suts_uri,
                                           action={'name': sut_name},
                                           json_data=json_data,
                                           raise_exc=False)
        if _response.status_code not in {self.REST_STATUS_CODES[x] for x in
                                         {'OK', 'NO CHANGE'}}:
            raise RestApiError(_response.reason)

        LOG.info("Modified SUT: %s", sut_name)

    def delete_suts(self, suts_ids=None):
        if not suts_ids:
            _curr_suts = self.get_response_params('get', self.suts_uri)
            suts_ids = [x['id'] for x in _curr_suts]
        LOG.info("Deleting SUTs with following IDs: %s", suts_ids)
        for _id in suts_ids:
            self.exec_rest_request('delete',
                                   '{}/{}'.format(self.suts_uri, _id))
            LOG.info("\tDone for SUT id: %s", _id)

    def _check_test_servers_state(self, test_servers_ids=None, delay=10,
                                  timeout=300):
        LOG.info("Waiting for related test servers state change to READY...")
        # Wait on state change
        _start_time = time.time()
        while time.time() - _start_time < timeout:
            ts_ids_not_ready = {x['id'] for x in
                                self.get_test_servers(test_servers_ids)
                                if x['state'] != 'READY'}
            if ts_ids_not_ready == set():
                break
            time.sleep(delay)
        else:
            raise RuntimeError(
                'Test servers not in READY state after {} seconds.'.format(
                    timeout))

    def create_test_servers(self, test_servers):
        """ Create test servers

        :param test_servers: input data for test servers creation
                             mandatory fields: managementIp
                             optional fields: name
        :type test_servers: list(dict)
        """
        _ts_ids = []
        for _ts in test_servers:
            _msg = 'Created test server "%(name)s"'
            _ts_ids.append(self._tcl.create_test_server(_ts))
            if _ts.get('thread_model'):
                _msg += ' in mode: "%(thread_model)s"'
                LOG.info(_msg, _ts)

        self._check_test_servers_state(_ts_ids)

    def get_test_servers(self, test_server_ids=None):
        if not test_server_ids:  # Get all test servers info
            _test_servers = self.exec_rest_request(
                'get', self.test_serv_uri).json()[self.test_serv_uri]
            LOG.info("Current test servers configuration: %s", _test_servers)
            return _test_servers

        _test_servers = []
        for _id in test_server_ids:
            _test_servers.append(self.exec_rest_request(
                'get', '{}/{}'.format(self.test_serv_uri, _id)).json())
        LOG.info("Current test servers configuration: %s", _test_servers)
        return _test_servers

    def configure_test_servers(self, action, json_data=None,
                               test_server_ids=None):
        if not test_server_ids:
            test_server_ids = [x['id'] for x in self.get_test_servers()]
        elif isinstance(test_server_ids, int):
            test_server_ids = [test_server_ids]
        for _id in test_server_ids:
            self.exec_rest_request('post',
                                   '{}/{}'.format(self.test_serv_uri, _id),
                                   action=action, json_data=json_data)
            LOG.info("Test server (id: %s) configuration done: %s", _id,
                     action)
        return test_server_ids

    def delete_test_servers(self, test_servers_ids=None):
        # Delete test servers
        for _ts in self.get_test_servers(test_servers_ids):
            self.exec_rest_request('delete', '{}/{}'.format(self.test_serv_uri,
                                                            _ts['id']))
            LOG.info("Deleted test server: %s", _ts['name'])

    def create_test_session(self, test_session):
        # Use tcl client to create session
        test_session['library'] = self._user_id
        LOG.debug("Creating session='%s'", test_session['name'])
        self._tcl.create_test_session(test_session)

    def get_test_session(self, test_session_name=None):
        if test_session_name:
            uri = 'libraries/{}/{}/{}'.format(self._user_id,
                                              self.test_session_uri,
                                              test_session_name)
        else:
            uri = self.user_lib_uri.format(self._user_id)
        _test_sessions = self.exec_rest_request('get', uri).json()
        return _test_sessions

    def configure_test_session(self, template_name, test_session):
        # Override specified test session parameters
        LOG.info('Update test session parameters: %s', test_session['name'])
        test_session.update({'library': self._user_id})
        return self.exec_rest_request(
            method='post',
            action={'action': 'overrideAndSaveAs'},
            json_data=test_session,
            resource='{}/{}'.format(self.user_lib_uri.format(self._user_id),
                                    template_name))

    def delete_test_session(self, test_session):
        return self.exec_rest_request('delete', '{}/{}'.format(
            self.user_lib_uri.format(self._user_id), test_session))

    def create_running_tests(self, test_session_name):
        r = self.exec_rest_request('post',
                                   self.running_tests_uri,
                                   json_data={'library': self._user_id,
                                              'name': test_session_name})
        if r.status_code != self.REST_STATUS_CODES['CREATED']:
            raise RestApiError('Failed to start test session.')
        self.run_id = r.json()['id']

    def get_running_tests(self, running_test_id=None):
        """Get JSON structure of specified running test entity

        :param running_test_id: ID of created running test entity
        :type running_test_id: int
        :returns list: running tests entity
        """
        if not running_test_id:
            running_test_id = ''
        _res_name = '{}/{}'.format(self.running_tests_uri, running_test_id)
        _res = self.exec_rest_request('get', _res_name, logs=False).json()
        # If no run_id specified, skip top level key in response dict.
        # Else return JSON as list
        return _res.get('runningTests', [_res])

    def delete_running_tests(self, running_test_id=None):
        if not running_test_id:
            running_test_id = ''
        _res_name = '{}/{}'.format(self.running_tests_uri, running_test_id)
        self.get_response_params('delete', _res_name)
        LOG.info("Deleted running test with id: %s", running_test_id)

    def _running_tests_action(self, running_test_id, action, json_data=None):
        if not json_data:
            json_data = {}
        # Supported actions:
        # 'stop', 'abort', 'continue', 'update', 'sendTcCommand', 'sendOdc'
        _res_name = '{}/{}'.format(self.running_tests_uri, running_test_id)
        self.exec_rest_request('post', _res_name, {'action': action},
                               json_data)
        LOG.debug("Executed action: '%s' on running test id: %s", action,
                  running_test_id)

    def stop_running_tests(self, running_test_id, json_data=None, force=False):
        _action = 'abort' if force else 'stop'
        self._running_tests_action(running_test_id, _action,
                                   json_data=json_data)
        LOG.info('Performed action: "%s" to test run with id: %s', _action,
                 running_test_id)

    def check_running_test_state(self, run_id):
        r = self.exec_rest_request('get',
                                   '{}/{}'.format(self.running_tests_uri,
                                                  run_id))
        return r.json().get("testStateOrStep")

    def get_running_tests_results(self, run_id):
        _res = self.exec_rest_request(
            'get',
            '{}/{}/{}'.format(self.running_tests_uri,
                              run_id,
                              'measurements')).json()
        return _res

    def _write_results(self, results):
        # Avoid None value at test session start
        _elapsed_time = results['elapsedTime'] if results['elapsedTime'] else 0

        _res_tabs = results.get('tabs')
        # Avoid parsing 'tab' dict key initially (missing or empty)
        if not _res_tabs:
            return

        # Flatten nested dict holding Landslide KPIs of current test run
        flat_kpis_dict = {}
        for _tab, _kpis in _res_tabs.items():
            for _kpi, _value in _kpis.items():
                # Combine table name and KPI name using delimiter "::"
                _key = '::'.join([_tab, _kpi])
                try:
                    # Cast value from str to float
                    # Remove comma and/or measure units, e.g. "us"
                    flat_kpis_dict[_key] = float(
                        _value.split(' ')[0].replace(',', ''))
                except ValueError:  # E.g. if KPI represents datetime
                    pass
            # Use current time for timestamps
        LOG.info("Polling test results of test run id: %s. Elapsed time: %s "
                 "seconds", self.run_id, _elapsed_time)
        return flat_kpis_dict

    def collect_kpi(self):
        if 'COMPLETE' in self.check_running_test_state(self.run_id):
            self._result.update({'done': True})
            return self._result
        _res = self.get_running_tests_results(self.run_id)
        _kpis = self._write_results(_res)
        if _kpis:
            _kpis.update({'run_id': int(self.run_id)})
            _kpis.update({'iteration': _res['iteration']})
            self._result.update(_kpis)
            return self._result


class LandslideTclClient(object):
    """Landslide TG TCL client class"""

    DEFAULT_TEST_NODE = {
        'ethStatsEnabled': True,
        'forcedEthInterface': '',
        'innerVlanId': 0,
        'ip': '',
        'mac': '',
        'mtu': 1500,
        'nextHop': '',
        'numLinksOrNodes': 1,
        'numVlan': 1,
        'phy': '',
        'uniqueVlanAddr': False,
        'vlanDynamic': 0,
        'vlanId': 0,
        'vlanUserPriority': 0,
        'vlanTagType': 0
    }

    TEST_NODE_CMD = \
        'ls::create -TestNode-{} -under $p_ -Type "eth"' \
        ' -Phy "{phy}" -Ip "{ip}" -NumLinksOrNodes {numLinksOrNodes}' \
        ' -NextHop "{nextHop}" -Mac "{mac}" -MTU {mtu} ' \
        ' -ForcedEthInterface "{forcedEthInterface}"' \
        ' -EthStatsEnabled {ethStatsEnabled}' \
        ' -VlanId {vlanId} -VlanUserPriority {vlanUserPriority}' \
        ' -NumVlan {numVlan} -UniqueVlanAddr {uniqueVlanAddr}' \
        ';'

    def __init__(self, tcl_handler, ts_context):
        self._url = None
        self._user = None
        self._library_id = None
        self._basic_library_id = None
        self._tcl = tcl_handler
        self._ts_context = ts_context
        self.ts_ids = set()

        # Test types names expected in session profile, test case and pod files
        self._tc_types = {"SGW_Nodal", "SGW_Node", "MME_Nodal", "PGW_Node",
                          "PCRF_Node"}

        self._class_param_config_handler = {
            "Array": self._configure_array_param,
            "TestNode": self._configure_test_node_param,
            "Sut": self._configure_sut_param,
            "Dmf": self._configure_dmf_param
        }

    def connect(self, url, auth):
        LOG.info("connect: server='%s' user='%s'", url, auth[0])
        res = self._tcl.execute(
            "ls::login {} {} {}".format(url, auth[0], auth[1]))
        if 'java0x' not in res:  # handle assignment reflects login success
            raise LandslideTclException(
                "connect: login failed ='{}'.".format(res))
        self._library_id = self._tcl.execute(
            "ls::get [ls::query LibraryInfo -userLibraryName {}] -Id".format(
                auth[0]))
        self._basic_library_id = self._get_library_id('Basic')
        self._url = url
        self._user = auth[0]
        LOG.debug("connect: user='%s' me='%s' basic='%s'", self._user,
                  self._library_id,
                  self._basic_library_id)

    def disconnect(self):
        LOG.info("disconnect: server='%s' user='%s'", self._url, self._user)
        self._tcl.execute("ls::logout")
        self._url = None
        self._user = None
        self._library_id = None
        self._basic_library_id = None

    def create_test_server(self, test_server):
        thread_model_map = {'Legacy': 'V0',
                            'Max': 'V1',
                            'Fireball': 'V1_FB3'}
        _ts_thread_model = test_server.get('thread_model')
        _ts_name = test_server['name']
        _ts_ip = test_server['ip']
        try:
            # Check if test server exists with name equal to _ts_name
            ts_id = int(self.resolve_test_server_name(_ts_name))
        except ValueError:
            # Such test server does not exist. Attempt to create it
            ts_id = self._tcl.execute(
                'ls::perform AddTs -Name "{}" -Ip "{}"'.format(
                    _ts_name, _ts_ip))
            try:
                int(ts_id)
            except ValueError:
                # Failed to create test server, e.g. limit reached
                raise RuntimeError(
                    'Failed to create test server: "{}". {}'.format(_ts_name,
                                                                    ts_id))
        # Retrieve current TsInfo configuration, result stored in handle "ts"
        self._tcl.execute(
            'set ts [ls::retrieve TsInfo -Name "{}"]'.format(_ts_name))

        # Set license ID, if it differs from current one, update test server
        _curr_lic_id = self._tcl.execute('ls::get $ts -RequestedLicense')
        if _curr_lic_id != self._ts_context.license_data['lic_id']:
            self._tcl.execute('ls::config $ts -RequestedLicense {}'.format(
                self._ts_context.license_data['lic_id']))
            self._tcl.execute('ls::perform ModifyTs $ts')

        # Skip below code modifying thread_model if it is not defined
        if _ts_thread_model:
            # Retrieve test server configuration, store it in handle "tsc"
            _cfguser_password = self._ts_context.vnfd_helper['mgmt-interface'][
                'cfguser_password']
            self._tcl.execute(
                'set tsc [ls::perform RetrieveTsConfiguration '
                '-name "{}" {}]'.format(_ts_name, _cfguser_password))
            # Configure ThreadModel, if it differs from current one
            _model = thread_model_map[_ts_thread_model]
            _curr_model = self._tcl.execute('ls::get $tsc -ThreadModel')
            if _curr_model != _model:
                self._tcl.execute(
                    'ls::config $tsc -ThreadModel "{}"'.format(_model))
                self._tcl.execute(
                    'ls::perform ApplyTsConfiguration $tsc {}'.format(
                        _cfguser_password))
        return ts_id

    def create_test_session(self, test_session):
        LOG.info("create_test_session: name='%s'", test_session['name'])
        self._tcl.execute('set test_ [ls::create TestSession]')
        self._tcl.execute(
            'ls::config $test_ -Library {} -Name "{}"'.format(
                self._library_id,
                test_session['name']))
        self._tcl.execute('ls::config $test_ -Description "{}"'.format(
            test_session['description']))
        if 'keywords' in test_session:
            self._tcl.execute('ls::config $test_ -Keywords "{}"'.format(
                test_session['keywords']))
        if 'duration' in test_session:
            self._tcl.execute('ls::config $test_ -Duration "{}"'.format(
                test_session['duration']))
        if 'iterations' in test_session:
            self._tcl.execute('ls::config $test_ -Iterations "{}"'.format(
                test_session['iterations']))
        if 'reservePorts' in test_session:
            if test_session['reservePorts']:
                self._tcl.execute('ls::config $test_ -Reserve Ports')

        if 'reservations' in test_session:
            for _reservation in test_session['reservations']:
                self._configure_reservation(_reservation)

        if 'reportOptions' in test_session:
            self._configure_report_options(test_session['reportOptions'])

        for _index, _group in enumerate(test_session['tsGroups']):
            self._configure_ts_group(_group, _index)

        self._save_test_session()

    def create_dmf(self, dmf):
        self._tcl.execute('set dmf_ [ls::create Dmf]')
        _lib_id = self._get_library_id(dmf['dmf']['library'])
        self._tcl.execute(
            'ls::config $dmf_ -Library {} -Name "{}"'.format(
                _lib_id,
                dmf['dmf']['name']))
        for _param_key in dmf:
            if _param_key == 'dmf':
                continue
            _param_value = dmf[_param_key]
            if isinstance(_param_value, dict):
                # Configure complex parameter
                _tcl_cmd = 'ls::config $dmf_'
                for _sub_param_key in _param_value:
                    _sub_param_value = _param_value[_sub_param_key]
                    if isinstance(_sub_param_value, str):
                        _tcl_cmd += ' -{} "{}"'.format(_sub_param_key,
                                                       _sub_param_value)
                    else:
                        _tcl_cmd += ' -{} {}'.format(_sub_param_key,
                                                     _sub_param_value)

                self._tcl.execute(_tcl_cmd)
            else:
                # Configure simple parameter
                if isinstance(_param_value, str):
                    self._tcl.execute(
                        'ls::config $dmf_ -{} "{}"'.format(_param_key,
                                                           _param_value))
                else:
                    self._tcl.execute(
                        'ls::config $dmf_ -{} {}'.format(_param_key,
                                                         _param_value))
        self._save_dmf()

    def configure_dmf(self, dmf):
        # Use create to reconfigure and overwrite existing dmf
        self.create_dmf(dmf)

    def delete_dmf(self, dmf):
        LOG.debug("delete_dmf: dmf=%s", dmf['dmf']['name'])
        LOG.debug("delete_dmf: NOT IMPLEMENTED")

    def _save_dmf(self):
        # Call 'Validate' to set default values for missing parameters
        res = self._tcl.execute('ls::perform Validate -Dmf $dmf_')
        if res == 'Invalid':
            res = self._tcl.execute('ls::get $dmf_ -ErrorsAndWarnings')
            LOG.error("_save_dmf: %s", res)
            raise LandslideTclException("_save_dmf: {}".format(res))
        else:
            res = self._tcl.execute('ls::save $dmf_ -overwrite')
            LOG.debug("_save_dmf: result (%s)", res)

    def _configure_report_options(self, options):
        for _option_key in options:
            _option_value = options[_option_key]
            if _option_key == 'format':
                _format = 0
                if _option_value == 'CSV':
                    _format = 1
                self._tcl.execute(
                    'ls::config $test_.ReportOptions -Format {} '
                    '-Ts -3 -Tc -3'.format(_format))
            else:
                self._tcl.execute(
                    'ls::config $test_.ReportOptions -{} {}'.format(
                        _option_key,
                        _option_value))

    def _configure_ts_group(self, ts_group, ts_group_index):
        try:
            _ts_id = int(self.resolve_test_server_name(ts_group['tsId']))
        except ValueError:
            raise RuntimeError('Test server name "{}" does not exist.'.format(
                ts_group['tsId']))
        if _ts_id not in self.ts_ids:
            self._tcl.execute(
                'set tss_ [ls::create TsGroup -under $test_ -tsId {} ]'.format(
                    _ts_id))
            self.ts_ids.add(_ts_id)
        for _case in ts_group.get('testCases', []):
            self._configure_tc_type(_case, ts_group_index)

        self._configure_preresolved_arp(ts_group.get('preResolvedArpAddress'))

    def _configure_tc_type(self, tc, ts_group_index):
        if tc['type'] not in self._tc_types:
            raise RuntimeError('Test type {} not supported.'.format(
                tc['type']))
        tc['type'] = tc['type'].replace('_', ' ')
        res = self._tcl.execute(
            'set tc_ [ls::retrieve testcase -libraryId {0} "{1}"]'.format(
                self._basic_library_id, tc['type']))
        if 'Invalid' in res:
            raise RuntimeError('Test type {} not found in "Basic" '
                               'library.'.format(tc['type']))
        self._tcl.execute(
            'ls::config $test_.TsGroup({}) -children-Tc $tc_'.format(
                ts_group_index))
        self._tcl.execute('ls::config $tc_ -Library {0} -Name "{1}"'.format(
            self._basic_library_id, tc['name']))
        self._tcl.execute(
            'ls::config $tc_ -Description "{}"'.format(tc['type']))
        self._tcl.execute(
            'ls::config $tc_ -Keywords "GTP LTE {}"'.format(tc['type']))
        if 'linked' in tc:
            self._tcl.execute(
                'ls::config $tc_ -Linked {}'.format(tc['linked']))
        if 'AssociatedPhys' in tc:
            self._tcl.execute('ls::config $tc_ -AssociatedPhys "{}"'.format(
                tc['AssociatedPhys']))
        if 'parameters' in tc:
            self._configure_parameters(tc['parameters'])

    def _configure_parameters(self, params):
        self._tcl.execute('set p_ [ls::get $tc_ -children-Parameters(0)]')
        for _param_key in sorted(params):
            _param_value = params[_param_key]
            if isinstance(_param_value, dict):
                # Configure complex parameter
                if _param_value['class'] in self._class_param_config_handler:
                    self._class_param_config_handler[_param_value['class']](
                        _param_key,
                        _param_value)
            else:
                # Configure simple parameter
                self._tcl.execute(
                    'ls::create {} -under $p_ -Value "{}"'.format(
                        _param_key,
                        _param_value))

    def _configure_array_param(self, name, params):
        self._tcl.execute('ls::create -Array-{} -under $p_ ;'.format(name))
        for param in params['array']:
            self._tcl.execute(
                'ls::create ArrayItem -under $p_.{} -Value "{}"'.format(name,
                                                                        param))

    def _configure_test_node_param(self, name, params):
        _params = self.DEFAULT_TEST_NODE
        _params.update(params)

        # TCL command expects lower case 'true' or 'false'
        _params['ethStatsEnabled'] = str(_params['ethStatsEnabled']).lower()
        _params['uniqueVlanAddr'] = str(_params['uniqueVlanAddr']).lower()

        cmd = self.TEST_NODE_CMD.format(name, **_params)
        self._tcl.execute(cmd)

    def _configure_sut_param(self, name, params):
        self._tcl.execute(
            'ls::create -Sut-{} -under $p_ -Name "{}";'.format(name,
                                                               params['name']))

    def _configure_dmf_param(self, name, params):
        self._tcl.execute('ls::create -Dmf-{} -under $p_ ;'.format(name))

        for _flow_index, _flow in enumerate(params['mainflows']):
            _lib_id = self._get_library_id(_flow['library'])
            self._tcl.execute(
                'ls::perform AddDmfMainflow $p_.Dmf {} "{}"'.format(
                    _lib_id,
                    _flow['name']))

            if not params.get('instanceGroups'):
                return

            _instance_group = params['instanceGroups'][_flow_index]

            # Traffic Mixer parameters handling
            for _key in ['mixType', 'rate']:
                if _key in _instance_group:
                    self._tcl.execute(
                        'ls::config $p_.Dmf.InstanceGroup({}) -{} {}'.format(
                            _flow_index, _key, _instance_group[_key]))

            # Assignments parameters handling
            for _row_id, _row in enumerate(_instance_group.get('rows', [])):
                self._tcl.execute(
                    'ls::config $p_.Dmf.InstanceGroup({}).Row({}) -Node {} '
                    '-OverridePort {} -ClientPort {} -Context {} -Role {} '
                    '-PreferredTransport {} -RatingGroup {} '
                    '-ServiceID {}'.format(
                        _flow_index, _row_id, _row['node'],
                        _row['overridePort'], _row['clientPort'],
                        _row['context'], _row['role'], _row['transport'],
                        _row['ratingGroup'], _row['serviceId']))

    def _configure_reservation(self, reservation):
        _ts_id = self.resolve_test_server_name(reservation['tsId'])
        self._tcl.execute(
            'set reservation_ [ls::create Reservation -under $test_]')
        self._tcl.execute(
            'ls::config $reservation_ -TsIndex {} -TsId {} '
            '-TsName "{}"'.format(reservation['tsIndex'],
                                  _ts_id,
                                  reservation['tsName']))
        for _subnet in reservation['phySubnets']:
            self._tcl.execute(
                'set physubnet_ [ls::create PhySubnet -under $reservation_]')
            self._tcl.execute(
                'ls::config $physubnet_ -Name "{}" -Base "{}" -Mask "{}" '
                '-NumIps {}'.format(_subnet['name'], _subnet['base'],
                                    _subnet['mask'], _subnet['numIps']))

    def _configure_preresolved_arp(self, pre_resolved_arp):
        if not pre_resolved_arp:  # Pre-resolved ARP configuration not found
            return
        for _entry in pre_resolved_arp:
            # TsGroup handle name should correspond in _configure_ts_group()
            self._tcl.execute(
                'ls::create PreResolvedArpAddress -under $tss_ '
                '-StartingAddress "{StartingAddress}" '
                '-NumNodes {NumNodes}'.format(**_entry))

    def delete_test_session(self, test_session):
        LOG.debug("delete_test_session: ts=%s", test_session)
        LOG.debug("delete_test_session: NOT IMPLEMENTED")

    def _save_test_session(self):
        # Call 'Validate' to set default values for missing parameters
        res = self._tcl.execute('ls::perform Validate -TestSession $test_')
        if res == 'Invalid':
            res = self._tcl.execute('ls::get $test_ -ErrorsAndWarnings')
            raise LandslideTclException("_save_test_session: {}".format(res))
        else:
            res = self._tcl.execute('ls::save $test_ -overwrite')
            LOG.debug("_save_test_session: result (%s)", res)

    def _get_library_id(self, library):
        _library_id = self._tcl.execute(
            "ls::get [ls::query LibraryInfo -systemLibraryName {}] -Id".format(
                library))
        try:
            int(_library_id)
            return _library_id
        except ValueError:
            pass

        _library_id = self._tcl.execute(
            "ls::get [ls::query LibraryInfo -userLibraryName {}] -Id".format(
                library))
        try:
            int(_library_id)
        except ValueError:
            LOG.error("_get_library_id: library='%s' not found.", library)
            raise LandslideTclException(
                "_get_library_id: library='{}' not found.".format(
                    library))

        return _library_id

    def resolve_test_server_name(self, ts_name):
        return self._tcl.execute("ls::query TsId {}".format(ts_name))


class LsTclHandler(object):
    """Landslide TCL Handler class"""

    LS_OK = "ls_ok"
    JRE_PATH = get_nsb_option('jre_path_i386')

    def __init__(self):
        self.tcl_cmds = {}
        self._ls = LsApi(jre_path=self.JRE_PATH)
        self._ls.tcl(
            "ls::config ApiOptions -NoReturnSuccessResponseString '{}'".format(
                self.LS_OK))

    def execute(self, command):
        res = self._ls.tcl(command)
        self.tcl_cmds[command] = res
        return res
