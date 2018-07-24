##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
from six.moves import builtins

from yardstick.benchmark.core import testcase
from yardstick.tests.unit import base as ut_base


class Arg(object):

    def __init__(self):
        self.casename = ('opnfv_yardstick_tc001', )


class TestcaseTestCase(ut_base.BaseUnitTestCase):

    def test_list_all(self):
        t = testcase.Testcase()
        result = t.list_all("")
        self.assertIsInstance(result, list)

    @mock.patch.object(builtins, 'print')
    def test_show(self, *args):
        t = testcase.Testcase()
        casename = Arg()
        result = t.show(casename)
        self.assertTrue(result)
