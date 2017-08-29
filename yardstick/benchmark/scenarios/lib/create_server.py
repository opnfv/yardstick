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


class CreateServer(base.Scenario):
    """Create an OpenStack server"""

    __scenario_type__ = "CreateServer"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.image_name = self.options.get("image_name", None)
        self.flavor_name = self.options.get("flavor_name", None)
        self.openstack = self.options.get("openstack_paras", None)

        self.glance_client = op_utils.get_glance_client()
        self.neutron_client = op_utils.get_neutron_client()
        self.nova_client = op_utils.get_nova_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        if self.image_name is not None:
            self.openstack['image'] = op_utils.get_image_id(self.glance_client,
                                                            self.image_name)
        if self.flavor_name is not None:
            self.openstack['flavor'] = op_utils.get_flavor_id(self.nova_client,
                                                              self.flavor_name)

        vm = op_utils.create_instance_and_wait_for_active(self.openstack)

        if vm:
            result.update({"instance_create": 1})
            LOG.info("Create server successful!")
        else:
            result.update({"instance_create": 0})
            LOG.error("Create server failed!")

        try:
            keys = self.scenario_cfg.get('output', '').split()
        except KeyError:
            pass
        else:
            values = [vm.id]
            return self._push_to_outputs(keys, values)
