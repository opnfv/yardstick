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

from yardstick.benchmark.scenarios.lib.delete_flavor import DeleteFlavor


class DeleteFlavorTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.delete_flavor')
    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_delete_flavor(self, mock_get_nova_client, mock_delete_flavor):
        options = {
            'flavor_name': 'yardstick_test_flavor'
        }
        args = {"options": options}
        obj = DeleteFlavor(args, {})
        obj.run({})
        self.assertTrue(mock_get_nova_client.called)
        self.assertTrue(mock_delete_flavor.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
