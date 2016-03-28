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

import mock
import unittest

from yardstick.cmd.commands import testcase
from yardstick.cmd.commands.testcase import TestcaseCommands

class Arg(object):
    def __init__(self):
        self.casename=('opnfv_yardstick_tc001',)

class TestcaseCommandsUT(unittest.TestCase):

    def test_do_list(self):
        t = testcase.TestcaseCommands()
        result = t.do_list("")
        self.assertEqual(result, True)

    def test_do_show(self):
        t = testcase.TestcaseCommands()
        casename = Arg()
        result = t.do_show(casename)
        self.assertEqual(result, True)

