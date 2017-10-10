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

    def test_check_value_equal(self):
        scenario_cfg = {'options': {'operator': 'equal', 'value1': 1, 'value2': 2}}
        obj = CheckValue(scenario_cfg, {})
        try:
            obj.run({})
        except Exception as e:
            self.assertIsInstance(e, AssertionError)

    def test_check_value_equal_fluctuation(self):
        scenario_cfg = {'options': {'operator': 'equal', 'value1': 1, 'value2': 1, 'fluctuation': 0.1}}
        obj = CheckValue(scenario_cfg, {})
        try:
            obj.run({})
        except Exception as e:
            self.assertIsInstance(e, AssertionError)

    def test_check_value_equal_pass(self):
        scenario_cfg = {'options': {'operator': 'equal', 'value1': 1, 'value2': 1}}
        obj = CheckValue(scenario_cfg, {})
        try:
            obj.run({})
        except Exception as e:
            self.assertIsInstance(e, AssertionError)

    def test_check_value_less_than(self):
        scenario_cfg = {'options': {'operator': 'less than', 'value1': 2, 'value2': 1}}
        obj = CheckValue(scenario_cfg, {})
        try:
            obj.run({})
        except Exception as e:
            self.assertIsInstance(e, AssertionError)

    def test_check_value_larger_than(self):
        scenario_cfg = {'options': {'operator': 'larger than', 'value1': 1, 'value2': 2}}
        obj = CheckValue(scenario_cfg, {})
        try:
            obj.run({})
        except Exception as e:
            self.assertIsInstance(e, AssertionError)

    def test_check_value_not_equal(self):
        scenario_cfg = {'options': {'operator': 'not equal', 'value1': 1, 'value2': 1}}
        obj = CheckValue(scenario_cfg, {})
        try:
            obj.run({})
        except Exception as e:
            self.assertIsInstance(e, AssertionError)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
