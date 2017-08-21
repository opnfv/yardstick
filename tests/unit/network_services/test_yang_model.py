# Copyright (c) 2016-2017 Intel Corporation
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

# Unittest for yardstick.network_services.utils

from __future__ import absolute_import

import unittest
import mock

import yaml

from yardstick.network_services.yang_model import YangModel


class YangModelTestCase(unittest.TestCase):
    """Test all Yang Model methods."""

    ENTRIES = {
        'access-list1': {
            'acl': {
                'access-list-entries': [{
                    'ace': {
                        'ace-oper-data': {
                            'match-counter': 0},
                        'actions': 'drop,count',
                        'matches': {
                            'destination-ipv4-network':
                                '152.16.40.20/24',
                            'destination-port-range': {
                                'lower-port': 0,
                                'upper-port': 65535},
                            'source-ipv4-network': '0.0.0.0/0',
                            'source-port-range': {
                                'lower-port': 0,
                                'upper-port': 65535}},
                        'rule-name': 'rule1588'}},
                    {
                        'ace': {
                            'ace-oper-data': {
                                'match-counter': 0},
                            'actions': 'drop,count',
                            'matches': {
                                'destination-ipv4-network':
                                    '0.0.0.0/0',
                                'destination-port-range': {
                                    'lower-port': 0,
                                    'upper-port': 65535},
                                'source-ipv4-network':
                                    '152.16.100.20/24',
                                'source-port-range': {
                                    'lower-port': 0,
                                    'upper-port': 65535}},
                            'rule-name': 'rule1589'}}],
                'acl-name': 'sample-ipv4-acl',
                    'acl-type': 'ipv4-acl'}
        }
    }

    def test__init__(self):
        cfg = "yang.yaml"
        y = YangModel(cfg)
        self.assertEqual(y.config_file, cfg)

    def test_config_file_setter(self):
        cfg = "yang.yaml"
        y = YangModel(cfg)
        self.assertEqual(y.config_file, cfg)
        cfg2 = "yang2.yaml"
        y.config_file = cfg2
        self.assertEqual(y.config_file, cfg2)

    def test__get_entries(self):
        cfg = "yang.yaml"
        y = YangModel(cfg)
        y._options = self.ENTRIES
        y._get_entries()
        self.assertIn("p acl add", y._rules)

    def test__get_entries_no_options(self):
        cfg = "yang.yaml"
        y = YangModel(cfg)
        y._get_entries()
        self.assertEqual(y._rules, '')

    @mock.patch('yardstick.network_services.yang_model.yaml_load')
    @mock.patch('yardstick.network_services.yang_model.open')
    def test__read_config(self, mock_open, mock_safe_load):
        cfg = "yang.yaml"
        y = YangModel(cfg)
        mock_safe_load.return_value = expected = {'key1': 'value1', 'key2': 'value2'}
        y._read_config()
        self.assertDictEqual(y._options, expected)

    @mock.patch('yardstick.network_services.yang_model.open')
    def test__read_config_open_error(self, mock_open):
        cfg = "yang.yaml"
        y = YangModel(cfg)
        mock_open.side_effect = IOError('my error')

        self.assertEqual(y._options, {})
        with self.assertRaises(IOError) as raised:
            y._read_config()

        self.assertIn('my error', str(raised.exception))
        self.assertEqual(y._options, {})

    def test_get_rules(self):
        cfg = "yang.yaml"
        y = YangModel(cfg)
        y._read_config = read_mock = mock.Mock()
        y._get_entries = get_mock = mock.Mock()

        y._rules = None
        self.assertIsNone(y.get_rules())
        self.assertEqual(read_mock.call_count, 1)
        self.assertEqual(get_mock.call_count, 1)

        # True value should prevent calling read and get
        y._rules = 999
        self.assertEqual(y.get_rules(), 999)
        self.assertEqual(read_mock.call_count, 1)
        self.assertEqual(get_mock.call_count, 1)
