import unittest

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


def main():
    unittest.main()


if __name__ == '__main__':
    main()
