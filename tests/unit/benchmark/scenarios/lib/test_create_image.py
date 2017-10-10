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

from yardstick.benchmark.scenarios.lib.create_image import CreateImage


class CreateImageTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.base.openstack_utils')
    def test_create_image(self, mock_openstack_utils):
        mock_glance_client = mock_openstack_utils.get_glance_client()
        args = {
            "options": {
                'image_name': 'yardstick_test_image_01',
                'disk_format': 'qcow2',
                'container_format': 'bare',
                'min_disk': '1',
                'min_ram': '512',
                'protected': 'False',
                'tags': '["yardstick automatic test image"]',
                'file_path': '/home/opnfv/images/cirros-0.3.5-x86_64-disk.img',
            },
        }
        obj = CreateImage(args, {})
        obj.run({})
        self.assertEqual(mock_openstack_utils.get_glance_client.call_count, 2)
        self.assertTrue(mock_glance_client.create_image.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
