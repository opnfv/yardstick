##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################


class ActionType:
    ATTACKER = "attacker"
    MONITOR = "monitor"
    RESULTCHECKER = "resultchecker"
    OPERATION = "operation"


class Condition:
    EQUAL = "eq"
    GREATERTHAN = "gt"
    GREATERTHANEQUAL = "gt_eq"
    LESSTHAN = "lt"
    LESSTHANEQUAL = "lt_eq"
    IN = "in"
