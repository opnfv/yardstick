#!/usr/bin/env python

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

import unittest
import multiprocessing
import time

from yardstick.benchmark.runners.iteration import IterationRunner


class RunnerTestCase(unittest.TestCase):

    def test_get_output(self):
        queue = multiprocessing.Queue()
        runner = IterationRunner({}, queue)
        runner.output_queue.put({'case': 'opnfv_yardstick_tc002'})
        runner.output_queue.put({'criteria': 'PASS'})

        idle_result = {
            'case': 'opnfv_yardstick_tc002',
            'criteria': 'PASS'
        }

        time.sleep(1)
        actual_result = runner.get_output()
        self.assertEqual(idle_result, actual_result)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
