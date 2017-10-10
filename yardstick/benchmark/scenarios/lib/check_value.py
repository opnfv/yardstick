##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import print_function
from __future__ import absolute_import

import logging

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class CheckValue(base.Scenario):
    """Check values between value1 and value2

    Parameters:
        operator: available operators are 'equal', 'not equal', 'less than' and 'larger than'
            type:       string
            unit:       N/A
            default:    N/A

        value1: input value1 for comparison
            type:       N/A
            unit:       N/A
            default:    N/A

        value2: input value2 for comparison
            type:       N/A
            unit:       N/A
            default:    N/A

        fluctuation: fluctuation rate for value1. only work with 'equal' operation now.
            type:       float
            unit:       N/A
            default:    0.0

    """

    __scenario_type__ = "CheckValue"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

    def run(self, result):
        """execute the test"""

        check_result = "PASS"

        LOG.debug("options=%s", self.options)
        op = self.options.get("operator")
        value1 = str(self.options.get("value1"))
        value2 = str(self.options.get("value2"))

        fluctuation = float(self.options.get("fluctuation", 0))
        if fluctuation != 0:
            value1_top = float(value2) * float(1 + fluctuation)
            value1_bottom = float(value2) * float(1 - fluctuation)

        try:
            if fluctuation != 0 and op == "equal" and not (value1_bottom <= float(value1) <=
                                                           value1_top):
                LOG.info("value1=%s, value2=%s, error: should fall within the range %s!!!",
                         value1, value2, fluctuation)
                check_result = "FAIL"
                assert (value1_bottom <= float(value1) <= value1_top), \
                    "Error %s!=%s in fluctuation range %s" % (value1, value2, fluctuation)
            elif fluctuation == 0 and op == "equal" and value1 != value2:
                LOG.info("value1=%s, value2=%s, error: should equal!!!", value1,
                         value2)
                check_result = "FAIL"
                assert value1 == value2, "Error %s!=%s" % (value1, value2)
            elif op == "larger than" and float(value1) < float(value2):
                LOG.info("value1=%s, value2=%s, error: should larger than!!!", value1,
                         value2)
                check_result = "FAIL"
                assert value1 > value2, "Error %s<=%s" % (value1, value2)
            elif op == "less than" and float(value1) > float(value2):
                LOG.info("value1=%s, value2=%s, error: should less than!!!", value1,
                         value2)
                check_result = "FAIL"
                assert value1 < value2, "Error %s>=%s" % (value1, value2)
            elif op == "not equal" and value1 == value2:
                LOG.info("value1=%s, value2=%s, error: should not equal!!!",
                         value1, value2)
                check_result = "FAIL"
                assert value1 != value2, "Error %s==%s" % (value1, value2)
        except AssertionError:
            LOG.info("Check result is %s", check_result)
            result.update({'check_result': check_result})
        else:
            LOG.info("Check result is %s", check_result)
            result.update({'check_result': check_result})
