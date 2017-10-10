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

    @mock.patch('yardstick.benchmark.scenarios.base.openstack_utils')
    def test_create_floating_ip(self, mock_openstack_utils):
        mock_neutron_client = mock_openstack_utils.get_neutron_client()
        args = {"options": {}}
        obj = CreateFloatingIp(args, {})
        obj.run({})
        self.assertEqual(mock_openstack_utils.get_neutron_client.call_count, 2)
        self.assertTrue(mock_neutron_client.create_floating_ip.called)
        self.assertTrue(mock_neutron_client.get_network_id.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
