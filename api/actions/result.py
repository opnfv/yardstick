##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging

from api.utils import influx as influx_utils
from api.utils import common as common_utils
from api import conf

logger = logging.getLogger(__name__)


def getResult(args):
    try:
        measurement = args['measurement']
        task_id = args['task_id']
    except KeyError:
        message = 'measurement and task_id must be needed'
        return common_utils.error_handler(message)

    measurement = conf.TEST_CASE_PRE + measurement

    query_template = "select * from %s where task_id='%s'"
    query_sql = query_template % ('tasklist', task_id)
    data = common_utils.translate_to_str(influx_utils.query(query_sql))

    def _unfinished():
        return common_utils.result_handler(0, [])

    def _finished():
        query_sql = query_template % (measurement, task_id)
        data = common_utils.translate_to_str(influx_utils.query(query_sql))

        return common_utils.result_handler(1, data)

    def _error():
        return common_utils.result_handler(2, data[0]['error'])

    try:
        status = data[0]['status']

        switcher = {
            0: _unfinished,
            1: _finished,
            2: _error
        }
        return switcher.get(status, lambda: 'nothing')()
    except IndexError:
        return common_utils.error_handler('no such task')
