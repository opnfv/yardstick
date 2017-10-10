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


class GetMigrateTargetHostTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.base.openstack_utils')
    def test_get_migrate_target_host(self, mock_openstack_utils):
        obj = GetMigrateTargetHost({}, {})
        obj.run({})

    @mock.patch('yardstick.benchmark.scenarios.base.openstack_utils')
    def test_get_migrate_host(self, mock_openstack_utils):
        class A(object):
            def __init__(self, service):
                self.service = service
                self.host = 'host4'

        mock_nova_client = mock_openstack_utils.get_nova_client()
        mock_nova_client.hosts.list_all.return_value = [A('compute')]
        obj = GetMigrateTargetHost({}, {})
        obj._host_name = 'host5'
        obj._get_migrate_host()


def main():
    unittest.main()


if __name__ == '__main__':
    main()
