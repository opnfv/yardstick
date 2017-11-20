##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'testcase' """
from __future__ import absolute_import

import prettytable

from yardstick.benchmark.core.testcase import Testcase
from yardstick.common.utils import cliargs
from yardstick.cmd.commands import change_osloobj_to_paras
from yardstick.cmd.commands import Commands


class TestcaseCommands(Commands):
    """Testcase commands.

       Set of commands to discover and display test cases.
    """

    def do_list(self, *args):
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
        case_table = prettytable.PrettyTable(['Testcase Name', 'Description'])
        case_table.align = 'l'
        for testcase_record in testcase_list:
            case_table.add_row([testcase_record['Name'], testcase_record['Description']])
        print(case_table)
