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
from requests import ConnectionError

from yardstick.common import utils
from third_party.influxdb.influxdb_line_protocol import make_lines
from yardstick.dispatcher.base import Base as DispatchBase

LOG = logging.getLogger(__name__)


class InfluxdbDispatcher(DispatchBase):
    """Dispatcher class for posting data into an influxdb target.
    """

    __dispatcher_type__ = "Influxdb"

    def __init__(self, task_id, conf):
        self.conf = conf.influxdb
        super(InfluxdbDispatcher, self).__init__(task_id)

    def setup(self):
        pass

    def teardown(self):
        pass

    def push(self, case, data):
        self._add_to_result(case, data)

        self._upload_one_record(case, data)

    def flush(self):
        self._complete_result()

    def _upload_one_record(self, case, data, tc_criteria="PASS"):

        line = self._data_to_line_protocol(case, data, tc_criteria)
        LOG.debug('Test result line format : %s', line)

        url = "{}/write?db={}".format(self.conf.target, self.conf.db_name)
        try:
            res = requests.post(url,
                                data=line,
                                auth=(self.conf.username, self.conf.password),
                                timeout=int(self.conf.timeout))
        except ConnectionError as err:
            LOG.exception('Failed to record result data: %s', err)
        else:
            if res.status_code != 204:
                LOG.error('Test result posting finished with status code'
                          ' %d.', res.status_code)
                LOG.error(res.text)

    def _data_to_line_protocol(self, case, data, criteria="PASS"):
        msg = {}

        point = {
            "measurement": case,
            "fields": utils.flatten_dict_key(data["data"]),
            "time": self._get_nano_timestamp(data),
            "tags": self._get_extended_tags(criteria),
        }
        msg["points"] = [point]
        msg["tags"] = self.result['result']['info']

        return make_lines(msg).encode('utf-8')

    def _get_nano_timestamp(self, results):
        try:
            timestamp = results["timestamp"]
        except KeyError:
            timestamp = time.time()

        return str(int(float(timestamp) * 1000000000))

    def _get_extended_tags(self, criteria):
        tags = {
            "task_id": self.task_id,
            "criteria": criteria
        }

        return tags
