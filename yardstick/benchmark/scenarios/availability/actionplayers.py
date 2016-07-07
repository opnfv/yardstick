##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################


class ActionPlayers(object):

    def action(self):
        pass


class AttackerPlayer(ActionPlayers):

    def __init__(self, attacker):
        self.underlyingAttacker = attacker

    def action(self):
        self.underlyingAttacker.inject_fault()


class OperationPlayer(ActionPlayers):

    def __init__(self, operation):
        self.underlyingOperation = operation

    def action(self):
        self.underlyingOperation.run()


class MonitorPlayer(ActionPlayers):

    def __init__(self, monitor):
        self.underlyingmonitor = monitor

    def action(self):
        self.underlyingmonitor.start_monitor()


class ResultCheckerPlayer(ActionPlayers):

    def __init__(self, resultChecker):
        self.underlyingresultChecker = resultChecker

    def action(self):
        self.underlyingresultChecker.verify()
