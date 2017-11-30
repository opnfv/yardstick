# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import unittest
from contextlib import contextmanager
import mock

from tests.unit import STL_MOCKS


STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.helpers.iniparser import ParseError
    from yardstick.network_services.helpers.iniparser import LineParser
    from yardstick.network_services.helpers.iniparser import BaseParser
    from yardstick.network_services.helpers.iniparser import ConfigParser

PARSE_TEXT_1 = """\

[section1]
key1=value1
list1: value2
       value3
       value4
key3='single quote value'  ; comment here
key4=

[section2]  ; comment with #2 other symbol
# here is a comment line
list2: value5
key with no value  # mixed comment ; symbols
; another comment line
key5=

[section1]  ; reopen a section!
key2="double quote value"
"""

PARSE_TEXT_2 = """\
[section1]
list1 = item1
        item2
        ended by eof"""

PARSE_TEXT_BAD_1 = """\
key1=value1
"""

PARSE_TEXT_BAD_2 = """\
[section1
"""

PARSE_TEXT_BAD_3 = """\
[]
"""

PARSE_TEXT_BAD_4 = """\
[section1]
    bad continuation
"""

PARSE_TEXT_BAD_5 = """\
[section1]
=value with no key
"""


class TestParseError(unittest.TestCase):

    def test___str__(self):
        error = ParseError('a', 2, 'c')
        self.assertEqual(str(error), "at line 2, a: 'c'")


class TestLineParser(unittest.TestCase):

    def test___repr__(self):
        line_parser = LineParser('', 101)
        self.assertIsNotNone(repr(line_parser))

    def test_error_invalid_assignment(self):
        line_parser = LineParser('', 101)
        self.assertIsNotNone(line_parser.error_invalid_assignment())


class TestBaseParser(unittest.TestCase):

    @staticmethod
    def make_open(text_blob):
        @contextmanager
        def internal_open(*args):
            yield text_blob.split('\n')

        return internal_open

    def test_parse(self):
        parser = BaseParser()
        parser.parse()

    def test_parse_empty_string(self):
        parser = BaseParser()
        self.assertIsNone(parser.parse(''))

    def test_not_implemented_methods(self):
        parser = BaseParser()

        with self.assertRaises(NotImplementedError):
            parser.assignment('key', 'value', LineParser('', 100))

        with self.assertRaises(NotImplementedError):
            parser.new_section('section')

        with self.assertRaises(NotImplementedError):
            parser.comment('comment')


class TestConfigParser(unittest.TestCase):

    @staticmethod
    def make_open(text_blob):
        @contextmanager
        def internal_open(*args):
            yield text_blob.split('\n')

        return internal_open

    @mock.patch('yardstick.network_services.helpers.iniparser.open')
    def test_parse(self, mock_open):
        mock_open.side_effect = self.make_open(PARSE_TEXT_1)

        existing_data = [['section0', [['key0', 'value0']]]]
        config_parser = ConfigParser('my_file', existing_data)
        config_parser.parse()

        expected = [
            [
                'section0',
                [
                    ['key0', 'value0'],
                ],
            ],
            [
                'section1',
                [
                    ['key1', 'value1'],
                    ['list1', 'value2\nvalue3\nvalue4'],
                    ['key3', 'single quote value'],
                    ['key4', ''],
                    ['key2', 'double quote value'],
                ],
            ],
            [
                'section2',
                [
                    ['list2', 'value5'],
                    ['key with no value', '@'],
                    ['key5', ''],
                ],
            ],
        ]

        self.assertEqual(config_parser.sections, expected)
        self.assertIsNotNone(config_parser.find_section('section1'))
        self.assertIsNone(config_parser.find_section('section3'))
        self.assertEqual(config_parser.find_section_index('section1'), 1)
        self.assertEqual(config_parser.find_section_index('section3'), -1)

    @mock.patch('yardstick.network_services.helpers.iniparser.open')
    def test_parse_2(self, mock_open):
        mock_open.side_effect = self.make_open(PARSE_TEXT_2)

        config_parser = ConfigParser('my_file')
        config_parser.parse()

        expected = [
            [
                'section1',
                [
                    ['list1', 'item1\nitem2\nended by eof'],
                ],
            ],
        ]

        self.assertEqual(config_parser.sections, expected)

    @mock.patch('yardstick.network_services.helpers.iniparser.open')
    def test_parse_negative(self, mock_open):
        bad_text_dict = {
            'no section': PARSE_TEXT_BAD_1,
            'incomplete section': PARSE_TEXT_BAD_2,
            'empty section name': PARSE_TEXT_BAD_3,
            'bad_continuation': PARSE_TEXT_BAD_4,
            'value with no key': PARSE_TEXT_BAD_5,
        }

        for bad_reason, bad_text in bad_text_dict.items():
            mock_open.side_effect = self.make_open(bad_text)

            config_parser = ConfigParser('my_file', [])

            try:
                # TODO: replace with assertRaises, when the UT framework supports
                # advanced messages when exceptions fail to occur
                config_parser.parse()
            except ParseError:
                pass
            else:
                self.fail('\n'.join([bad_reason, bad_text, str(config_parser.sections)]))
