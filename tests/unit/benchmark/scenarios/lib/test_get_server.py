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

from yardstick.benchmark.scenarios.lib.get_server import GetServer


class GetServerTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.base.openstack_utils')
    def test_get_server_with_name(self, mock_openstack_utils):
        scenario_cfg = {
            'options': {
                'server_name': 'yardstick_server'
            },
            'output': 'status server'
        }
        obj = GetServer(scenario_cfg, {})
        obj.run({})
        self.assertTrue(mock_openstack_utils.get_server_by_name.called)

    @mock.patch('yardstick.benchmark.scenarios.base.openstack_utils')
    def test_get_server_with_id(self, mock_openstack_utils):
        mock_server = mock.Mock()
        mock_nova_client = mock_openstack_utils.get_nova_client()
        mock_nova_client.servers = {'1': mock_server}
        scenario_cfg = {
            'options': {
                'server_id': '1'
            },
            'output': 'status server'
        }
        obj = GetServer(scenario_cfg, {})
        obj.run({})
        self.assertEqual(mock_openstack_utils.get_nova_client.call_count, 2)
        self.assertIs(obj.current_server, mock_server)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
