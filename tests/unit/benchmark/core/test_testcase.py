#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.cmd.commands.testcase

from __future__ import absolute_import
import mock
import unittest

from yardstick.benchmark.core import testcase


class Arg(object):

    def __init__(self):
        self.casename = ('opnfv_yardstick_tc001',)
        self.input_file = 'extended_testcases.tar'


class TestcaseUT(unittest.TestCase):

    def test_list_all(self):
        t = testcase.Testcase()
        result = t.list_all()
        self.assertIsInstance(result, list)

    def test_show(self):
        t = testcase.Testcase()
        casename = Arg()
        result = t.show(casename)
        self.assertTrue(result)

    @mock.patch('yardstick.benchmark.core.testcase.shutil.copytree')
    def test_enable(self, copytree_mock):
        t = testcase.Testcase()
        input_file = Arg()
        result = t.enable(input_file)
        copytree_mock.assert_called()
        self.assertTrue(result)

    @mock.patch('yardstick.benchmark.core.testcase.shutil.rmtree')
    @mock.patch('yardstick.benchmark.core.testcase.shutil.copytree')
    def test_disable(self, rmtree_mock, copytree_mock):
        t = testcase.Testcase()
        result = t.disable()
        rmtree_mock.assert_called()
        copytree_mock.assert_called()
        self.assertTrue(result)

def main():
    unittest.main()


if __name__ == '__main__':
    main()
