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

    @mock.patch('yardstick.common.openstack_utils.create_image')
    @mock.patch('yardstick.common.openstack_utils.get_glance_client')
    def test_create_image(self, mock_get_glance_client, mock_create_image):
        options = {
                'image_name': 'yardstick_test_image_01',
                'disk_format': 'qcow2',
                'container_format': 'bare',
                'min_disk': '1',
                'min_ram': '512',
                'protected': 'False',
                'tags': '["yardstick automatic test image"]',
                'file_path': '/home/opnfv/images/cirros-0.3.5-x86_64-disk.img'
        }
        args = {"options": options}
        obj = CreateImage(args, {})
        obj.run({})
        self.assertTrue(mock_create_image.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
