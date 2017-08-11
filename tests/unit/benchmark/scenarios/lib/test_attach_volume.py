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

from yardstick.benchmark.scenarios.lib.attach_volume import AttachVolume


class AttachVolumeTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.attach_server_volume')
    def test_attach_volume(self, mock_attach_server_volume):
        options = {
                'volume_id': '123-456-000',
                'server_id': '000-123-456'
        }
        args = {"options": options}
        obj = AttachVolume(args, {})
        obj.run({})
        self.assertTrue(mock_attach_server_volume.called)

def main():
    unittest.main()


if __name__ == '__main__':
    main()
