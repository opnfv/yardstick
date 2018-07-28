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

import logging

from yardstick.common import exceptions
from yardstick.common import utils as common_utils
from yardstick.network_services import utils as net_serv_utils
from yardstick.network_services.vnf_generic.vnf import sample_vnf

try:
    from lsapi import LsApi
except ImportError:
    LsApi = common_utils.ErrorClass

LOG = logging.getLogger(__name__)


class LandslideResourceHelper(sample_vnf.ClientResourceHelper):
    """Landslide TG helper class"""

    REST_STATUS_CODES = {'OK': 200, 'CREATED': 201, 'NO CHANGE': 409}
    REST_API_CODES = {'NOT MODIFIED': 500810}

    def __init__(self, setup_helper):
        super(LandslideResourceHelper, self).__init__(setup_helper)
        self._result = {}
        self.vnfd_helper = setup_helper.vnfd_helper
        self.scenario_helper = setup_helper.scenario_helper

        # TCL session initialization
        self._tcl = LandslideTclClient(LsTclHandler(), self)

    def terminate(self):
        raise NotImplementedError()

    def collect_kpi(self):
        raise NotImplementedError()


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
        self.tcl_server_ip = None
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

    def connect(self, tcl_server_ip, username, password):
        """ Connect to TCL server with username and password

        :param tcl_server_ip: TCL server IP address
        :type tcl_server_ip: str
        :param username: existing username on TCL server
        :type username: str
        :param password: password related to username on TCL server
        :type password: str
        """
        LOG.info("connect: server='%s' user='%s'", tcl_server_ip, username)
        res = self._tcl.execute(
            "ls::login {} {} {}".format(tcl_server_ip, username, password))
        if 'java0x' not in res:  # handle assignment reflects login success
            raise exceptions.LandslideTclException(
                "connect: login failed ='{}'.".format(res))
        self._library_id = self._tcl.execute(
            "ls::get [ls::query LibraryInfo -userLibraryName {}] -Id".format(
                username))
        self._basic_library_id = self._get_library_id('Basic')
        self.tcl_server_ip = tcl_server_ip
        self._user = username
        LOG.debug("connect: user='%s' me='%s' basic='%s'", self._user,
                  self._library_id,
                  self._basic_library_id)

    def disconnect(self):
        """ Disconnect from TCL server. Drop TCL connection configuration """
        LOG.info("disconnect: server='%s' user='%s'",
                 self.tcl_server_ip, self._user)
        self._tcl.execute("ls::logout")
        self.tcl_server_ip = None
        self._user = None
        self._library_id = None
        self._basic_library_id = None

    def _add_test_server(self, name, ip):
        try:
            # Check if test server exists with name equal to _ts_name
            ts_id = int(self.resolve_test_server_name(name))
        except ValueError:
            # Such test server does not exist. Attempt to create it
            ts_id = self._tcl.execute(
                'ls::perform AddTs -Name "{}" -Ip "{}"'.format(name, ip))
            try:
                int(ts_id)
            except ValueError:
                # Failed to create test server, e.g. limit reached
                raise RuntimeError(
                    'Failed to create test server: "{}". {}'.format(name,
                                                                    ts_id))
        return ts_id

    def _update_license(self, name):
        """ Setup/update test server license

        :param name: test server name
        :type name: str
        """
        # Retrieve current TsInfo configuration, result stored in handle "ts"
        self._tcl.execute(
            'set ts [ls::retrieve TsInfo -Name "{}"]'.format(name))

        # Set license ID, if it differs from current one, update test server
        _curr_lic_id = self._tcl.execute('ls::get $ts -RequestedLicense')
        if _curr_lic_id != self._ts_context.license_data['lic_id']:
            self._tcl.execute('ls::config $ts -RequestedLicense {}'.format(
                self._ts_context.license_data['lic_id']))
            self._tcl.execute('ls::perform ModifyTs $ts')

    def _set_thread_model(self, name, thread_model):
        # Retrieve test server configuration, store it in handle "tsc"
        _cfguser_password = self._ts_context.vnfd_helper['mgmt-interface'][
            'cfguser_password']
        self._tcl.execute(
            'set tsc [ls::perform RetrieveTsConfiguration '
            '-name "{}" {}]'.format(name, _cfguser_password))
        # Configure ThreadModel, if it differs from current one
        thread_model_map = {'Legacy': 'V0',
                            'Max': 'V1',
                            'Fireball': 'V1_FB3'}
        _model = thread_model_map[thread_model]
        _curr_model = self._tcl.execute('ls::get $tsc -ThreadModel')
        if _curr_model != _model:
            self._tcl.execute(
                'ls::config $tsc -ThreadModel "{}"'.format(_model))
            self._tcl.execute(
                'ls::perform ApplyTsConfiguration $tsc {}'.format(
                    _cfguser_password))

    def create_test_server(self, test_server):
        _ts_thread_model = test_server.get('thread_model')
        _ts_name = test_server['name']

        ts_id = self._add_test_server(_ts_name, test_server['ip'])

        self._update_license(_ts_name)

        # Skip below code modifying thread_model if it is not defined
        if _ts_thread_model:
            self._set_thread_model(_ts_name, _ts_thread_model)

        return ts_id

    def create_test_session(self, test_session):
        """ Create, configure and save Landslide test session object.

        :param test_session: Landslide TestSession object
        :type test_session: dict
        """
        LOG.info("create_test_session: name='%s'", test_session['name'])
        self._tcl.execute('set test_ [ls::create TestSession]')
        self._tcl.execute('ls::config $test_ -Library {} -Name "{}"'.format(
                self._library_id, test_session['name']))
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
        """ Create, configure and save Landslide Data Message Flow object.

        :param dmf: Landslide Data Message Flow object
        :type: dmf: dict
        """
        self._tcl.execute('set dmf_ [ls::create Dmf]')
        _lib_id = self._get_library_id(dmf['dmf']['library'])
        self._tcl.execute('ls::config $dmf_ -Library {} -Name "{}"'.format(
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
        raise NotImplementedError

    def _save_dmf(self):
        # Call 'Validate' to set default values for missing parameters
        res = self._tcl.execute('ls::perform Validate -Dmf $dmf_')
        if res == 'Invalid':
            res = self._tcl.execute('ls::get $dmf_ -ErrorsAndWarnings')
            LOG.error("_save_dmf: %s", res)
            raise exceptions.LandslideTclException("_save_dmf: {}".format(res))
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
        raise NotImplementedError

    def _save_test_session(self):
        # Call 'Validate' to set default values for missing parameters
        res = self._tcl.execute('ls::perform Validate -TestSession $test_')
        if res == 'Invalid':
            res = self._tcl.execute('ls::get $test_ -ErrorsAndWarnings')
            raise exceptions.LandslideTclException(
                "_save_test_session: {}".format(res))
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
            raise exceptions.LandslideTclException(
                "_get_library_id: library='{}' not found.".format(
                    library))

        return _library_id

    def resolve_test_server_name(self, ts_name):
        return self._tcl.execute("ls::query TsId {}".format(ts_name))


class LsTclHandler(object):
    """Landslide TCL Handler class"""

    LS_OK = "ls_ok"
    JRE_PATH = net_serv_utils.get_nsb_option('jre_path_i386')

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
