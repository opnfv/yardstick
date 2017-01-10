##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import uuid
import os
import logging

from api import conf
from api.utils import common as common_utils

logger = logging.getLogger(__name__)


def runTestCase(args):
    try:
        opts = args.get('opts', {})
        testcase = args['testcase']
    except KeyError:
        return common_utils.error_handler('Lack of testcase argument')

    testcase_name = conf.TEST_CASE_PRE + testcase
    testcase = os.path.join(conf.TEST_CASE_PATH, testcase_name + '.yaml')

    task_id = str(uuid.uuid4())

    command_list = ['task', 'start']
    command_list = common_utils.get_command_list(command_list, opts, testcase)
    logger.debug('The command_list is: %s', command_list)

    logger.debug('Start to execute command list')
    task_dict = {
        'task_id': task_id,
        'details': testcase_name
    }
    common_utils.exec_command_task(command_list, task_dict)

    return common_utils.result_handler('success', task_id)
