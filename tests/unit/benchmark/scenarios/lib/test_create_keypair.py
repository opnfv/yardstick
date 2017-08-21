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

from yardstick.benchmark.scenarios.lib.create_keypair import CreateKeypair


class CreateKeypairTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.create_keypair')
    def test_create_keypair(self, mock_create_keypair):
        options = {
            'key_name': 'yardstick_key',
            'key_path': '/tmp/yardstick_key'
        }
        args = {"options": options}
        obj = CreateKeypair(args, {})
        obj.run({})
        self.assertTrue(mock_create_keypair.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
