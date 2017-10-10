##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import print_function
from __future__ import absolute_import

import logging

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class GetServerIp(base.Scenario):
    """Get a server by name"""

    __scenario_type__ = "GetServerIp"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        'ip_type': "floating",
    }

    def _run(self, result):
        ip_type = self.ip_type
        for address_list in self.server['addresses'].values():
            for address_data in address_list:
                if address_data['OS-EXT-IPS:type'] == ip_type:
                    return [address_data['addr']]
