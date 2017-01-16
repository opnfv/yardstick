##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import logging

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Dummy(base.Scenario):
    """Execute Dummy echo
    """
    __scenario_type__ = "Dummy"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""
        if not self.setup_done:
            self.setup()

        result["hello"] = "yardstick"
        LOG.info("Dummy echo hello yardstick!")
