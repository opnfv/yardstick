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


class CreateImage(base.OpenstackScenario):
    """Create an OpenStack image"""

    __scenario_type__ = "CreateImage"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        'image_name': 'TestImage',
        'file_path': None,
        'disk_format': 'qcow2',
        'container_format': 'bare',
        'min_disk': 0,
        'max_ram': 0,
        'protected': False,
        'public': 'public',
    }

    def __init__(self, scenario_cfg, context_cfg):
        super(CreateImage, self).__init__(scenario_cfg, context_cfg)

        self.kwargs = self.options.get("property", {})
        self.kwargs['tags'] = self.options.get("tags", [])
        self.kwargs.update({key: getattr(self, key) for key in self.DEFAULT_OPTIONS})

    def _run(self, result):
        """execute the test"""

        image_id = self.glance_create_image(**self.kwargs)

        if image_id:
            LOG.info("Create image successful!")
            values = [image_id]

        else:
            LOG.info("Create image failed!")
            values = []

        return values
