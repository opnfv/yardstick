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
import yardstick.common.openstack_utils as op_utils

LOG = logging.getLogger(__name__)


class CreateImage(base.Scenario):
    """Create an OpenStack image

    Parameters
        image_name - name of the image to be created
            type:    string
            unit:    N/A
            default: 'test-image'
        file_path - path to the image file
            type:    string
            unit:    N/A
            default: null
        openstack_params - additional openstack parameters
            type:    dict
            unit:    N/A
            default: null

    Outputs:
        image_id - id of the created image
            type:    string
            unit:    N/A
    """

    __scenario_type__ = "CreateImage"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.image_name = self.options.get("image_name", "test-image")
        self.file_path = self.options.get("file_path")
        self.openstack_params = self.options.get("openstack_params", {})

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        image_id = op_utils.create_image(self.image_name, self.file_path, **self.openstack_params)

        if image_id:
            LOG.info("Create image successful!")
            values = [image_id]

        else:
            LOG.info("Create image failed!")
            values = []

        try:
            keys = self.scenario_cfg.get('output', '').split()
        except KeyError:
            pass
        else:
            return self._push_to_outputs(keys, values)
