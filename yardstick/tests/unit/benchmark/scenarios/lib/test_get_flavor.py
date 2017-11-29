##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest
import mock

from yardstick.benchmark.scenarios.lib.get_flavor import GetFlavor


class GetFlavorTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.get_flavor_by_name')
    def test_get_flavor(self, mock_get_flavor_by_name):
        options = {
            'flavor_name': 'yardstick_test_flavor'
        }
        args = {"options": options}
        obj = GetFlavor(args, {})
        obj.run({})
        self.assertTrue(mock_get_flavor_by_name.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
