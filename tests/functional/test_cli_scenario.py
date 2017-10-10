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
import logging
import subprocess

from tests.functional import utils

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class ScenarioTestCase(unittest.TestCase):

    def setUp(self):
        super(ScenarioTestCase, self).setUp()
        self.yardstick = utils.Yardstick()

    def test_scenario_list(self):
        try:
            res = self.yardstick("scenario list")
        except subprocess.CalledProcessError as e:
            LOGGER.error('Command output:\n%s', e.output)
            raise

        self.assertIn("Lmbench", res)
        self.assertIn("Perf", res)
        self.assertIn("Fio", res)
        self.assertIn("Ping", res)
        self.assertIn("Iperf3", res)
        self.assertIn("Pktgen", res)

    def test_scenario_show_Lmbench(self):
        res = self.yardstick("scenario show Lmbench")
        sub_str = "Execute lmbench memory read latency or memory bandwidth benchmark in a host"
        self.assertIn(sub_str, res)

    def test_scenario_show_Perf(self):
        res = self.yardstick("scenario show Perf")
        sub_str = "Execute perf benchmark in a host"
        self.assertIn(sub_str, res)

    def test_scenario_show_Fio(self):
        res = self.yardstick("scenario show Fio")
        sub_str = "Execute fio benchmark in a host"
        self.assertIn(sub_str, res)

    def test_scenario_show_Ping(self):
        res = self.yardstick("scenario show Ping")
        sub_str = "Execute ping between two hosts"
        self.assertIn(sub_str, res)

    def test_scenario_show_Iperf3(self):
        res = self.yardstick("scenario show Iperf3")
        sub_str = "Execute iperf3 between two hosts"
        self.assertIn(sub_str, res)

    def test_scenario_show_Pktgen(self):
        res = self.yardstick("scenario show Pktgen")
        sub_str = "Execute pktgen between two hosts"
        self.assertIn(sub_str, res)
