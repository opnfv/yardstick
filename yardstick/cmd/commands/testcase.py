##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'testcase' """
from __future__ import print_function
from __future__ import absolute_import

from yardstick.benchmark.core.testcase import Testcase
from yardstick.benchmark.core import print_hbar
from yardstick.common.utils import cliargs
from yardstick.cmd.commands import change_osloobj_to_paras
from yardstick.cmd.commands import Commands


class TestcaseCommands(Commands):
    """Testcase commands.

       Set of commands to discover and display test cases.
    """

    def do_list(self, args):
        """List existing test cases"""
        testcase_list = self.client.get('/yardstick/testcases')['result']
        self._format_print(testcase_list)

    @cliargs("casename", type=str, help="test case name", nargs=1)
    def do_show(self, args):
        """Show details of a specific test case"""
        param = change_osloobj_to_paras(args)
        Testcase().show(param)

    def _format_print(self, testcase_list):
        """format output"""

        print_hbar(88)
        print("| %-21s | %-60s" % ("Testcase Name", "Description"))
        print_hbar(88)
        for testcase_record in testcase_list:
            print("| %-16s | %-60s" % (testcase_record['Name'],
                                       testcase_record['Description']))
        print_hbar(88)
