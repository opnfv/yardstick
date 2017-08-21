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

from flask import request
from flask_restful import Resource

from yardstick import _init_logging
from yardstick.common import constants as consts
from yardstick.common import utils as common_utils

_init_logging()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


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

        args.update({k: v for k, v in request.form.items()})

        return action, args

    def _get_args(self):
        args = common_utils.translate_to_str(request.args)

        return args

    def _dispatch_post(self, **kwargs):
        action, args = self._post_args()
        args.update(kwargs)
        return self._dispatch(args, action)

    def _dispatch(self, args, action):
        try:
            return getattr(self, action)(args)
        except AttributeError:
            common_utils.result_handler(consts.API_ERROR, 'No such action')


class Url(object):

    def __init__(self, url, target):
        super(Url, self).__init__()
        self.url = url
        self.target = target

common_utils.import_modules_from_package("api.resources")
