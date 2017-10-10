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

from yardstick.benchmark.scenarios.lib.create_server import CreateServer


class CreateServerTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.base.openstack_utils')
    def test_create_server(self, mock_openstack_utils):
        mock_nova_client = mock_openstack_utils.get_nova_client()
        scenario_cfg = {
            'options' : {
                'openstack_paras': {},
            },
            'output': 'server',
        }
        obj = CreateServer(scenario_cfg, {})
        obj.run({})
        self.assertEqual(mock_openstack_utils.get_nova_client.call_count, 2)
        self.assertTrue(mock_nova_client.create_instance_and_wait_for_active.called)

    @mock.patch('yardstick.benchmark.scenarios.base.openstack_utils')
    def test_create_server_with_flavor_and_image(self, mock_openstack_utils):
        mock_nova_client = mock_openstack_utils.get_nova_client()
        scenario_cfg = {
            'options' : {
                'flavor_name': 'example_flavor',
                'image_name': 'example_image',
            },
            'output': 'server',
        }
        obj = CreateServer(scenario_cfg, {})
        obj.run({})
        self.assertEqual(mock_openstack_utils.get_nova_client.call_count, 2)
        self.assertGreater(len(obj.openstack_paras), 0)
        self.assertTrue(mock_openstack_utils.get_glance_client.called)
        self.assertTrue(mock_nova_client.create_instance_and_wait_for_active.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
