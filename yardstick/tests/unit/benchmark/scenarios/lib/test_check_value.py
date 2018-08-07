##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest

from yardstick.benchmark.scenarios.lib import check_value
from yardstick.common import exceptions as y_exc


class CheckValueTestCase(unittest.TestCase):

    def test_eq_pass(self):
        scenario_cfg = {'options': {'operator': 'eq',
                                    'value1': 1,
                                    'value2': 1}}
        obj = check_value.CheckValue(scenario_cfg, {})
        result = obj.run({})

        self.assertEqual({}, result)

    def test_ne_pass(self):
        scenario_cfg = {'options': {'operator': 'ne',
                                    'value1': 1,
                                    'value2': 2}}
        obj = check_value.CheckValue(scenario_cfg, {})
        result = obj.run({})

        self.assertEqual({}, result)

    def test_result(self):
        scenario_cfg = {'options': {'operator': 'eq',
                                    'value1': 1,
                                    'value2': 1},
                        'output': 'foo'}
        obj = check_value.CheckValue(scenario_cfg, {})
        result = obj.run({})

        self.assertDictEqual(result, {'foo': 'PASS'})

    def test_eq(self):
        scenario_cfg = {'options': {'operator': 'eq',
                                    'value1': 1,
                                    'value2': 2}}
        obj = check_value.CheckValue(scenario_cfg, {})

        with self.assertRaises(y_exc.ValueCheckError):
            result = obj.run({})
            self.assertEqual({}, result)

    def test_ne(self):
        scenario_cfg = {'options': {'operator': 'ne',
                                    'value1': 1,
                                    'value2': 1}}
        obj = check_value.CheckValue(scenario_cfg, {})

        with self.assertRaises(y_exc.ValueCheckError):
            result = obj.run({})
            self.assertEqual({}, result)
