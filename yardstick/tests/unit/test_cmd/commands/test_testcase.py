##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest
from mock import patch

from yardstick.cmd.commands.testcase import TestcaseCommands


class TestcaseCommandsUT(unittest.TestCase):
    @patch('yardstick.cmd.commands.testcase.TestcaseCommands._format_print')
    @patch('yardstick.cmd.commands.client')
    def test_do_list(self, mock_client, mock_print):
        mock_client.get.return_value = {'result': []}
        TestcaseCommands().do_list({})
        self.assertTrue(mock_print.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
