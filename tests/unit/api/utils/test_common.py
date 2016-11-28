##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest
import json

from api.utils import common


class TranslateToStrTestCase(unittest.TestCase):

    def test_translate_to_str_unicode(self):
        input_str = u'hello'
        output_str = common.translate_to_str(input_str)

        result = 'hello'
        self.assertEqual(result, output_str)

    def test_translate_to_str_dict_list_unicode(self):
        input_str = {
            u'hello': {u'hello': [u'world']}
        }
        output_str = common.translate_to_str(input_str)

        result = {
            'hello': {'hello': ['world']}
        }
        self.assertEqual(result, output_str)


class GetCommandListTestCase(unittest.TestCase):

    def test_get_command_list_no_opts(self):
        command_list = ['a']
        opts = {}
        args = 'b'
        output_list = common.get_command_list(command_list, opts, args)

        result_list = ['a', 'b']
        self.assertEqual(result_list, output_list)

    def test_get_command_list_with_opts_args(self):
        command_list = ['a']
        opts = {
            'b': 'c',
            'task-args': 'd'
        }
        args = 'e'

        output_list = common.get_command_list(command_list, opts, args)

        result_list = ['a', 'e', '--b', '--task-args', 'd']
        self.assertEqual(result_list, output_list)


class ErrorHandlerTestCase(unittest.TestCase):

    def test_error_handler(self):
        message = 'hello world'
        output_dict = json.loads(common.error_handler(message))

        result = {
            'status': 'error',
            'message': message
        }

        self.assertEqual(result, output_dict)


class ResultHandlerTestCase(unittest.TestCase):

    def test_result_handler(self):
        status = 1
        data = ['hello world']
        output_dict = json.loads(common.result_handler(status, data))

        result = {
            'status': status,
            'result': data
        }

        self.assertEqual(result, output_dict)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
