##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest
import mock

from yardstick.cmd.commands.env import EnvCommand


class EnvCommandTestCase(unittest.TestCase):

    @mock.patch('yardstick.cmd.commands.env.HttpClient')
    def test_do_influxdb(self, mock_http_client):
        env = EnvCommand()
        env.do_influxdb({})
        self.assertTrue(mock_http_client().post.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
