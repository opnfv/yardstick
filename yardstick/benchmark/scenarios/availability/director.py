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

from yardstick.benchmark.scenarios.availability.monitor import basemonitor
from yardstick.benchmark.scenarios.availability.attacker import baseattacker
from yardstick.benchmark.scenarios.availability.operation import baseoperation
from yardstick.benchmark.scenarios.availability.result_checker \
    import baseresultchecker
from yardstick.benchmark.scenarios.availability import ActionType
from yardstick.benchmark.scenarios.availability import actionplayers
from yardstick.benchmark.scenarios.availability import actionrollbackers

LOG = logging.getLogger(__name__)


class Director(object):
    """
    Director is used to direct a test scenaio
    including the creation of action players, test result verification
    and rollback of actions.
    """

    def __init__(self, scenario_cfg, context_cfg):

        # A stack store Rollbacker that will be called after
        # all actionplayers finish.
        self.executionSteps = []
        self.data = {}

        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        nodes = self.context_cfg.get("nodes", None)
        # setup attackers
        if "attackers" in self.scenario_cfg["options"]:
            LOG.debug("start init attackers...")
            attacker_cfgs = self.scenario_cfg["options"]["attackers"]
            self.attackerMgr = baseattacker.AttackerMgr()
            self.data = self.attackerMgr.init_attackers(attacker_cfgs,
                                                        nodes)

        # setup monitors
        if "monitors" in self.scenario_cfg["options"]:
            LOG.debug("start init monitors...")
            monitor_cfgs = self.scenario_cfg["options"]["monitors"]
            self.monitorMgr = basemonitor.MonitorMgr(self.data)
            self.monitorMgr.init_monitors(monitor_cfgs, nodes)
        # setup operations
        if "operations" in self.scenario_cfg["options"]:
            LOG.debug("start init operations...")
            operation_cfgs = self.scenario_cfg["options"]["operations"]
            self.operationMgr = baseoperation.OperationMgr()
            self.operationMgr.init_operations(operation_cfgs, nodes)
        # setup result checker
        if "resultCheckers" in self.scenario_cfg["options"]:
            LOG.debug("start init resultCheckers...")
            result_check_cfgs = self.scenario_cfg["options"]["resultCheckers"]
            self.resultCheckerMgr = baseresultchecker.ResultCheckerMgr()
            self.resultCheckerMgr.init_ResultChecker(result_check_cfgs, nodes)

    def createActionPlayer(self, type, key, intermediate_variables=None):
        if intermediate_variables is None:
            intermediate_variables = {}
        LOG.debug(
            "the type of current action is %s, the key is %s", type, key)
        if type == ActionType.ATTACKER:
            return actionplayers.AttackerPlayer(self.attackerMgr[key])
        if type == ActionType.MONITOR:
            return actionplayers.MonitorPlayer(self.monitorMgr[key])
        if type == ActionType.RESULTCHECKER:
            return actionplayers.ResultCheckerPlayer(
                self.resultCheckerMgr[key])
        if type == ActionType.OPERATION:
            return actionplayers.OperationPlayer(self.operationMgr[key],
                                                 intermediate_variables)
        LOG.debug("something run when creatactionplayer")

    def createActionRollbacker(self, type, key):
        LOG.debug(
            "the type of current action is %s, the key is %s", type, key)
        if type == ActionType.ATTACKER:
            return actionrollbackers.AttackerRollbacker(self.attackerMgr[key])
        if type == ActionType.OPERATION:
            return actionrollbackers.OperationRollbacker(
                self.operationMgr[key])
        LOG.debug("no rollbacker created for %s", key)

    def verify(self):
        result = True
        if hasattr(self, 'monitorMgr'):
            result &= self.monitorMgr.verify_SLA()
        if hasattr(self, 'resultCheckerMgr'):
            result &= self.resultCheckerMgr.verify()
        if result:
            LOG.debug("monitors are passed")
        return result

    def stopMonitors(self):
        if "monitors" in self.scenario_cfg["options"]:
            self.monitorMgr.wait_monitors()

    def knockoff(self):
        LOG.debug("knock off ....")
        while self.executionSteps:
            singleStep = self.executionSteps.pop()
            singleStep.rollback()
