##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import unittest

from yardstick.tests.functional import utils


class ScenarioTestCase(unittest.TestCase):

    def setUp(self):
        super(ScenarioTestCase, self).setUp()
        self.yardstick = utils.Yardstick()

    def test_scenario_list(self):
        res = self.yardstick("scenario list")

        self.assertIn("Lmbench", res)
        self.assertIn("Perf", res)
        self.assertIn("Fio", res)
        self.assertIn("Ping", res)
        self.assertIn("Iperf3", res)
        self.assertIn("Pktgen", res)

    def test_scenario_show_Lmbench(self):
        res = self.yardstick("scenario show Lmbench")
        self.assertIn("Execute lmbench memory read latency or memory "
                      "bandwidth benchmark in a hos", res)

    def test_scenario_show_Perf(self):
        res = self.yardstick("scenario show Perf")
        self.assertIn("Execute perf benchmark in a host", res)

    def test_scenario_show_Fio(self):
        res = self.yardstick("scenario show Fio")
        self.assertIn("Execute fio benchmark in a host", res)

    def test_scenario_show_Ping(self):
        res = self.yardstick("scenario show Ping")
        self.assertIn("Execute ping between two hosts", res)

    def test_scenario_show_Iperf3(self):
        res = self.yardstick("scenario show Iperf3")
        self.assertIn("Execute iperf3 between two hosts", res)

    def test_scenario_show_Pktgen(self):
        res = self.yardstick("scenario show Pktgen")
        self.assertIn("Execute pktgen between two hosts", res)
