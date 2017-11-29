##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest

from yardstick.benchmark.scenarios.lib.check_value import CheckValue


class CheckValueTestCase(unittest.TestCase):

    def test_check_value_eq(self):
        scenario_cfg = {'options': {'operator': 'eq', 'value1': 1, 'value2': 2}}
        obj = CheckValue(scenario_cfg, {})
        try:
            obj.run({})
        except Exception as e:
            self.assertIsInstance(e, AssertionError)

    def test_check_value_eq_pass(self):
        scenario_cfg = {'options': {'operator': 'eq', 'value1': 1, 'value2': 1}}
        obj = CheckValue(scenario_cfg, {})
        try:
            obj.run({})
        except Exception as e:
            self.assertIsInstance(e, AssertionError)

    def test_check_value_ne(self):
        scenario_cfg = {'options': {'operator': 'ne', 'value1': 1, 'value2': 1}}
        obj = CheckValue(scenario_cfg, {})
        try:
            obj.run({})
        except Exception as e:
            self.assertIsInstance(e, AssertionError)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
