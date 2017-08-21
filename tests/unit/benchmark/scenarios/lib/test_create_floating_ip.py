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

from yardstick.benchmark.scenarios.lib.create_floating_ip import CreateFloatingIp


class CreateFloatingIpTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.create_floating_ip')
    @mock.patch('yardstick.common.openstack_utils.get_network_id')
    @mock.patch('yardstick.common.openstack_utils.get_neutron_client')
    def test_create_floating_ip(self, mock_create_floating_ip, mock_get_network_id, mock_get_neutron_client):
        options = {}
        args = {"options": options}
        obj = CreateFloatingIp(args, {})
        obj.run({})
        self.assertTrue(mock_create_floating_ip.called)
        self.assertTrue(mock_get_network_id.called)
        self.assertTrue(mock_get_neutron_client.called)

def main():
    unittest.main()


if __name__ == '__main__':
    main()
