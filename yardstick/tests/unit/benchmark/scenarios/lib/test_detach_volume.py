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

from yardstick.benchmark.scenarios.lib.detach_volume import DetachVolume


class DetachVolumeTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.detach_volume')
    def test_detach_volume(self, mock_detach_volume):
        options = {
            'server_id': '321-321-321',
            'volume_id': '123-123-123'
        }
        args = {"options": options}
        obj = DetachVolume(args, {})
        obj.run({})
        self.assertTrue(mock_detach_volume.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
