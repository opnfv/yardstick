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


class DeleteImage(base.OpenstackScenario):
    """Delete an OpenStack image"""

    __scenario_type__ = "DeleteImage"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        "image_name": "TestImage",
    }

    def _run(self, result):
        """execute the test"""

        image_id = self.glance_get_image_id(self.image_name)
        LOG.info("Deleting image: %s", self.image_name)
        status = self.glance_delete_image(image_id)

        if status:
            LOG.info("Delete image successful!")
            return [status]
        else:
            LOG.info("Delete image failed!")
            return []
