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

from yardstick.benchmark.scenarios.lib.delete_server import DeleteServer


class DeleteServerTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.delete_instance')
    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_delete_server(self, mock_get_nova_client, mock_delete_instance):
        options = {
            'server_id': '1234-4567-0000'
        }
        args = {"options": options}
        obj = DeleteServer(args, {})
        obj.run({})
        self.assertTrue(mock_get_nova_client.called)
        self.assertTrue(mock_delete_instance.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
