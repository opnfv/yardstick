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

from api.actions import result


class GetResultTestCase(unittest.TestCase):

    def test_getResult_with_no_taskid_arg(self):
        args = {}
        output = json.loads(result.getResult(args))

        self.assertEqual('error', output['status'])


def main():
    unittest.main()


if __name__ == '__main__':
    main()
