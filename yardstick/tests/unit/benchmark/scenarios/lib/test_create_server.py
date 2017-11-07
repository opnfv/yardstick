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

    @mock.patch('yardstick.common.openstack_utils.create_instance_and_wait_for_active')
    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    @mock.patch('yardstick.common.openstack_utils.get_glance_client')
    @mock.patch('yardstick.common.openstack_utils.get_neutron_client')
    def test_create_server(self, mock_get_nova_client, mock_get_neutron_client,
                           mock_get_glance_client, mock_create_instance_and_wait_for_active):
        scenario_cfg = {
            'options' : {
                 'openstack_paras': 'example'
             },
             'output': 'server'
        }
        obj = CreateServer(scenario_cfg, {})
        obj.run({})
        self.assertTrue(mock_get_nova_client.called)
        self.assertTrue(mock_get_glance_client.called)
        self.assertTrue(mock_get_neutron_client.called)
        self.assertTrue(mock_create_instance_and_wait_for_active.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
