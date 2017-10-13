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


import os
import unittest
import mock

from contextlib import contextmanager
from six.moves import StringIO

from tests.unit import STL_MOCKS

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.helpers.iniparser import ParseError
    from yardstick.network_services.helpers.iniparser import LineParser
    from yardstick.network_services.helpers.iniparser import BaseParser
    from yardstick.network_services.helpers.iniparser import YardstickConfigParser

PARSE_TEXT_1 = """\

[section1]
key1=value1
list1: value2
       value3
       value4
key3='single quote value'  ; comment here
key4=
key1=value_one  # duplicate key
key1=value_two  # duplicate key, immediately following its own appearance
multi
    line
    key    # is this a thing?

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


class TestYardstickConfigParser(unittest.TestCase):

    @staticmethod
    def make_open(text_blob):
        @contextmanager
        def internal_open(*args):
            yield text_blob.split('\n')

        return internal_open

    def setUp(self):
        super(TestYardstickConfigParser, self).setUp()
        self.SMALL_SECTION = [
            'section1',
            [
                ['key1', 'value1'],
                ['key2', 'value2'],
            ],
        ]
        self.LARGE_SECTION = [
            'section1',
            [
                ['key1', 'value1'],
                ['key2', 'value2'],
                ['key1', 'value3'],
                ['key2', 'value4'],
                ['key1', 'value5'],
            ],
        ]

    def test_section_get(self):
        value = YardstickConfigParser.section_get(self.SMALL_SECTION, 'key2')
        self.assertEqual(value, 'value2')

    def test_section_get_default(self):
        value = YardstickConfigParser.section_get(self.SMALL_SECTION, 'key3', 'default3')
        self.assertEqual(value, 'default3')

    def test_section_get_invalid_section(self):
        with self.assertRaises(TypeError):
            YardstickConfigParser.section_get(None, 'key2', 'default2')

    def test_section_get_negative(self):
        with self.assertRaises(KeyError):
            YardstickConfigParser.section_get(self.SMALL_SECTION, 'key3')

    def test_section_set_value(self):

        expected = [
            'section1',
            [
                ['key1', 'value1'],
                ['key2', 'value_two'],
                ['key1', 'value3'],
                ['key2', 'value4'],
                ['key1', 'value5'],
            ],
        ]
        YardstickConfigParser.section_set_value(self.LARGE_SECTION, 'key2', 'value_two')
        self.assertEqual(self.LARGE_SECTION, expected)

    def test_section_set_value_set_one_not_first(self):

        expected = [
            'section1',
            [
                ['key1', 'value1'],
                ['key2', 'value2'],
                ['key1', 'value_one'],
                ['key2', 'value4'],
                ['key1', 'value5'],
            ],
        ]
        YardstickConfigParser.section_set_value(self.LARGE_SECTION, 'key1', 'value_one', 1)
        self.assertEqual(self.LARGE_SECTION, expected)

    def test_section_set_value_set_two(self):
        expected = [
            'section1',
            [
                ['key1', 'value_one'],
                ['key2', 'value2'],
                ['key1', 'value3'],
                ['key2', 'value4'],
                ['key1', 'value_one'],
            ],
        ]
        YardstickConfigParser.section_set_value(self.LARGE_SECTION, 'key1', 'value_one', [0, 2])
        self.assertEqual(self.LARGE_SECTION, expected)

    def test_section_set_value_set_all(self):
        expected = [
            'section1',
            [
                ['key1', 'value1'],
                ['key2', 'value_two'],
                ['key1', 'value3'],
                ['key2', 'value_two'],
                ['key1', 'value5'],
            ],
        ]
        YardstickConfigParser.section_set_value(self.LARGE_SECTION, 'key2', 'value_two',
                                                set_all=True)
        self.assertEqual(self.LARGE_SECTION, expected)

    def test_section_set_value_key_not_present(self):
        YardstickConfigParser.section_set_value(self.LARGE_SECTION, 'key3', 'value6')
        self.assertEqual(len(self.LARGE_SECTION[1]), 5)
        for key, value in self.LARGE_SECTION[1]:
            self.assertNotEqual(key, 'key3')
            self.assertNotEqual(value, 'value6')

    def test_section_del(self):
        s = self.SMALL_SECTION[:]
        YardstickConfigParser.section_del(s, 'key2')
        value = YardstickConfigParser.section_get(s, 'key2', default='default')
        self.assertEqual(value, 'default')

    def test_update_section(self):
        input_sections = [
            'MASTER',
            [
                ['type', 'value1'],
                ['filename', 0],
                ['type', 'value2'],
                ['filename', 10],
                ['type', 'value3'],
            ],
        ]
        new_section_data = [['filename', 1], ['filename', 15], ['filename', 25],
                            ['filename', 'last']]
        expected_sections = [
            'MASTER',
            [
                ['type', 'value1'],
                ['filename', 1],
                ['type', 'value2'],
                ['filename', 15],
                ['type', 'value3'],
                ['filename', 25],
                ['filename', 'last'],
            ],
        ]
        self.assertIsNone(
            YardstickConfigParser.update_section_data(input_sections, new_section_data))
        self.assertEqual(input_sections, expected_sections)

    def test_dump(self):
        input_data = []
        expected = ''

        config_parser = YardstickConfigParser(sections=input_data)
        result = config_parser.dumps()
        self.assertEqual(result, expected)

        input_data = [
            [
                'section1',
                [],
            ],
        ]
        expected = '[section1]\n\n'
        config_parser = YardstickConfigParser(sections=input_data)
        result = config_parser.dumps()
        self.assertEqual(result, expected)

        input_data = [
            [
                'section1',
                [],
            ],
            [
                'section2',
                [
                    ['key1', 'value1'],
                    ['__name__', 'not this one'],
                    ['key2', None],
                    ['key3', 234],
                    ['key4', 'multi-line\nvalue'],
                ],
            ],
        ]
        expected = os.linesep.join([
            '[section1]',
            '',
            '[section2]',
            'key1=value1',
            'key2',
            'key3=234',
            'key4=multi-line\n\tvalue',
            '',
            '',
        ])
        config_parser = YardstickConfigParser(sections=input_data)
        result = config_parser.dumps()
        self.assertEqual(result, expected)
        s = StringIO()
        config_parser.write(s)
        self.assertEqual(s.getvalue(), expected)

    def test_dump_key_value(self):
        b = StringIO()

        YardstickConfigParser.dump_key_value(b, "", "", quote="quote")
        self.assertEqual(b.getvalue(), "=quotequote")

    @mock.patch('yardstick.network_services.helpers.iniparser.open')
    def test_load(self, mock_open):
        mock_open.side_effect = self.make_open(PARSE_TEXT_1)

        config_parser = YardstickConfigParser(sections=[['section0', [['key0', 'value0']]]])
        config_parser.load('my_file')

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
                    ['key1', 'value_one'],
                    ['key1', 'value_two'],
                    ['multi\nline\nkey', '@'],
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
        self.assertIsNotNone(config_parser.find_section_data('section1'))
        self.assertIsNone(config_parser.find_section_data('section3'))
        self.assertEqual(config_parser.find_section_index('section1'), 1)
        self.assertEqual(config_parser.find_section_index('section3'), -1)
        c = YardstickConfigParser(sections=[['section0', [['key0', 'value0']]]])
        c.loads(PARSE_TEXT_1)
        self.assertEqual(c.sections, expected)

    @mock.patch('yardstick.network_services.helpers.iniparser.open')
    def test_parse(self, mock_open):
        mock_open.side_effect = self.make_open(PARSE_TEXT_2)

        config_parser = YardstickConfigParser('my_file')
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

            config_parser = YardstickConfigParser('my_file', [])

            try:
                # TODO: replace with assertRaises, when the UT framework supports
                # advanced messages when exceptions fail to occur
                config_parser.parse()
            except ParseError:
                pass
            else:
                self.fail('\n'.join([bad_reason, bad_text, str(config_parser.sections)]))

    def test_get(self):
        config_parser = YardstickConfigParser(sections=[['section1', [['key1', 'value1']]]])
        self.assertEqual(config_parser.get('section1', 'key1'), 'value1')

    def test_get_default(self):
        config_parser = YardstickConfigParser(sections=[])
        self.assertEqual(config_parser.get('section1', 'key1', 'default1'), 'default1')

    def test_get_negative(self):
        config_parser = YardstickConfigParser(sections=[])
        with self.assertRaises(KeyError):
            config_parser.get('section1', 'key1')

    def test_set(self):
        config_parser = YardstickConfigParser(sections=[])

        expected = [['section1', [['key1', 'value1']]]]
        config_parser.set('section1', 'key1', 'value1')
        self.assertEqual(config_parser.sections, expected)

    def test_set_existing_section(self):
        config_parser = YardstickConfigParser(sections=[['section1', [['key1', 'value1']]]])

        expected = [['section1', [['key1', 'value1'], ['key2', 'value2']]]]
        config_parser.set('section1', 'key2', 'value2')
        self.assertEqual(config_parser.sections, expected)

    def test_set_update_existing_key(self):
        config_parser = YardstickConfigParser(sections=[['section1', [['key1', 'value1']]]])

        expected = [['section1', [['key1', 'value2']]]]
        config_parser.set('section1', 'key1', 'value2')
        self.assertEqual(config_parser.sections, expected)

    def test_append(self):
        config_parser = YardstickConfigParser(sections=[])

        expected = [['section1', [['key1', 'value1']]]]
        config_parser.append('section1', 'key1', 'value1')
        self.assertEqual(config_parser.sections, expected)

    def test_append_existing_section(self):
        config_parser = YardstickConfigParser(sections=[['section1', [['key1', 'value1']]]])

        expected = [['section1', [['key1', 'value1'], ['key2', 'value2']]]]
        config_parser.append('section1', 'key2', 'value2')
        self.assertEqual(config_parser.sections, expected)

    def test_append_update_existing_key(self):
        config_parser = YardstickConfigParser(sections=[['section1', [['key1', 'value1']]]])

        expected = [['section1', [['key1', 'value1\nvalue2']]]]
        config_parser.append('section1', 'key1', 'value2')
        self.assertEqual(config_parser.sections, expected)
