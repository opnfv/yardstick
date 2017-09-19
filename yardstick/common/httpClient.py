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
import time

from oslo_serialization import jsonutils
import requests

logger = logging.getLogger(__name__)


class HttpClient(object):

    def post(self, url, data, timeout=0):
        data = jsonutils.dump_as_bytes(data)
        headers = {'Content-Type': 'application/json'}
        t_end = time.time() + timeout
        while True:
            try:
                response = requests.post(url, data=data, headers=headers)
                result = response.json()
                logger.debug('The result is: %s', result)
                return result
            except Exception:
                if time.time() > t_end:
                    logger.exception('')
                    raise
            time.sleep(1)

    def get(self, url):
        response = requests.get(url)
        return response.json()
