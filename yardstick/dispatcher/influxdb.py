##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import

import logging
import os
import time

import requests
import six
from oslo_config import cfg
from oslo_serialization import jsonutils

from third_party.influxdb.influxdb_line_protocol import make_lines
from yardstick.dispatcher.base import Base as DispatchBase

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
influx_dispatcher_opts = [
    cfg.StrOpt('target',
               default='http://127.0.0.1:8086',
               help='The target where the http request will be sent. '
                    'If this is not set, no data will be posted. For '
                    'example: target = http://hostname:1234/path'),
    cfg.StrOpt('db_name',
               default='yardstick',
               help='The database name to store test results.'),
    cfg.StrOpt('username',
               default='root',
               help='The user name to access database.'),
    cfg.StrOpt('password',
               default='root',
               help='The user password to access database.'),
    cfg.IntOpt('timeout',
               default=5,
               help='The max time in seconds to wait for a request to '
                    'timeout.'),
]

CONF.register_opts(influx_dispatcher_opts, group="dispatcher_influxdb")


class InfluxdbDispatcher(DispatchBase):
    """Dispatcher class for posting data into an influxdb target.
    """

    __dispatcher_type__ = "Influxdb"

    def __init__(self, conf):
        super(InfluxdbDispatcher, self).__init__(conf)
        self.timeout = CONF.dispatcher_influxdb.timeout
        self.target = CONF.dispatcher_influxdb.target
        self.db_name = CONF.dispatcher_influxdb.db_name
        self.username = CONF.dispatcher_influxdb.username
        self.password = CONF.dispatcher_influxdb.password
        self.influxdb_url = "%s/write?db=%s" % (self.target, self.db_name)
        self.raw_result = []
        self.case_name = ""
        self.tc = ""
        self.task_id = -1
        self.runners_info = {}
        self.static_tags = {
            "pod_name": os.environ.get('NODE_NAME', 'unknown'),
            "installer": os.environ.get('INSTALLER_TYPE', 'unknown'),
            "deploy_scenario": os.environ.get('DEPLOY_SCENARIO', 'unknown'),
            "version": os.path.basename(os.environ.get('YARDSTICK_BRANCH',
                                                       'unknown'))

        }

    def _dict_key_flatten(self, data):
        next_data = {}

        if not [v for v in data.values()
                if type(v) == dict or type(v) == list]:
            return data

        for k, v in six.iteritems(data):
            if type(v) == dict:
                for n_k, n_v in six.iteritems(v):
                    next_data["%s.%s" % (k, n_k)] = n_v
            elif type(v) == list:
                for index, item in enumerate(v):
                    next_data["%s%d" % (k, index)] = item
            else:
                next_data[k] = v

        return self._dict_key_flatten(next_data)

    def _get_nano_timestamp(self, results):
        try:
            timestamp = results["benchmark"]["timestamp"]
        except Exception:
            timestamp = time.time()

        return str(int(float(timestamp) * 1000000000))

    def _get_extended_tags(self, data):
        runner_info = self.runners_info[data["runner_id"]]
        tags = {
            "runner_id": data["runner_id"],
            "task_id": self.task_id,
            "scenarios": runner_info["scenarios"]
        }
        if "host" in runner_info:
            tags["host"] = runner_info["host"]
        if "target" in runner_info:
            tags["target"] = runner_info["target"]

        return tags

    def _data_to_line_protocol(self, data):
        msg = {}
        point = {}
        point["measurement"] = self.tc
        point["fields"] = self._dict_key_flatten(data["benchmark"]["data"])
        point["time"] = self._get_nano_timestamp(data)
        point["tags"] = self._get_extended_tags(data)
        msg["points"] = [point]
        msg["tags"] = self.static_tags

        return make_lines(msg).encode('utf-8')

    def record_result_data(self, data):
        LOG.debug('Test result : %s', jsonutils.dump_as_bytes(data))
        self.raw_result.append(data)
        if self.target == '':
            # if the target was not set, do not do anything
            LOG.error('Dispatcher target was not set, no data will'
                      'be posted.')
            return -1

        if isinstance(data, dict) and "scenario_cfg" in data:
            self.tc = data["scenario_cfg"]["tc"]
            self.task_id = data["scenario_cfg"]["task_id"]
            scenario_cfg = data["scenario_cfg"]
            runner_id = data["runner_id"]
            self.runners_info[runner_id] = {"scenarios": scenario_cfg["type"]}
            if "host" in scenario_cfg:
                self.runners_info[runner_id]["host"] = scenario_cfg["host"]
            if "target" in scenario_cfg:
                self.runners_info[runner_id]["target"] = scenario_cfg["target"]
            return 0

        if self.tc == "":
            LOG.error('Test result : %s', jsonutils.dump_as_bytes(data))
            LOG.error('The case_name cannot be found, no data will be posted.')
            return -1

        try:
            line = self._data_to_line_protocol(data)
            LOG.debug('Test result line format : %s', line)
            res = requests.post(self.influxdb_url,
                                data=line,
                                auth=(self.username, self.password),
                                timeout=self.timeout)
            if res.status_code != 204:
                LOG.error('Test result posting finished with status code'
                          ' %d.', res.status_code)
                LOG.error(res.text)

        except Exception as err:
            LOG.exception('Failed to record result data: %s',
                          err)
            return -1
        return 0

    def flush_result_data(self):
        LOG.debug('Test result all : %s',
                  jsonutils.dump_as_bytes(self.raw_result))
        return 0
