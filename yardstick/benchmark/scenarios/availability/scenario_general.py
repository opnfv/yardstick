##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import logging

from yardstick.benchmark.scenarios import base
from yardstick.benchmark.scenarios.availability.director import Director

LOG = logging.getLogger(__name__)


class ScenarioGeneral(base.Scenario):
    """Support orchestrating general HA test scenarios."""

    __scenario_type__ = "GeneralHA"

    def __init__(self, scenario_cfg, context_cfg):
        LOG.debug(
            "scenario_cfg:%s context_cfg:%s", scenario_cfg, context_cfg)
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg

    def setup(self):
        self.director = Director(self.scenario_cfg, self.context_cfg)

    def run(self, args):
        steps = self.scenario_cfg["options"]["steps"]
        orderedSteps = sorted(steps, key=lambda x: x['index'])
        for step in orderedSteps:
            LOG.debug(
                "\033[94m running step: %s .... \033[0m",
                orderedSteps.index(step) + 1)
            try:
                actionPlayer = self.director.createActionPlayer(
                    step['actionType'], step['actionKey'])
                actionPlayer.action()
                actionRollbacker = self.director.createActionRollbacker(
                    step['actionType'], step['actionKey'])
                if actionRollbacker:
                    self.director.executionSteps.append(actionRollbacker)
            except Exception:
                LOG.exception("Exception")
                LOG.debug(
                    "\033[91m exception when running step: %s .... \033[0m",
                    orderedSteps.index(step))
                break
            finally:
                pass

        self.director.stopMonitors()
        if self.director.verify():
            LOG.debug(
                "\033[92m congratulations, "
                "the test cases scenario is pass! \033[0m")
        else:
            LOG.debug(
                "\033[91m aoh,the test cases scenario failed,"
                "please check the detail debug information! \033[0m")

    def teardown(self):
        self.director.knockoff()
