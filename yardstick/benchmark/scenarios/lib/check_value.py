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
import operator

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class CheckValue(base.Scenario):
    """Check values between value1 and value2

    options:
        operator: equal(eq) and not equal(ne)
        value1:
        value2:
    output: check_result
    """

    __scenario_type__ = "CheckValue"
    LOGGER = LOG

    def _run(self, result):
        """execute the test"""

        operator_name = self.operator
        operator_func = getattr(operator, operator_name)
        LOG.debug("options=%s", self.options)

        message = "Error {} not {} {}".format(self.value1, operator_name, self.value2)
        try:
            assert operator_func and operator_func(self.value1, self.value2), message
        except AssertionError:
            LOG.info(message)
            raise

        LOG.info("Check result is PASS")
        return ['PASS']
