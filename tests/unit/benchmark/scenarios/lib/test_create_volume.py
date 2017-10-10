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

from yardstick.benchmark.scenarios.lib.create_volume import CreateVolume


class CreateVolumeTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.base.openstack_utils')
    def test_create_volume(self, mock_openstack_utils):
        mock_glance_client = mock_openstack_utils.get_glance_client()
        mock_cinder_client = mock_openstack_utils.get_cinder_client()
        args = {
            "options": {
                'volume_name': 'yardstick_test_volume_01',
                'size': '256',
                'image': 'cirros-0.3.5',
            },
        }
        obj = CreateVolume(args, {})
        obj.run({})
        self.assertEqual(mock_openstack_utils.get_glance_client.call_count, 2)
        self.assertEqual(mock_openstack_utils.get_cinder_client.call_count, 2)
        self.assertTrue(mock_cinder_client.create_volume.called)
        self.assertTrue(mock_glance_client.get_image_id.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
