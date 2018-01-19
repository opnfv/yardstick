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
from __future__ import print_function

import os
import tarfile
import shutil
import logging

from yardstick.common.task_template import TaskTemplate
from yardstick.common import constants as consts
from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)


class Testcase(object):
    """Testcase commands.

       Set of commands to discover and display test cases.
    """
    ANSIBLE_BACKUP = os.path.join(consts.EXTENDED_REPOS_DIR, 'ansible_bak/')
    EXTENDED_SCENARIO_DIR = os.path.join(consts.YARDSTICK_ROOT_PATH, 'yardstick/benchmark/scenarios/extended/')

    def list_all(self, args):
        """List existing test cases"""

        testcase_files = self._get_testcase_file_list()
        testcase_list = [self._get_record(f) for f in testcase_files]

        return testcase_list

    def _get_testcase_file_list(self):
        try:
            testcase_files = sorted(os.listdir(consts.TESTCASE_DIR))
        except OSError:
            LOG.exception('Failed to list dir:\n%s\n', consts.TESTCASE_DIR)
            raise

        return testcase_files

    def _get_record(self, testcase_file):

        file_path = os.path.join(consts.TESTCASE_DIR, testcase_file)
        with open(file_path) as f:
            try:
                testcase_info = f.read()
            except IOError:
                LOG.exception('Failed to load test case:\n%s\n', testcase_file)
                raise

        description, installer, deploy_scenarios = self._parse_testcase(
            testcase_info)

        record = {
            'Name': testcase_file.split(".")[0],
            'Description': description,
            'installer': installer,
            'deploy_scenarios': deploy_scenarios
        }

        return record

    def _parse_testcase(self, testcase_info):

        rendered_testcase = TaskTemplate.render(testcase_info)
        testcase_cfg = yaml_load(rendered_testcase)

        test_precondition = testcase_cfg.get('precondition', {})
        installer_type = test_precondition.get('installer_type', 'all')
        deploy_scenarios = test_precondition.get('deploy_scenarios', 'all')

        description = self._get_description(testcase_cfg)

        return description, installer_type, deploy_scenarios

    def _get_description(self, testcase_cfg):
        try:
            description_list = testcase_cfg['description'].split(';')
        except KeyError:
            return ''
        else:
            try:
                return description_list[1].replace(os.linesep, '').strip()
            except IndexError:
                return description_list[0].replace(os.linesep, '').strip()

    def show(self, args):
        """Show details of a specific test case"""
        testcase_name = args.casename[0]
        testcase_path = os.path.join(consts.TESTCASE_DIR,
                                     testcase_name + ".yaml")
        with open(testcase_path) as f:
            try:
                testcase_info = f.read()
            except IOError:
                LOG.exception('Failed to load test case:\n%s\n', testcase_path)
                raise

            print(testcase_info)
        return True

    def enable(self, args):
        """Enable extended test cases"""
        testcase_tar_file = args.input_file[0]

        if not os.path.exists(testcase_tar_file):
            LOG.info('Test case tar file not found!')
        elif not testcase_tar_file.endswith('.tar'):
            LOG.info('Test case tar file not in correct format!')
        else:
            testcase_tar = tarfile.open(testcase_tar_file, 'r')
            LOG.info('Extracting test case tar file to %s ...', consts.EXTENDED_REPOS_DIR)
            testcase_tar.extractall(consts.EXTENDED_REPOS_DIR)
            testcase_tar.close()

        # copy test case yaml and test suite yaml files to Yardstick repo
        extended_testcase_src = os.path.join(consts.EXTENDED_REPOS_DIR, 'tests/opnfv/test_cases/')
        LOG.info('Copying test case yaml files to Yardstick repo...')
        shutil.copytree(extended_testcase_src, consts.EXTENDED_TESTCASE_DIR)
        extended_testsuite_src = os.path.join(consts.EXTENDED_REPOS_DIR, 'tests/opnfv/test_suites/')
        LOG.info('Copying test suite yaml files to Yardstick repo...')
        shutil.copytree(extended_testsuite_src, consts.EXTENDED_TESTSUITE_DIR)

        # copy scenario py files to Yardstick repo
        extended_scenario_src = os.path.join(consts.EXTENDED_REPOS_DIR, 'yardstick/benchmark/scenarios/')
        LOG.info('Copying scenario py files to Yardstick repo...')
        shutil.copytree(extended_scenario_src, self.EXTENDED_SCENARIO_DIR)

        # backup Yardstick repo's ansible folder first
        # the copy ansible scripts to Yardstick repo
        shutil.copytree(consts.ANSIBLE_DIR, self.ANSIBLE_BACKUP)
        extended_ansible_src = os.path.join(consts.EXTENDED_REPOS_DIR, 'ansible/')
        LOG.info('Copying ansible scripts to Yardstick repo...')
        cmd = "cp -r %s %s" % (extended_ansible_src, consts.YARDSTICK_ROOT_PATH)
        os.system(cmd)

        # TODO:support extended test case docs to Yardstick repo

        LOG.info('Complete!')
        return True

    def disable(self):
        """Disable extended test cases"""

        # remove ansible scripts
        LOG.info('Removing ansible scripts from Yardstick repo...')
        shutil.rmtree(consts.ANSIBLE_DIR)
        shutil.copytree(self.ANSIBLE_BACKUP, consts.ANSIBLE_DIR)

        # remove consts.EXTENDED_TESTCASE_DIR
        LOG.info('Removing test case yaml files from Yardstick repo...')
        shutil.rmtree(consts.EXTENDED_TESTCASE_DIR)

        # remove consts.EXTENDED_TESTSUITE_DIR
        LOG.info('Removing test suite yaml files from Yardstick repo...')
        shutil.rmtree(consts.EXTENDED_TESTSUITE_DIR)

        # remove EXTENDED_SCENARIO_DIR
        LOG.info('Removing scenario py files from Yardstick repo...')
        shutil.rmtree(self.EXTENDED_SCENARIO_DIR)

        # remove consts.EXTENDED_REPOS_DIR
        LOG.info('Removing extended yardstick repo...')
        shutil.rmtree(consts.EXTENDED_REPOS_DIR)

        LOG.info('Complete!')
        return True
