##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# ping scenario

from __future__ import print_function
from __future__ import absolute_import
import pkg_resources
import logging

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class KKLT(base.Scenario):
    """Execute ping between two hosts

  Parameters
    packetsize - number of data bytes to send
        type:    int
        unit:    bytes
        default: 56
    """

    __scenario_type__ = "Cjk"

    TARGET_SCRIPT = 'ping_benchmark.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking', KKLT.TARGET_SCRIPT)
        host = self.context_cfg['host']
        print(scenario_cfg)
        print(context_cfg)
        print(host)

    def run(self, result):
        pass
