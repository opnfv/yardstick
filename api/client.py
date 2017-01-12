##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import requests

from oslo_serialization import jsonutils

from yardstick.common import constants as consts

logger = logging.getLogger(__name__)


def post(url, data={}):
    url = '{}{}'.format(consts.BASE_URL, url)
    data = jsonutils.dumps(data)
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=data, headers=headers)
        result = response.json()
        logger.debug('The result is: %s', result)

        return result
    except Exception as e:
        logger.exception('Failed: %s', e)
        raise


def get(url):
    url = '{}{}'.format(consts.BASE_URL, url)
    response = requests.get(url)
    return response.json()
