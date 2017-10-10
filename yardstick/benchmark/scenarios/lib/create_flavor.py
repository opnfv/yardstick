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


class CreateFlavor(base.Scenario):
    """Create an OpenStack flavor

    Parameters
        flavor_name - name of the flavor to be created
            type:    string
            unit:    N/A
            default: 'test-flavor'
        ram - memory size in MB
            type:    int
            unit:    MB
            default: 1024
        vcpus - the number of vcpus
            type:    int
            unit:    N/A
            default: 2
        disk - disk space in GB
            type:    int
            unit:    GB
            default: 100
        openstack_params - additional openstack parameters
            type:    dict
            unit:    N/A
            default: null

    Outputs:
        flavor_id - id of the created flavor
            type:    string
            unit:    N/A
    """

    __scenario_type__ = "CreateFlavor"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.flavor_name = self.options.get("flavor_name", "test-flavor")
        self.ram = self.options.get("ram", 1024)
        self.vcpus = self.options.get("vcpus", 2)
        self.disk = self.options.get("disk", 100)
        self.openstack_params = self.options.get("openstack_params", {})

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        LOG.info("Creating flavor %s with %s vcpus, %sMB ram and %sGB disk",
                 self.flavor_name, self.vcpus, self.ram, self.disk)
        flavor = op_utils.create_flavor(self.flavor_name, self.ram, self.vcpus, self.disk,
                                        **self.openstack_params)

        if flavor:
            LOG.info("Create flavor successful!")
            values = [flavor.id]
        else:
            LOG.info("Create flavor failed!")
            values = []

        try:
            keys = self.scenario_cfg.get('output', '').split()
        except KeyError:
            pass
        else:
            return self._push_to_outputs(keys, values)
