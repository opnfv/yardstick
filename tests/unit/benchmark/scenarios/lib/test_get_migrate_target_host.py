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

from yardstick.benchmark.scenarios.lib.get_migrate_target_host import GetMigrateTargetHost

BASE = 'yardstick.benchmark.scenarios.lib.get_migrate_target_host'


class GetMigrateTargetHostTestCase(unittest.TestCase):

    @mock.patch('{}.openstack_utils.get_nova_client'.format(BASE))
    @mock.patch('{}.GetMigrateTargetHost._get_migrate_host'.format(BASE))
    @mock.patch('{}.GetMigrateTargetHost._get_current_host_name'.format(BASE))
    def test_get_migrate_target_host(self,
                                     mock_get_current_host_name,
                                     mock_get_migrate_host,
                                     mock_get_nova_client):
        obj = GetMigrateTargetHost({}, {})
        obj.run({})
        self.assertTrue(mock_get_nova_client.called)
        self.assertTrue(mock_get_current_host_name.called)
        self.assertTrue(mock_get_migrate_host.called)

    @mock.patch('{}.openstack_utils.get_nova_client'.format(BASE))
    def test_get_migrate_host(self, mock_get_nova_client):
        class A(object):
            def __init__(self, service):
                self.service = service
                self.host = 'host4'

        mock_get_nova_client().hosts.list_all.return_value = [A('compute')]
        obj = GetMigrateTargetHost({}, {})
        host = obj._get_migrate_host('host5')
        self.assertTrue(mock_get_nova_client.called)
        self.assertEqual(host, 'host4')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
