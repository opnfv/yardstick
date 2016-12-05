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
        lmbench = "Execute lmbench memory read latency"
        "or memory bandwidth benchmark in a host" in res
        self.assertTrue(lmbench)

    def test_scenario_show_Perf(self):
        res = self.yardstick("scenario show Perf")
        perf = "Execute perf benchmark in a host" in res
        self.assertTrue(perf)

    def test_scenario_show_Fio(self):
        res = self.yardstick("scenario show Fio")
        fio = "Execute fio benchmark in a host" in res
        self.assertTrue(fio)

    def test_scenario_show_Ping(self):
        res = self.yardstick("scenario show Ping")
        ping = "Execute ping between two hosts" in res
        self.assertTrue(ping)

    def test_scenario_show_Iperf3(self):
        res = self.yardstick("scenario show Iperf3")
        iperf3 = "Execute iperf3 between two hosts" in res
        self.assertTrue(iperf3)

    def test_scenario_show_Pktgen(self):
        res = self.yardstick("scenario show Pktgen")
        pktgen = "Execute pktgen between two hosts" in res
        self.assertTrue(pktgen)
