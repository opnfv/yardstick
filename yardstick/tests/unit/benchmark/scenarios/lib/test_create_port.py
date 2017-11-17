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

from yardstick.benchmark.scenarios.lib.create_port import CreatePort


class CreatePortTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.get_neutron_client')
    def test_create_port(self, mock_get_neutron_client):
        options = {
          'openstack_paras': {
             'name': 'yardstick_port'
          }
        }
        args = {"options": options}
        obj = CreatePort(args, {})
        obj.run({})
        self.assertTrue(mock_get_neutron_client.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
