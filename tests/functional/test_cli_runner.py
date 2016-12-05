##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################


from __future__ import absolute_import
import unittest

from tests.functional import utils


class RunnerTestCase(unittest.TestCase):

    def setUp(self):
        super(RunnerTestCase, self).setUp()
        self.yardstick = utils.Yardstick()

    def test_runner_list(self):
        res = self.yardstick("runner list")

        self.assertIn("Duration", res)
        self.assertIn("Arithmetic", res)
        self.assertIn("Iteration", res)
        self.assertIn("Sequence", res)

    def test_runner_show_Duration(self):
        res = self.yardstick("runner show Duration")
        duration = "duration - amount of time" in res
        self.assertTrue(duration)

    def test_runner_show_Arithmetic(self):
        res = self.yardstick("runner show Arithmetic")
        arithmetic = "Run a scenario arithmetically" in res
        self.assertTrue(arithmetic)

    def test_runner_show_Iteration(self):
        res = self.yardstick("runner show Iteration")
        iteration = "iterations - amount of times" in res
        self.assertTrue(iteration)

    def test_runner_show_Sequence(self):
        res = self.yardstick("runner show Sequence")
        sequence = "sequence - list of values which are executed" in res
        self.assertTrue(sequence)
