##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import mock
import unittest

from yardstick.benchmark.scenarios.lib import create_volume


class CreateVolumeTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_cinder_client = mock.patch(
            'yardstick.common.openstack_utils.get_cinder_client')
        self.mock_cinder_client = self._mock_cinder_client.start()
        self._mock_glance_client = mock.patch(
            'yardstick.common.openstack_utils.get_glance_client')
        self.mock_glance_client = self._mock_glance_client.start()
        self.addCleanup(self._stop_mock)

        self.scenario_cfg = {
            "options" :
                {
                    'volume_name': 'yardstick_test_volume_01',
                    'size': '256',
                    'image': 'cirros-0.3.5'
                }
            }

        self.scenario = create_volume.CreateVolume(
            scenario_cfg=self.scenario_cfg,
            context_cfg={})

    def _stop_mock(self):
        self._mock_cinder_client.stop()
        self._mock_glance_client.stop()

    def test_init(self):
        self.mock_cinder_client.return_value = "All volumes are equal"
        self.mock_glance_client.return_value = "Images are more equal"

        expected_vol_name = self.scenario_cfg["options"]["volume_name"]
        expected_vol_size = self.scenario_cfg["options"]["size"]
        expected_im_name = self.scenario_cfg["options"]["image"]
        expected_im_id = None

        scenario = create_volume.CreateVolume(
            scenario_cfg=self.scenario_cfg,
            context_cfg={})

        self.assertEqual(expected_vol_name, scenario.volume_name)
        self.assertEqual(expected_vol_size, scenario.volume_size)
        self.assertEqual(expected_im_name, scenario.image_name)
        self.assertEqual(expected_im_id, scenario.image_id)
        self.assertEqual("All volumes are equal", scenario.cinder_client)
        self.assertEqual("Images are more equal", scenario.glance_client)

    def test_setup(self):
        self.assertFalse(self.scenario.setup_done)
        self.scenario.setup()
        self.assertTrue(self.scenario.setup_done)

    @mock.patch('yardstick.common.openstack_utils.create_volume')
    @mock.patch('yardstick.common.openstack_utils.get_image_id')
    def test_run(self, mock_image_id, mock_create_volume):
        self.scenario.run()

        mock_image_id.assert_called_once()
        mock_create_volume.assert_called_once()

    @mock.patch.object(create_volume.CreateVolume, 'setup')
    def test_run_no_setup(self, scenario_setup):
        self.scenario.setup_done = False
        self.scenario.run()
        scenario_setup.assert_called_once()

    @mock.patch('yardstick.common.openstack_utils.create_volume')
    @mock.patch('yardstick.common.openstack_utils.get_image_id')
    @mock.patch('yardstick.common.openstack_utils.get_cinder_client')
    @mock.patch('yardstick.common.openstack_utils.get_glance_client')
    def test_create_volume(self, mock_get_glance_client,
                           mock_get_cinder_client, mock_image_id,
                           mock_create_volume):
        options = {
            'volume_name': 'yardstick_test_volume_01',
            'size': '256',
            'image': 'cirros-0.3.5'
        }
        args = {"options": options}
        scenario = create_volume.CreateVolume(args, {})
        scenario.run()
        self.assertTrue(mock_create_volume.called)
        self.assertTrue(mock_image_id.called)
        self.assertTrue(mock_get_glance_client.called)
        self.assertTrue(mock_get_cinder_client.called)
