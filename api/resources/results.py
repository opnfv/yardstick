##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import logging
import uuid

from api.utils import influx as influx_utils
from api.utils import common as common_utils
from api.database.handlers import TasksHandler

logger = logging.getLogger(__name__)


def default(args):
    return getResult(args)


def getResult(args):
    try:
        task_id = args['task_id']

        uuid.UUID(task_id)
    except KeyError:
        message = 'task_id must be provided'
        return common_utils.result_handler(2, message)

    task = TasksHandler().get_task_by_taskid(task_id)

    def _unfinished():
        return common_utils.result_handler(0, {})

    def _finished():
        testcases = task.details.split(',')

        def get_data(testcase):
            query_template = "select * from %s where task_id='%s'"
            query_sql = query_template % (testcase, task_id)
            data = common_utils.translate_to_str(influx_utils.query(query_sql))
            return data

        result = _format_data({k: get_data(k) for k in testcases})

        return common_utils.result_handler(1, result)

    def _error():
        return common_utils.result_handler(2, task.error)

    try:
        status = task.status

        switcher = {
            0: _unfinished,
            1: _finished,
            2: _error
        }
        return switcher.get(status, lambda: 'nothing')()
    except IndexError:
        return common_utils.result_handler(2, 'no such task')


def _format_data(data):
    try:
        first_value = data.values()[0][0]
    except IndexError:
        return {'criteria': 'FAIL', 'testcases': {}}
    else:
        info = {
            'deploy_scenario': first_value.get('deploy_scenario'),
            'installer': first_value.get('installer'),
            'pod_name': first_value.get('pod_name'),
            'version': first_value.get('version')
        }
        task_id = first_value.get('task_id')
        criteria = first_value.get('criteria')
        testcases = {k: _get_case_data(v) for k, v in data.items()}

        result = {
            'criteria': criteria,
            'info': info,
            'task_id': task_id,
            'testcases': testcases
        }
        return result


def _get_case_data(data):
    try:
        scenario = data[0]
    except IndexError:
        return {'tc_data': [], 'criteria': 'FAIL'}
    else:
        tc_data = [_get_scenario_data(s) for s in data]
        criteria = scenario.get('criteria')
        return {'tc_data': tc_data, 'criteria': criteria}


def _get_scenario_data(data):
    result = {
        'data': {},
        'timestamp': ''
    }

    blacklist = {'criteria', 'deploy_scenario', 'host', 'installer',
                 'pod_name', 'runner_id', 'scenarios', 'target',
                 'task_id', 'time', 'version'}

    keys = set(data.keys()) - set(blacklist)
    for k in keys:
        result['data'][k] = data[k]

    result['timestamp'] = data.get('time')

    return result
