##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'testcase' """
from yardstick.benchmark.core.testcase import Testcase
from yardstick.common.utils import cliargs
from yardstick.cmd.commands import change_osloobj_to_paras


class TestcaseCommands(object):
    '''Testcase commands.

       Set of commands to discover and display test cases.
    '''

    def do_list(self, args):
        '''List existing test cases'''
        param = change_osloobj_to_paras(args)
        Testcase().list_all(param)

    @cliargs("casename", type=str, help="test case name", nargs=1)
    def do_show(self, args):
        '''Show details of a specific test case'''
        param = change_osloobj_to_paras(args)
        Testcase().show(param)
