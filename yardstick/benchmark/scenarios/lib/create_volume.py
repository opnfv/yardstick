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

import time
import logging
from itertools import takewhile

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class CreateVolume(base.OpenstackScenario):
    """Create an OpenStack volume"""

    __scenario_type__ = "CreateVolume"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        "image": None,
        "size": 100,
        "volume_name": "TestVolume",
    }

    @staticmethod
    def _status_predicate(status):
        return status in ['creating', 'downloading']

    def _get_status(self):
        volume = self.cinder_get_volume_by_name(self.volume_name)
        return volume.status

    def _run(self, result):
        """execute the test"""

        image_id = None
        if self.image:
            image_id = self.glance_get_image_id(self.glance_client, self.image)

        volume = self.cinder_create_volume(self.volume_name, self.size, image_id)

        for status in takewhile(self._status_predicate, iter(self._get_status, object())):
            LOG.info("Volume status is: %s" % status)
            time.sleep(5)

        LOG.info("Create volume successful!")
        return [volume.id]
