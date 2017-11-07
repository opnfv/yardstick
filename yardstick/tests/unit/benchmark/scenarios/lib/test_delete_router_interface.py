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
import paramiko

from yardstick.benchmark.scenarios.lib.delete_router_interface import DeleteRouterInterface


class DeleteRouterInterfaceTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.get_neutron_client')
    @mock.patch('yardstick.common.openstack_utils.remove_interface_router')
    def test_delete_router_interface(self, mock_get_neutron_client, mock_remove_interface_router):
        options = {
            'router_id': '123-123-123',
            'subnet_id': '321-321-321'
        }
        args = {"options": options}
        obj = DeleteRouterInterface(args, {})
        obj.run({})
        self.assertTrue(mock_get_neutron_client.called)
        self.assertTrue(mock_remove_interface_router.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
