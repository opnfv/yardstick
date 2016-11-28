##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging

from flask import request
from flask_restful import Resource

from api.utils import common as common_utils
from api.actions import test as test_action
from api.actions import result as result_action
from api.actions import env as env_action

logger = logging.getLogger(__name__)


class Test(Resource):
    def post(self):
        action = common_utils.translate_to_str(request.json.get('action', ''))
        args = common_utils.translate_to_str(request.json.get('args', {}))
        logger.debug('Input args is: action: %s, args: %s', action, args)

        try:
            return getattr(test_action, action)(args)
        except AttributeError:
            return common_utils.error_handler('Wrong action')


class Result(Resource):
    def get(self):
        args = common_utils.translate_to_str(request.args)
        action = args.get('action', '')
        logger.debug('Input args is: action: %s, args: %s', action, args)

        try:
            return getattr(result_action, action)(args)
        except AttributeError:
            return common_utils.error_handler('Wrong action')


class Env(Resource):
    def post(self):
        action = common_utils.translate_to_str(request.json.get('action', ''))
        args = common_utils.translate_to_str(request.json.get('args', {}))
        logger.debug('Input args is: action: %s, args: %s', action, args)

        try:
            return getattr(env_action, action)(args)
        except AttributeError:
            return common_utils.error_handler('Wrong action')
