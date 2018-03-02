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

from yardstick.benchmark.scenarios.lib import create_keypair


class CreateKeypairTestCase(unittest.TestCase):
    @mock.patch.object(create_keypair, 'paramiko')
    @mock.patch.object(create_keypair, 'op_utils')
    def test_create_keypair(self, mock_op_utils, *args):
        options = {
            'key_name': 'yardstick_key',
            'key_path': '/tmp/yardstick_key'
        }
        args = {"options": options}
        obj = create_keypair.CreateKeypair(args, {})
        obj.run({})
        mock_op_utils.create_keypair.assert_called_once()
