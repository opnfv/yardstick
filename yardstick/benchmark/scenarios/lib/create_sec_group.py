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


class CreateSecgroup(base.Scenario):
    """Create an OpenStack security group"""

    __scenario_type__ = "CreateSecgroup"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.sg_name = self.options.get("sg_name", "yardstick_sec_group")
        self.description = self.options.get("description", None)
        self.neutron_client = op_utils.get_neutron_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        sg_id = op_utils.create_security_group_full(self.neutron_client,
                                                    sg_name=self.sg_name,
                                                    sg_description=self.description)

        if sg_id:
            result.update({"sg_create": 1})
            LOG.info("Create security group successful!")
        else:
            result.update({"sg_create": 0})
            LOG.error("Create security group failed!")

        try:
            keys = self.scenario_cfg.get('output', '').split()
        except KeyError:
            pass
        else:
            values = [sg_id]
            return self._push_to_outputs(keys, values)
