##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.common.utils

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


def main():
    unittest.main()

if __name__ == '__main__':
    main()
