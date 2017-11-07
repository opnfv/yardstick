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

from yardstick.benchmark.scenarios.lib.create_router import CreateRouter


class CreateRouterTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.get_neutron_client')
    @mock.patch('yardstick.common.openstack_utils.create_neutron_router')
    def test_create_router(self, mock_get_neutron_client, mock_create_neutron_router):
        options = {
          'openstack_paras': {
             'admin_state_up': 'True',
             'name': 'yardstick_router'
          }
        }
        args = {"options": options}
        obj = CreateRouter(args, {})
        obj.run({})
        self.assertTrue(mock_get_neutron_client.called)
        self.assertTrue(mock_create_neutron_router.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
