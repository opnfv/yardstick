##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'testcase' """
from yardstick.cmd import print_hbar
from yardstick.common.task_template import TaskTemplate
from yardstick.common.utils import cliargs
import os
import yaml
import sys


class TestcaseCommands(object):
    '''Testcase commands.

       Set of commands to discover and display test cases.
    '''
    def __init__(self):
        self.test_case_path = 'tests/opnfv/test_cases/'
        self.testcase_list = []

    def do_list(self, args):
        '''List existing test cases'''

        try:
            testcase_files = os.listdir(self.test_case_path)
        except Exception as e:
            print(("Failed to list dir:\n%(path)s\n%(err)s\n")
                  % {"path": self.test_case_path, "err": e})
            raise e
        testcase_files.sort()

        for testcase_file in testcase_files:
            record = self._get_record(testcase_file)
            self.testcase_list.append(record)

        self._format_print(self.testcase_list)
        return True

    @cliargs("casename", type=str, help="test case name", nargs=1)
    def do_show(self, args):
        '''Show details of a specific test case'''
        testcase_name = args.casename[0]
        testcase_path = self.test_case_path + testcase_name + ".yaml"
        try:
            with open(testcase_path) as f:
                try:
                    testcase_info = f.read()
                    print testcase_info

                except Exception as e:
                    print(("Failed to load test cases:"
                           "\n%(testcase_file)s\n%(err)s\n")
                          % {"testcase_file": testcase_path, "err": e})
                    raise e
        except IOError as ioerror:
            sys.exit(ioerror)
        return True

    def _get_record(self, testcase_file):

        try:
            with open(self.test_case_path + testcase_file) as f:
                try:
                    testcase_info = f.read()
                except Exception as e:
                    print(("Failed to load test cases:"
                           "\n%(testcase_file)s\n%(err)s\n")
                          % {"testcase_file": testcase_file, "err": e})
                    raise e
                description, installer, deploy_scenarios = \
                    self._parse_testcase(testcase_info)

                record = {'Name': testcase_file.split(".")[0],
                          'Description': description,
                          'installer': installer,
                          'deploy_scenarios': deploy_scenarios}
                return record
        except IOError as ioerror:
            sys.exit(ioerror)

    def _parse_testcase(self, testcase_info):

        kw = {}
        rendered_testcase = TaskTemplate.render(testcase_info, **kw)
        testcase_cfg = yaml.load(rendered_testcase)
        test_precondition = testcase_cfg.get('precondition', None)
        installer_type = 'all'
        deploy_scenarios = 'all'
        if test_precondition is not None:
            installer_type = test_precondition.get('installer_type', 'all')
            deploy_scenarios = test_precondition.get('deploy_scenarios', 'all')

        description = testcase_info.split("\n")[2][1:].strip()
        return description, installer_type, deploy_scenarios

    def _format_print(self, testcase_list):
        '''format output'''

        print_hbar(88)
        print("| %-21s | %-60s" % ("Testcase Name", "Description"))
        print_hbar(88)
        for testcase_record in testcase_list:
            print "| %-16s | %-60s" % (testcase_record['Name'],
                                       testcase_record['Description'])
        print_hbar(88)
