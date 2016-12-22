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

from api import conf
from api.utils import common as common_utils

logger = logging.getLogger(__name__)


def runTestSuite(args):
    try:
        opts = args.get('opts', {})
        testsuite = args['testsuite']
    except KeyError:
        return common_utils.error_handler('Lack of testsuite argument')

    if 'suite' not in opts.keys():
        opts['suite'] = 'true'

    testsuite = os.path.join(conf.TEST_SUITE_PATH,
                             conf.TEST_SUITE_PRE + testsuite + '.yaml')

    task_id = str(uuid.uuid4())

    command_list = ['task', 'start']
    command_list = common_utils.get_command_list(command_list, opts, testsuite)
    logger.debug('The command_list is: %s', command_list)

    logger.debug('Start to execute command list')
    common_utils.exec_command_task(command_list, task_id)

    return common_utils.result_handler('success', task_id)
