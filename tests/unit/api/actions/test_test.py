##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest
import json

from api.actions import test


class RunTestCase(unittest.TestCase):

    def test_runTestCase_with_no_testcase_arg(self):
        args = {}
        output = json.loads(test.runTestCase(args))

        self.assertEqual('error', output['status'])


def main():
    unittest.main()


if __name__ == '__main__':
    main()
