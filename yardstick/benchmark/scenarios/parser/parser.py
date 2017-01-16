##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import print_function
from __future__ import absolute_import
import pkg_resources
import logging
import subprocess
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Parser(base.Scenario):
    """running Parser Yang-to-Tosca module as a tool
    validating output against expected outcome

    more info https://wiki.opnfv.org/parser
    """
    __scenario_type__ = "Parser"

    SETUP_SCRIPT = "parser_setup.sh"
    TEARDOWN_SCRIPT = "parser_teardown.sh"
    PARSER_SCRIPT = "parser.sh"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.setup_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.parser",
            Parser.SETUP_SCRIPT)
        cmd = "%s" % (self.setup_script)

        subprocess.call(cmd, shell=True)

        self.setup_done = True

    def run(self, result):
        """execute the translation"""
        options = self.scenario_cfg['options']
        yangfile = options.get("yangfile", '~/yardstick/samples/yang.yaml')
        toscafile = options.get("toscafile", '~/yardstick/samples/tosca.yaml')

        self.parser_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.parser",
            Parser.PARSER_SCRIPT)

        if not self.setup_done:
            self.setup()

        cmd1 = "%s %s %s" % (self.parser_script, yangfile, toscafile)
        cmd2 = "chmod 777 %s" % (self.parser_script)
        subprocess.call(cmd2, shell=True)
        p = subprocess.Popen(cmd1, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        p.communicate()
        print("yangtotosca finished")

        result['yangtotosca'] = "success" if p.returncode == 0 else "fail"

    def teardown(self):
        """ for scenario teardown remove parser and pyang """
        self.teardown_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.parser",
            Parser.TEARDOWN_SCRIPT)
        subprocess.call(self.teardown_script, shell=True)
        self.teardown_done = True


def _test():
    """internal test function"""
    pass


if __name__ == '__main__':
    _test()
