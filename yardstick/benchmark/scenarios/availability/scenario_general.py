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
        self.intermediate_variables = {}

    def setup(self):
        self.director = Director(self.scenario_cfg, self.context_cfg)

    def run(self, result):
        steps = self.scenario_cfg["options"]["steps"]
        orderedSteps = sorted(steps, key=lambda x: x['index'])
        for step in orderedSteps:
            LOG.debug(
                "\033[94m running step: %s .... \033[0m",
                orderedSteps.index(step) + 1)
            try:
                actionPlayer = self.director.createActionPlayer(
                    step['actionType'], step['actionKey'],
                    self.intermediate_variables)
                actionPlayer.action()
                actionRollbacker = self.director.createActionRollbacker(
                    step['actionType'], step['actionKey'])
                if actionRollbacker:
                    self.director.executionSteps.append(actionRollbacker)
            except Exception:  # pylint: disable=broad-except
                LOG.exception("Exception")
                LOG.debug(
                    "\033[91m exception when running step: %s .... \033[0m",
                    orderedSteps.index(step))
                break
            finally:
                pass

        self.director.stopMonitors()

        verify_result = self.director.verify()
        for k, v in self.director.data.items():
            if v == 0:
                result['sla_pass'] = 0
                verify_result = False
                LOG.info("\033[92m The service process (%s) not found in the host environment", k)

        result['sla_pass'] = 1 if verify_result else 0
        self.director.store_result(result)

        assert verify_result is True, "The HA test case NOT passed"

    def teardown(self):
        self.director.knockoff()
