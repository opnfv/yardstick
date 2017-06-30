##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import re
import importlib
import logging

from flask import request
from flask_restful import Resource

from api.utils import common as common_utils
from yardstick.common import constants as consts

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ApiResource(Resource):

    def _post_args(self):
        data = request.json if request.json else {}
        params = common_utils.translate_to_str(data)
        action = params.get('action', request.form.get('action', ''))
        args = params.get('args', {})

        try:
            args['file'] = request.files['file']
        except KeyError:
            pass

        logger.debug('Input args is: action: %s, args: %s', action, args)

        return action, args

    def _get_args(self):
        args = common_utils.translate_to_str(request.args)
        logger.debug('Input args is: args: %s', args)

        return args

    def _dispatch_post(self):
        action, args = self._post_args()
        return self._dispatch(args, action)

    def _dispatch_get(self, **kwargs):
        args = self._get_args()
        args.update(kwargs)
        return self._dispatch(args)

    def _dispatch(self, args, action='default'):
        module_name = re.sub(r'([A-Z][a-z]*)', r'_\1',
                             self.__class__.__name__)[1:].lower()

        module_name = 'api.resources.%s' % module_name
        resources = importlib.import_module(module_name)
        try:
            return getattr(resources, action)(args)
        except AttributeError:
            common_utils.result_handler(consts.API_ERROR, 'No such action')
