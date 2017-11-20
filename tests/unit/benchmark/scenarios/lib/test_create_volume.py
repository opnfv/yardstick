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

    @mock.patch('yardstick.common.openstack_utils.create_volume')
    @mock.patch('yardstick.common.openstack_utils.get_image_id')
    @mock.patch('yardstick.common.openstack_utils.get_cinder_client')
    @mock.patch('yardstick.common.openstack_utils.get_glance_client')
    def test_create_volume(self, mock_get_glance_client,
                           mock_get_cinder_client, mock_image_id,
                           mock_create_volume):
        """Test create_volume.

        Expected bahaviour:
            * The glance client is called (to get image info).
            * The cinder client is called to create the volume.
        """
        scenario_cfg = {
            "options" :
                {
                    'volume_name': 'yardstick_test_volume_01',
                    'size': '256',
                    'image': 'cirros-0.3.5'
                }
            }

        obj = CreateVolume(scenario_cfg, {})
        obj.run(result={})

        mock_get_glance_client.assert_called()
        mock_get_cinder_client.assert_called()
        mock_image_id.assert_called()
        mock_create_volume.assert_called()

def main():
    unittest.main()


if __name__ == '__main__':
    main()
