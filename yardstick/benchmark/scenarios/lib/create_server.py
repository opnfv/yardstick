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


class CreateServer(base.OpenstackScenario):
    """Create an OpenStack server"""

    __scenario_type__ = "CreateServer"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        "openstack_paras": dict,
        "flavor_name": None,
        "image_name": None,
    }

    def _get_image_id(self):
        return self.glance_get_image_id(self.image_name)

    def _get_flavor_id(self):
        return self.nova_get_flavor_id(self.flavor_name)

    def _run(self, result):
        """execute the test"""

        if self.image_name is not None:
            self.openstack_paras['image'] = self._get_image_id()

        if self.flavor_name is not None:
            self.openstack_paras['flavor'] = self._get_flavor_id()

        vm = self.nova_create_instance_and_wait_for_active(self.openstack_paras)

        try:
            values = [vm.id]
        except AttributeError:
            result["instance_create"] = 0
            LOG.error("Create server failed!")
            return []
        else:
            result["instance_create"] = 1
            LOG.info("Create server successful!")
            return values
