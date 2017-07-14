##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.common.utils

from __future__ import absolute_import
import os
import mock
import unittest

from yardstick.common import utils


class IterSubclassesTestCase(unittest.TestCase):
    # Disclaimer: this class is a modified copy from
    # rally/tests/unit/common/plugin/test_discover.py
    # Copyright 2015: Mirantis Inc.

    def test_itersubclasses(self):
        class A(object):
            pass

        class B(A):
            pass

        class C(A):
            pass

        class D(C):
            pass

        self.assertEqual([B, C, D], list(utils.itersubclasses(A)))


class TryAppendModuleTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.utils.importutils')
    def test_try_append_module_not_in_modules(self, mock_importutils):

        modules = {}
        name = 'foo'
        utils.try_append_module(name, modules)
        mock_importutils.import_module.assert_called_with(name)

    @mock.patch('yardstick.common.utils.importutils')
    def test_try_append_module_already_in_modules(self, mock_importutils):

        modules = {'foo'}
        name = 'foo'
        utils.try_append_module(name, modules)
        self.assertFalse(mock_importutils.import_module.called)


class ImportModulesFromPackageTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.utils.os.walk')
    @mock.patch('yardstick.common.utils.try_append_module')
    def test_import_modules_from_package_no_mod(self, mock_append, mock_walk):

        sep = os.sep
        mock_walk.return_value = ([
            ('..' + sep + 'foo', ['bar'], ['__init__.py']),
            ('..' + sep + 'foo' + sep + 'bar', [], ['baz.txt', 'qux.rst'])
        ])

        utils.import_modules_from_package('foo.bar')
        self.assertFalse(mock_append.called)

    @mock.patch('yardstick.common.utils.os.walk')
    @mock.patch('yardstick.common.utils.importutils')
    def test_import_modules_from_package(self, mock_importutils, mock_walk):

        sep = os.sep
        mock_walk.return_value = ([
            ('foo' + sep + '..' + sep + 'bar', [], ['baz.py'])
        ])

        utils.import_modules_from_package('foo.bar')
        mock_importutils.import_module.assert_called_with('bar.baz')


class GetParaFromYaml(unittest.TestCase):

    @mock.patch('yardstick.common.utils.os.environ.get')
    def test_get_param_para_not_found(self, get_env):
        file_path = 'config_sample.yaml'
        get_env.return_value = self._get_file_abspath(file_path)
        args = 'releng.file'
        default = 'hello'
        self.assertTrue(utils.get_param(args, default), default)

    @mock.patch('yardstick.common.utils.os.environ.get')
    def test_get_param_para_exists(self, get_env):
        file_path = 'config_sample.yaml'
        get_env.return_value = self._get_file_abspath(file_path)
        args = 'releng.dir'
        para = '/home/opnfv/repos/releng'
        self.assertEqual(para, utils.get_param(args))

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path


class CommonUtilTestCase(unittest.TestCase):

    def setUp(self):
        self.data = {
            "benchmark": {
                "data": {
                    "mpstat": {
                        "cpu0": {
                            "%sys": "0.00",
                            "%idle": "99.00"
                        },
                        "loadavg": [
                            "1.09",
                            "0.29"
                        ]
                    },
                    "rtt": "1.03"
                }
            }
        }

    def test__dict_key_flatten(self):
        line = 'mpstat.loadavg1=0.29,rtt=1.03,mpstat.loadavg0=1.09,' \
               'mpstat.cpu0.%idle=99.00,mpstat.cpu0.%sys=0.00'
        # need to sort for assert to work
        line = ",".join(sorted(line.split(',')))
        flattened_data = utils.flatten_dict_key(
            self.data['benchmark']['data'])
        result = ",".join(
            ("=".join(item) for item in sorted(flattened_data.items())))
        self.assertEqual(result, line)


class TranslateToStrTestCase(unittest.TestCase):

    def test_translate_to_str_unicode(self):
        input_str = u'hello'
        output_str = utils.translate_to_str(input_str)

        result = 'hello'
        self.assertEqual(result, output_str)

    def test_translate_to_str_dict_list_unicode(self):
        input_str = {
            u'hello': {u'hello': [u'world']}
        }
        output_str = utils.translate_to_str(input_str)

        result = {
            'hello': {'hello': ['world']}
        }
        self.assertEqual(result, output_str)


class ChangeObjToDictTestCase(unittest.TestCase):

    def test_change_obj_to_dict(self):
        class A(object):
            def __init__(self):
                self.name = 'yardstick'

        obj = A()
        obj_r = utils.change_obj_to_dict(obj)
        obj_s = {'name': 'yardstick'}
        self.assertEqual(obj_r, obj_s)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
