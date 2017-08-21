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

from yardstick.benchmark.scenarios.lib.delete_image import DeleteImage


class DeleteImageTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.delete_image')
    @mock.patch('yardstick.common.openstack_utils.get_image_id')
    @mock.patch('yardstick.common.openstack_utils.get_glance_client')
    def test_delete_image(self, mock_get_glance_client, mock_image_id, mock_delete_image):
        options = {
                'image_name': 'yardstick_test_image_01'
        }
        args = {"options": options}
        obj = DeleteImage(args, {})
        obj.run({})
        self.assertTrue(mock_delete_image.called)
        self.assertTrue(mock_image_id.called)
        self.assertTrue(mock_get_glance_client.called)

def main():
    unittest.main()


if __name__ == '__main__':
    main()
