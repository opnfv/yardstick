##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import os
import json
import logging
import requests
import time

from oslo_config import cfg

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
        self.influxdb_url = "%s/write?db=%s" % (self.target, self.db_name)
        self.raw_result = []
        self.case_name = ""
        self.tc = ""
        self.task_id = -1
        tags = {
            "pod_name": os.environ.get('POD_NAME', 'unknown'),
            "installer": os.environ.get('INSTALLER_TYPE', 'unknown'),
            "version": os.environ.get('YARDSTICK_VERSION', 'unknown')
        }
        self.tags = ",".join([k+"="+v for k, v in tags.items()])

    def _get_extended_tags(self, data):
        tags = {
            "runner_id": data["runner_id"],
            "tc": self.tc,
            "task_id": self.task_id
        }

        return ",".join(["%s=%s" % (k, v) for k, v in tags.items()])

    def _data_to_line_protocol(self, data):
        '''
        line protocol format:
            <measurement>[,<tag-key>=<tag-value>...] <field-key>=<field-value>\
                [,<field2-key>=<field2-value>...] [unix-nano-timestamp]

        here use case_name as measurement
        '''
        extended_tags = self._get_extended_tags(data)
        line = ",".join([self.case_name, self.tags, extended_tags])
        line += " " + format_for_dashboard(self.case_name, data)
        line += " " + get_nano_timestamp(data)
        return line

    def record_result_data(self, data):
        LOG.debug('Test result : %s' % json.dumps(data))
        self.raw_result.append(data)
        if self.target == '':
            # if the target was not set, do not do anything
            LOG.error('Dispatcher target was not set, no data will'
                      'be posted.')
            return -1

        if isinstance(data, dict) and "scenario_cfg" in data:
            self.case_name = data["scenario_cfg"]["type"]
            self.tc = data["scenario_cfg"]["tc"]
            self.task_id = data["scenario_cfg"]["task_id"]
            return 0

        if self.case_name == "":
            LOG.error('Test result : %s' % json.dumps(data))
            LOG.error('The case_name cannot be found, no data will be posted.')
            return -1

        try:
            line = self._data_to_line_protocol(data)
            LOG.debug('Test result line format : %s' % line)
            res = requests.post(self.influxdb_url,
                                data=line,
                                timeout=self.timeout)
            if res.status_code != 204:
                LOG.error('Test result posting finished with status code'
                          ' %d.' % res.status_code)
        except Exception as err:
            LOG.exception('Failed to record result data: %s',
                          err)
            return -1
        return 0

    def flush_result_data(self):
        LOG.debug('Test result all : %s' % json.dumps(self.raw_result))
        return 0


def format_for_dashboard(case, results):
    """
    Generic method calling the method corresponding to the test case
    if specific format method format_Casename_for_dashboard
    (e.g. format_Ping_for_dashboard) exist call it,
    otherwise use general format method 'format_General_for_dashboard'.
    """

    try:
        cmd = "format_" + case + "_for_dashboard(results)"
        res = eval(cmd)
    except NameError:
        cmd = "format_General_for_dashboard(results)"
        res = eval(cmd)
    return res


def format_Ping_for_dashboard(results):
    return "rtt=%f" % results["benchmark"]["data"]["rtt"]


def _general_dict_to_line(data):
    next_data = {}

    # if all the values is not dict or list return join line
    if not [v for v in data.values()
            if type(v) == dict or type(v) == list]:
        return ",".join(["%s=%s" % (k, v) for k, v in data.items()])

    for k, v in data.iteritems():
        if type(v) == dict:
            for n_k, n_v in v.iteritems():
                next_data["%s.%s" % (k, n_k)] = n_v
        elif type(v) == list:
            for index, item in enumerate(v):
                next_data["%s%d" % (k, index)] = item
        else:
            next_data[k] = v

    return _general_dict_to_line(next_data)


def format_General_for_dashboard(results):
    data = results["benchmark"]["data"]

    return _general_dict_to_line(data)


def get_nano_timestamp(results):
    try:
        timestamp = results["benchmark"]["timestamp"]
    except Exception:
        timestamp = time.time()

    return str(int(float(timestamp) * 1000000000))
