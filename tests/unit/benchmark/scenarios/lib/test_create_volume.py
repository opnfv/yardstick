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

    @mock.patch('yardstick.common.openstack_utils.get_cinder_client', autospec=True)
    @mock.patch('yardstick.common.openstack_utils.get_glance_client', autospec=True)
    def setUp(self, mock_glance_client, mock_cinder_client):
        """Set up class for CreateVolumeTestCase"""
        # To instantiate CreateVolume here, we need these clients mocked
        # so that the tests don't try to talk to OpenStack
        self.mock_cinder_client = mock_cinder_client
        self.mock_glance_client = mock_glance_client

        self.scenario_cfg = {
            "options" :
                {
                    'volume_name': 'yardstick_test_volume_01',
                    'size': '256',
                    'image': 'cirros-0.3.5'
                }
            }

        self.scenario = CreateVolume(scenario_cfg=self.scenario_cfg,
                                     context_cfg={})

    @mock.patch('yardstick.common.openstack_utils.get_cinder_client')
    @mock.patch('yardstick.common.openstack_utils.get_glance_client')
    def test_init(self, mock_glance_client, mock_cinder_client):
        """Test that the CreateVolume object is instantiated correctly.


        Setup: None
        Test: create a new CreateVolume object
        Expected behaviour:
          * Attributes are set correctly (volume_name, volume_size,
            image_name, image_id, glance_client, cinder_client)
        """
        mock_cinder_client.return_value = "All volumes are equal"
        mock_glance_client.return_value = "Images are more equal"

        expected_vol_name = self.scenario_cfg["options"]["volume_name"]
        expected_vol_size = self.scenario_cfg["options"]["size"]
        expected_im_name = self.scenario_cfg["options"]["image"]
        expected_im_id = None

        scenario = CreateVolume(scenario_cfg=self.scenario_cfg,
                                context_cfg={})

        self.assertEqual(expected_vol_name, scenario.volume_name)
        self.assertEqual(expected_vol_size, scenario.volume_size)
        self.assertEqual(expected_im_name, scenario.image_name)
        self.assertEqual(expected_im_id, scenario.image_id)
        self.assertEqual("All volumes are equal", scenario.cinder_client)
        self.assertEqual("Images are more equal", scenario.glance_client)

    def test_setup(self):
        """Test CreateVolume.setup.

        Set-up: CreateVolume.setup_done is False
        Test: calle CreateVolume.setup()
        Expected behaviour: CreateVolume.setup_done is true
        """
        self.assertFalse(self.scenario.setup_done)

        self.scenario.setup()

        self.assertTrue(self.scenario.setup_done)

    @mock.patch('yardstick.common.openstack_utils.create_volume')
    @mock.patch('yardstick.common.openstack_utils.get_image_id')
    def test_run(self, mock_image_id,
                 mock_create_volume):
        """Test CreateVolume.run under normal conditions.

        Expected bahaviour:
            * The glance client is called (to get image info).
            * The cinder client is called to create the volume.
        """

        self.scenario.run(result={})

        mock_image_id.assert_called()
        mock_create_volume.assert_called()

    @mock.patch.object(CreateVolume, 'setup')
    def test_run_no_setup(self, scenario_setup):
        """Test CreateVolume.run when setup is not done.

        Set-up: CreateVolume.setup is False
        Test: call CreateVolume.run
        Expected behaviour: CreateVolume.setup is called
        """
        self.scenario.setup_done = False

        self.scenario.run(result={})

        scenario_setup.assert_called()


def main():
    unittest.main()


if __name__ == '__main__':
    main()
