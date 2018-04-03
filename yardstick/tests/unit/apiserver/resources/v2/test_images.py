##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import mock

import unittest

from yardstick.tests.unit.apiserver import APITestCase
from api.resources.v2.images import format_image_info


class V2ImagesTestCase(APITestCase):
    @mock.patch('yardstick.common.openstack_utils.list_images')
    @mock.patch('yardstick.common.utils.source_env')
    def test_get(self, _, mock_list_images):
        if self.app is None:
            unittest.skip('host config error')
            return

        single_image = mock.MagicMock()
        single_image.name = 'yardstick-image'
        single_image.size = 16384
        single_image.status = 'active'
        single_image.updated_at = '2018-04-08'

        mock_list_images.return_value = [single_image]
        url = 'api/v2/yardstick/images'
        resp = self._get(url)
        self.assertEqual(resp.get('status'), 1)


class FormatImageInfoTestCase(unittest.TestCase):
    def test_format_image_info(self):
        image = mock.MagicMock()
        image.name = 'yardstick-image'
        image.size = 1048576
        image.status = 'active'
        image.updated_at = '2018-04-08'

        image_dict = format_image_info(image)
        self.assertEqual(image_dict.get('size'), 1)
