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

LOG = logging.getLogger(__name__)


class ActionRollbacker(object):
    """
    Abstract the rollback functions of attacker, operation
    and mybe others in future
    """

    def rollback(self):
        pass


class AttackerRollbacker(ActionRollbacker):

    def __init__(self, attacker):
        self.underlyingAttacker = attacker

    def rollback(self):
        LOG.debug(
            "\033[93m recovering attacker %s \033[0m",
            self.underlyingAttacker.key)
        self.underlyingAttacker.recover()


class OperationRollbacker(ActionRollbacker):

    def __init__(self, operation):
        self.underlyingOperation = operation

    def rollback(self):
        LOG.debug(
            "\033[93m rollback operation %s \033[0m",
            self.underlyingOperation.key)
        self.underlyingOperation.rollback()
