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

from yardstick.benchmark.scenarios.lib.delete_volume import DeleteVolume


class DeleteVolumeTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.get_cinder_client')
    @mock.patch('yardstick.common.openstack_utils.delete_volume')
    def test_delete_volume(self, mock_get_cinder_client, mock_delete_volume):
        options = {
            'volume_id': '123-123-123'
        }
        args = {"options": options}
        obj = DeleteVolume(args, {})
        obj.run({})
        self.assertTrue(mock_get_cinder_client.called)
        self.assertTrue(mock_delete_volume.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
