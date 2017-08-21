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
import time

import requests

from yardstick.common import utils
from third_party.influxdb.influxdb_line_protocol import make_lines
from yardstick.dispatcher.base import Base as DispatchBase

LOG = logging.getLogger(__name__)


class InfluxdbDispatcher(DispatchBase):
    """Dispatcher class for posting data into an influxdb target.
    """

    __dispatcher_type__ = "Influxdb"

    def __init__(self, conf):
        super(InfluxdbDispatcher, self).__init__(conf)
        db_conf = conf['dispatcher_influxdb']
        self.timeout = int(db_conf.get('timeout', 5))
        self.target = db_conf.get('target', 'http://127.0.0.1:8086')
        self.db_name = db_conf.get('db_name', 'yardstick')
        self.username = db_conf.get('username', 'root')
        self.password = db_conf.get('password', 'root')

        self.influxdb_url = "%s/write?db=%s" % (self.target, self.db_name)

        self.task_id = -1

    def flush_result_data(self, data):
        LOG.debug('Test result all : %s', data)
        if self.target == '':
            # if the target was not set, do not do anything
            LOG.error('Dispatcher target was not set, no data will be posted.')

        result = data['result']
        self.tags = result['info']
        self.task_id = result['task_id']
        self.criteria = result['criteria']
        testcases = result['testcases']

        for case, data in testcases.items():
            tc_criteria = data['criteria']
            for record in data['tc_data']:
                self._upload_one_record(record, case, tc_criteria)

        return 0

    def _upload_one_record(self, data, case, tc_criteria):
        try:
            line = self._data_to_line_protocol(data, case, tc_criteria)
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
            LOG.exception('Failed to record result data: %s', err)

    def _data_to_line_protocol(self, data, case, criteria):
        msg = {}
        point = {
            "measurement": case,
            "fields": utils.flatten_dict_key(data["data"]),
            "time": self._get_nano_timestamp(data),
            "tags": self._get_extended_tags(criteria),
        }
        msg["points"] = [point]
        msg["tags"] = self.tags

        return make_lines(msg).encode('utf-8')

    def _get_nano_timestamp(self, results):
        try:
            timestamp = results["timestamp"]
        except Exception:
            timestamp = time.time()

        return str(int(float(timestamp) * 1000000000))

    def _get_extended_tags(self, criteria):
        tags = {
            "task_id": self.task_id,
            "criteria": criteria
        }

        return tags
