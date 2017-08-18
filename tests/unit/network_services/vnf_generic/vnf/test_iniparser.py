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

from __future__ import absolute_import

import unittest
from contextlib import contextmanager
import mock

from tests.unit import STL_MOCKS


STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.iniparser import ParseError
    from yardstick.network_services.vnf_generic.vnf.iniparser import BaseParser
    from yardstick.network_services.vnf_generic.vnf.iniparser import ConfigParser

PARSE_TEXT_1 = """\

[section1]
key1=value1
list1: value2
       value3
       value4
key2="double quote value"
key3='single quote value'  ; comment here
key4=

[section2]
# here is a comment line
list2: value5
; another comment line
key5=
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
no list or key
"""

PARSE_TEXT_BAD_5 = """\
[section1]
    bad continuation
"""

PARSE_TEXT_BAD_6 = """\
[section1]
=value with no key
"""


class TestParseError(unittest.TestCase):

    def test___str__(self):
        error = ParseError('a', 2, 'c')
        self.assertEqual(str(error), "at line 2, a: 'c'")


class TestBaseParser(unittest.TestCase):

    @staticmethod
    def make_open(text_blob):
        @contextmanager
        def internal_open(*args, **kwargs):
            yield text_blob.split('\n')

        return internal_open

    @mock.patch('yardstick.network_services.vnf_generic.vnf.iniparser.open')
    def test_parse_none(self, mock_open):
        mock_open.side_effect = self.make_open('')

        parser = BaseParser()

        self.assertIsNone(parser.parse())

    def test_not_implemented_methods(self):
        parser = BaseParser()

        with self.assertRaises(NotImplementedError):
            parser.assignment('key', 'value')

        with self.assertRaises(NotImplementedError):
            parser.new_section('section')


class TestConfigParser(unittest.TestCase):

    @staticmethod
    def make_open(text_blob):
        @contextmanager
        def internal_open(*args, **kwargs):
            yield text_blob.split('\n')

        return internal_open

    @mock.patch('yardstick.network_services.vnf_generic.vnf.iniparser.open')
    def test_parse(self, mock_open):
        mock_open.side_effect = self.make_open(PARSE_TEXT_1)

        config_parser = ConfigParser('my_file', {})
        config_parser.parse()

        expected = {
            'section1': [
                ['key1', 'value1'],
                ['list1', 'value2\nvalue3\nvalue4'],
                ['key2', 'double quote value'],
                ['key3', 'single quote value'],
                ['key4', ''],
            ],
            'section2': [
                ['list2', 'value5'],
                ['key5', ''],
            ],
        }

        self.assertDictEqual(config_parser.sections, expected)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.iniparser.open')
    def test_parse_2(self, mock_open):
        mock_open.side_effect = self.make_open(PARSE_TEXT_2)

        config_parser = ConfigParser('my_file', {})
        config_parser.parse()

        expected = {
            'section1': [
                ['list1', 'item1\nitem2\nended by eof'],
            ],
        }

        self.assertDictEqual(config_parser.sections, expected)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.iniparser.open')
    def test_parse_negative(self, mock_open):
        bad_text_dict = {
            'no section': PARSE_TEXT_BAD_1,
            'incomplete section': PARSE_TEXT_BAD_2,
            'empty section name': PARSE_TEXT_BAD_3,
            'no list or key': PARSE_TEXT_BAD_4,
            'bad_continuation': PARSE_TEXT_BAD_5,
            'value with no key': PARSE_TEXT_BAD_6,
        }

        for bad_reason, bad_text in bad_text_dict.items():
            mock_open.side_effect = self.make_open(bad_text)

            config_parser = ConfigParser('my_file', {})

            try:
                # TODO: replace with assertRaises, when the UT framework supports
                # advanced messages when exceptions fail to occur
                config_parser.parse()
            except ParseError:
                pass
            else:
                self.fail('\n'.join([bad_reason, bad_text, str(config_parser.sections)]))
