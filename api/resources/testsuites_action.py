##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

"""Yardstick test suite api action"""

from __future__ import absolute_import
import uuid
import os
import logging
import yaml

from api.utils import common as common_utils
from yardstick.common import constants as consts
from yardstick.common.task_template import TaskTemplate

logger = logging.getLogger(__name__)


def runTestSuite(args):
    try:
        opts = args.get('opts', {})
        testsuite = args['testsuite']
    except KeyError:
        return common_utils.error_handler('Lack of testsuite argument')

    if 'suite' not in opts:
        opts['suite'] = 'true'

    testsuite = os.path.join(consts.TESTSUITE_DIR, '{}.yaml'.format(testsuite))

    task_id = str(uuid.uuid4())

    command_list = ['task', 'start']
    command_list = common_utils.get_command_list(command_list, opts, testsuite)
    logger.debug('The command_list is: %s', command_list)

    logger.debug('Start to execute command list')
    task_dic = {
        'task_id': task_id,
        'details': _get_cases_from_suite_file(testsuite)
    }
    common_utils.exec_command_task(command_list, task_dic)

    return common_utils.result_handler('success', task_id)


def _get_cases_from_suite_file(testsuite):
    def get_name(full_name):
        return os.path.splitext(full_name)[0]

    with open(testsuite) as f:
        contents = TaskTemplate.render(f.read())

    suite_dic = yaml.safe_load(contents)
    testcases = [get_name(c['file_name']) for c in suite_dic['test_cases']]
    return ','.join(testcases)
