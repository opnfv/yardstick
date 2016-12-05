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

from oslo_serialization import jsonutils
import requests

logger = logging.getLogger(__name__)


class HttpClient(object):

    def post(self, url, data):
        data = jsonutils.dump_as_bytes(data)
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(url, data=data, headers=headers)
            result = response.json()
            logger.debug('The result is: %s', result)

            return result
        except Exception as e:
            logger.debug('Failed: %s', e)
            raise

    def get(self, url):
        response = requests.get(url)
        return response.json()
