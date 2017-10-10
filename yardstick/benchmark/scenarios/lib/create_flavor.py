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


class CreateFlavor(base.OpenstackScenario):
    """Create an OpenStack flavor"""

    __scenario_type__ = "CreateFlavor"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        'flavor_name': 'TestFlavor',
        'vcpus': 2,
        'ram': 1024,
        'disk': 100,
        'is_public': True,
    }

    def _run(self, result):
        """execute the test"""

        args = self.flavor_name, self.vcpus, self.ram, self.disk

        LOG.info("Creating flavor %s with %s vcpus, %sMB ram and %sGB disk", *args)
        flavor = self.nova_create_flavor(*args, is_public=self.is_public)

        try:
            values = [flavor.id]
        except AttributeError:
            LOG.info("Create flavor failed!")
            return []
        else:
            LOG.info("Create flavor successful!")
            return values
