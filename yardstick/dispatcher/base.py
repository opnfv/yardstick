# Copyright 2013 IBM Corp
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
# yardstick comment: this is a modified copy of
# ceilometer/ceilometer/dispatcher/__init__.py

from __future__ import absolute_import
import abc
import six
import os
import logging
import collections

import yardstick.common.utils as utils
from yardstick.common import constants as consts


LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Base(object):

    def __init__(self, task_id):
        self.task_id = task_id
        self.result = {
            'status': 0,
            'result': {
                'task_id': task_id,
                'criteria': '',
                'info': self._get_common_info(),
                'testcases': {}
            }
        }

    def _add_to_result(self, case, data):
        testcases = self.result['result']['testcases']

        if case not in testcases:
            testcases[case] = {'criteria': 'FAIL', 'tc_data': []}

        testcases[case]['tc_data'].append(data)

    def _update_total_status(self):
        self.result['result']['criteria'] = self._get_total_status()

    def _get_total_status(self):
        testcases = self.result['result']['testcases']

        status = any(t.get('criteria') != 'PASS' for t in testcases.values())
        if status:
            return 'FAIL'
        else:
            return 'PASS'

    def _update_task_status(self):
        self.result['status'] = 1

    def _complete_result(self):
        self._update_total_status()
        self._update_task_status()

    def update_case_status(self, case, status):
        testcases = self.result['result']['testcases']

        if case not in testcases:
            testcases[case] = {'criteria': 'FAIL', 'tc_data': []}

        testcases[case]['criteria'] = status

    def _get_common_info(self):
        info = {
            'deploy_scenario': os.environ.get('DEPLOY_SCENARIO', 'unknown'),
            'installer': os.environ.get('INSTALLER_TYPE', 'unknown'),
            'pod_name': os.environ.get('NODE_NAME', 'unknown'),
            'version': os.environ.get('YARDSTICK_BRANCH', 'unknown'),
        }
        return info

    @abc.abstractmethod
    def setup(self):
        """ Dispatcher setup interface """

    @abc.abstractmethod
    def teardown(self):
        """ Dispatcher teardown interface """

    @abc.abstractmethod
    def push(self, case, data):
        """ Push data interface """

    @abc.abstractmethod
    def flush(self):
        """Flush result data into permanent storage media interface."""


class OutputConfiguration(object):

    def __init__(self, conf):

        if not isinstance(conf, collections.Mapping):
            LOG.error('Output configuration must be a dict')
            self.conf = {}
        else:
            self.conf = conf

        self.out_types = None
        self._init_out_types()
        self.set_configuration()
        self._update_http_target()

    def _init_out_types(self):
        try:
            out_type = os.environ['DISPATCHER']
        except KeyError:
            try:
                out_type = self.conf['DEFAULT']['dispatcher']
            except KeyError:
                out_type = 'file'
        finally:
            self.out_types = out_type.split(',')

    def set_configuration(self):
        for out_type in self.out_types:
            configuration = self._get_sub_configration(out_type)
            params = self.conf['dispatcher_{}'.format(out_type)]
            setattr(self, out_type, configuration(params))

    def _get_sub_configration(self, configuration_type):
        for sub in utils.itersubclasses(ConfigurationBase):
            if sub.__configuration_type__ == configuration_type:
                return sub
        else:
            raise RuntimeError('No such dispatcher found')

    def _update_http_target(self):
        if 'http' in self.out_types:
            try:
                target = os.environ['TARGET']
            except KeyError:
                pass
            else:
                self.http.target = target


class ConfigurationBase(object):

    def __init__(self, conf):
        self.set_configuration(conf)

    def set_configuration(self, conf):
        for k, v in conf.items():
            setattr(self, k, v)


class FileConfiguration(ConfigurationBase):

    __configuration_type__ = 'file'

    def __init__(self, conf):
        self.file_path = consts.DEFAULT_OUTPUT_FILE
        self.max_bytes = None
        self.backup_count = None

        super(FileConfiguration, self).__init__(conf)


class InfluxDBConfiguration(ConfigurationBase):

    __configuration_type__ = 'influxdb'

    def __init__(self, conf):
        # default value, will be updated later
        self.target = 'http://127.0.0.1:8086'
        self.db_name = 'yardstick'
        self.username = 'root'
        self.password = 'root'
        self.timeout = 5

        super(InfluxDBConfiguration, self).__init__(conf)


class HttpConfiguration(ConfigurationBase):

    __configuration_type__ = 'http'

    def __init__(self, conf):
        self.target = 'http://127.0.0.1:8000/results'
        self.timeout = 5

        super(HttpConfiguration, self).__init__(conf)


class NSBConfiguration(ConfigurationBase):

    __configuration_type__ = 'nsb'

    def __init__(self, conf):
        self.trex_path = None
        self.bin_path = None
        self.trex_client_lib = None

        super(NSBConfiguration, self).__init__(conf)


class DispatcherManager(object):

    def __init__(self, task_id, conf):
        self.configuration = OutputConfiguration(conf)
        self.dispatchers = []

        self._init_dispatchers(task_id)

    def _init_dispatchers(self, task_id):
        for out_type in self.configuration.out_types:
            dispatcher = self._get_sub_dispatcher(out_type)
            self.dispatchers.append(dispatcher(task_id, self.configuration))

    def _get_sub_dispatcher(self, out_type):
        for sub in utils.itersubclasses(Base):
            if out_type.capitalize() == sub.__dispatcher_type__:
                return sub
        else:
            raise RuntimeError("No such dispatcher_type %s" % out_type)

    def update_case_status(self, case, status):
        for dispatcher in self.dispatchers:
            dispatcher.update_case_status(case, status)

    def update_file_path(self, path):
        try:
            file_configuration = getattr(self.configuration, 'file')
        except AttributeError:
            LOG.error('No file configuration found')
        else:
            file_configuration.file_path = path

    def get_result(self):
        return self.dispatchers[0].result

    def push(self, case, data):
        for dispatcher in self.dispatchers:
            dispatcher.push(case, data)

    def flush(self):
        for dispatcher in self.dispatchers:
            dispatcher.flush()
