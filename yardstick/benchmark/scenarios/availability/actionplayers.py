##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################


class ActionPlayer(object):
    """
    Abstract the action functions of attacker,
    monitor, operation, resultchecker and mybe others in future
    """

    def action(self):
        pass


class AttackerPlayer(ActionPlayer):

    def __init__(self, attacker):
        self.underlyingAttacker = attacker

    def action(self):
        self.underlyingAttacker.inject_fault()


class OperationPlayer(ActionPlayer):

    def __init__(self, operation, intermediate_variables):
        self.underlyingOperation = operation
        self.underlyingOperation.intermediate_variables \
            = intermediate_variables

    def action(self):
        self.underlyingOperation.run()


class MonitorPlayer(ActionPlayer):

    def __init__(self, monitor):
        self.underlyingmonitor = monitor

    def action(self):
        self.underlyingmonitor.start_monitor()


class ResultCheckerPlayer(ActionPlayer):

    def __init__(self, resultChecker):
        self.underlyingresultChecker = resultChecker

    def action(self):
        self.underlyingresultChecker.verify()
