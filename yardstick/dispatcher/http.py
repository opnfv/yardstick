##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import json
import logging

import requests

from yardstick.dispatcher.base import Base as DispatchBase

LOG = logging.getLogger(__name__)


class HttpDispatcher(DispatchBase):
    """Dispatcher class for posting data into a http target.
    """

    __dispatcher_type__ = "Http"

    # TODO: make parameters below configurable, currently just hard coded
    # The target where the http request will be sent.
    target = "http://127.0.0.1:8000/results"
    # The max time in seconds to wait for a request to timeout.
    timeout = 5

    def __init__(self, conf):
        super(HttpDispatcher, self).__init__(conf)
        self.headers = {'Content-type': 'application/json'}
        self.timeout = self.timeout
        self.target = self.target

    def record_result_data(self, data):
        if self.target == '':
            # if the target was not set, do not do anything
            LOG.error('Dispatcher target was not set, no data will'
                      'be posted.')
            return

        # We may have receive only one counter on the wire
        if not isinstance(data, list):
            data = [data]

        for result in data:
            try:
                LOG.debug('Message : %s' % result)
                res = requests.post(self.target,
                                    data=json.dumps(result),
                                    headers=self.headers,
                                    timeout=self.timeout)
                LOG.debug('Message posting finished with status code'
                          '%d.' % res.status_code)
            except Exception as err:
                LOG.exception('Failed to record result data: %s',
                              err)
