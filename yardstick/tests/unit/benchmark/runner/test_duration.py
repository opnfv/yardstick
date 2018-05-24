##############################################################################
# Copyright (c) 2018 Nokia and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest

from yardstick.benchmark.runners.duration import DurationRunner


class DurationRunnerTest(unittest.TestCase):

    @mock.patch('yardstick.benchmark.runners.duration.multiprocessing')
    def test__run_benchmark(self, mock_multiprocessing):
        scenario_cfg = {
            'runner': {},
        }

        runner = DurationRunner({})
        runner._run_benchmark(mock.Mock(), 'my_method', scenario_cfg, {})
        self.assertEqual(mock_multiprocessing.Process.call_count, 1)
