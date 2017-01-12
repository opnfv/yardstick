##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'testcase' """
import os
import yaml
import sys
import logging

from yardstick.common.task_template import TaskTemplate
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)


class Testcase(object):
    '''Testcase commands.

       Set of commands to discover and display test cases.
    '''
    def list_all(self, args):
        '''List existing test cases'''

        testcase_files = self._get_testcase_file_list()

        testcase_list = [self._get_record(f) for f in testcase_files]

        return testcase_list

    def _get_testcase_file_list(self):
        try:
            testcase_files = os.listdir(consts.TESTCASE_DIR)
        except Exception as e:
            LOG.debug('Failed to list dir:\n{}\n{}\n'.format(
                consts.TESTCASE_DIR, e))
            raise e

        testcase_files.sort()
        return testcase_files

    def _get_record(self, testcase_file):

        try:
            file_path = os.path.join(consts.TESTCASE_DIR, testcase_file)
            with open(file_path) as f:
                try:
                    testcase_info = f.read()
                except IOError as e:
                    LOG.debug('Failed to load test cases:\n%s\n%s\n',
                              testcase_file, e)
                    raise e

                description, installer, deploy_scenarios = \
                    self._parse_testcase(testcase_info)

                record = {
                    'Name': testcase_file.split(".")[0],
                    'Description': description,
                    'installer': installer,
                    'deploy_scenarios': deploy_scenarios
                }

                return record
        except IOError as ioerror:
            sys.exit(ioerror)

    def _parse_testcase(self, testcase_info):

        rendered_testcase = TaskTemplate.render(testcase_info)
        testcase_cfg = yaml.load(rendered_testcase)

        try:
            test_precondition = testcase_cfg['precondition']
            installer_type = test_precondition.get('installer_type', 'all')
            deploy_scenarios = test_precondition.get('deploy_scenarios', 'all')
        except KeyError:
            installer_type = 'all'
            deploy_scenarios = 'all'

        description = self._get_description(testcase_cfg)

        return description, installer_type, deploy_scenarios

    def _get_description(self, testcase_cfg):
        try:
            description_list = testcase_cfg['description'].split(';')
            try:
                return description_list[1].replace('\n', '')
            except IndexError:
                return description_list[0].replace('\n', '')
        except KeyError:
            return ''

    def show(self, args):
        '''Show details of a specific test case'''
        testcase_name = args.casename[0]
        testcase_path = os.path.join(consts.TESTCASE_DIR,
                                     testcase_name + ".yaml")
        try:
            with open(testcase_path) as f:
                try:
                    testcase_info = f.read()
                    print testcase_info

                except IOError as e:
                    LOG.debug('Failed to load test cases:\n%s\n%s\n',
                              testcase_path, e)
                    raise e
        except IOError as ioerror:
            sys.exit(ioerror)
        return True
