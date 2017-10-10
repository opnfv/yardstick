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

from yardstick.benchmark.scenarios.lib.delete_keypair import DeleteKeypair


class DeleteKeypairTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.base.openstack_utils')
    def test_delete_keypair(self, mock_openstack_utils):
        mock_nova_client = mock_openstack_utils.get_nova_client()
        options = {
            'key_name': 'yardstick_key'
        }
        args = {"options": options}
        obj = DeleteKeypair(args, {})
        obj.run({})
        self.assertEqual(mock_openstack_utils.get_nova_client.call_count, 2)
        self.assertTrue(mock_nova_client.delete_keypair.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
