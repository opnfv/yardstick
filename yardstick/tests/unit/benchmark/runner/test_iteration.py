##############################################################################
# Copyright (c) 2018 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest
import multiprocessing
import os
import time

from yardstick.benchmark.runners import iteration
from yardstick.common import exceptions as y_exc


class IterationRunnerTest(unittest.TestCase):
    def setUp(self):
        self.scenario_cfg = {
            'runner': {'interval': 0, "duration": 0},
            'type': 'some_type'
        }

        self.benchmark = mock.Mock()
        self.benchmark_cls = mock.Mock(return_value=self.benchmark)

    def _assert_defaults__worker_run_setup_and_teardown(self):
        self.benchmark_cls.assert_called_once_with(self.scenario_cfg, {})
        self.benchmark.setup.assert_called_once()

    def _assert_defaults__worker_run_one_iteration(self):
        self.benchmark.pre_run_wait_time.assert_called_once_with(0)
        self.benchmark.my_method.assert_called_once_with({})

    def test__worker_process_broad_exception(self):
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.YardstickException)

        with self.assertRaises(Exception): 
            iteration._worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                                 self.scenario_cfg, {},
                                 multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_run_one_iteration()
        self._assert_defaults__worker_run_setup_and_teardown()
