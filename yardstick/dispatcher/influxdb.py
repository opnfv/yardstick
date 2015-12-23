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
    """Dispatcher class for posting data into a influxdb target.
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
        tags = {
            "pod_name": os.environ.get('POD_NAME', 'unknown'),
            "installer": os.environ.get('INSTALLER_TYPE', 'unknown'),
            "version": os.environ.get('YARDSTICK_VERSION', 'unknown')
        }
        self.tags = ",".join([k+"="+v for k, v in tags.items()])

    '''
    line protocol format:
        <measurement>[,<tag-key>=<tag-value>...] <field-key>=<field-value>\
            [,<field2-key>=<field2-value>...] [unix-nano-timestamp]

    here use case_name as measurement
    '''
    def _data_to_line_protocol(self, data):
        line = ",".join([self.case_name, self.tags])
        line += " " + format_for_dashboard(self.case_name, data)
        # TODO add timestamp ???
        return line

    def record_result_data(self, data):
        LOG.debug('Test result : %s' % json.dumps(data))
        self.raw_result.append(data)
        if self.target == '':
            # if the target was not set, do not do anything
            LOG.error('Dispatcher target was not set, no data will'
                      'be posted.')
            return

        if isinstance(data, dict) and "scenario_cfg" in data:
            self.case_name = data["scenario_cfg"]["type"]
            return

        if self.case_name == "":
            LOG.error('Test result : %s' % json.dumps(self.result))
            LOG.error('The case_name cannot be found, no data will be posted.')
            return

        try:
            line = self._data_to_line_protocol(data)
            LOG.debug('Test result line format : %s' % line)
            res = requests.post(self.influxdb_url,
                                data=line,
                                timeout=self.timeout)
            LOG.debug('Test result posting finished with status code'
                      ' %d.' % res.status_code)
        except Exception as err:
            LOG.exception('Failed to record result data: %s',
                          err)

    def flush_result_data(self):
        LOG.debug('Test result all : %s' % json.dumps(self.raw_result))


def get_cases():
    """
    get the list of the supported test cases
    TODO: update the list when adding a new test case for the dashboard
    """
    return ["Ping", "Iperf", "Netperf", "Pktgen", "Fio", "Lmbench",
            "Perf", "Cyclictest"]


def check_case_exist(case):
    """
    check if the test case exists
    if the test case is not defined or not declared in the list
    return False
    """
    cases = get_cases()

    if (case is None or case not in cases):
        return False
    else:
        return True


def format_for_dashboard(case, results):
    """
    generic method calling the method corresponding to the test case
    check that the test case is properly declared first
    then build the call to the specific method
    """
    if check_case_exist(case):
        cmd = "format_" + case + "_for_dashboard(results)"
        res = eval(cmd)
    else:
        res = []
        print "Test cases not declared"
    return res


def format_Ping_for_dashboard(results):
    return "rtt=%f" % results["benchmark"]["data"]["rtt"]
