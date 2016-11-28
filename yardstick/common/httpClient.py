##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import json
import logging

import requests

logger = logging.getLogger(__name__)


class HttpClient(object):

    def post(self, url, data):
        data = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(url, data=data, headers=headers)
            result = response.json()
            logger.debug('The result is: %s', result)
        except Exception as e:
            logger.debug('Failed: %s', e)
