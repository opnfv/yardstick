# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from yardstick.benchmark.scenarios import base


LOG = logging.getLogger(__name__)


class Dummy2(base.Scenario):
    """Execute Dummy (v2!) echo"""
    __scenario_type__ = "Dummy2"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        self.setup_done = True

    def run(self, result):
        if not self.setup_done:
            self.setup()

        result["hello"] = "yardstick"
        LOG.info("Dummy (v2!) echo hello yardstick!")
