##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import collections
import logging

from flask import jsonify

from api.utils.daemonthread import DaemonThread
from yardstick.cmd.cli import YardstickCLI

logger = logging.getLogger(__name__)


def translate_to_str(object):
    if isinstance(object, collections.Mapping):
        return {str(k): translate_to_str(v) for k, v in object.items()}
    elif isinstance(object, list):
        return [translate_to_str(ele) for ele in object]
    elif isinstance(object, unicode):
        return str(object)
    return object


def get_command_list(command_list, opts, args):

    command_list.append(args)

    command_list.extend(('--{}'.format(k) for k in opts if 'task-args' != k))

    task_args = opts.get('task-args', '')
    if task_args:
        command_list.extend(['--task-args', str(task_args)])

    return command_list


def exec_command_task(command_list, task_dict):   # pragma: no cover
    daemonthread = DaemonThread(YardstickCLI().api, (command_list, task_dict))
    daemonthread.start()


def error_handler(message):
    logger.debug(message)
    result = {
        'status': 'error',
        'message': message
    }
    return jsonify(result)


def result_handler(status, data):
    result = {
        'status': status,
        'result': data
    }
    return jsonify(result)


class Url(object):

    def __init__(self, url, resource, endpoint):
        super(Url, self).__init__()
        self.url = url
        self.resource = resource
        self.endpoint = endpoint
