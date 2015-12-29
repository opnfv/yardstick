##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import pkg_resources
import logging
import json

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Parser(base.Scenario):
    """running Parser Yang-to-Tosca module as a tool
    validating output against expected outcome

    more info https://wiki.opnfv.org/parser
    """
    __scenario_type__ = "Parser"

    TARGET_SCRIPT = "parser.bash"
    YANG_FILE = "yang.yaml"
    TOSCA_FILE = "tosca.yaml"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.parser",
            Parser.TARGET_SCRIPT)
        self.yangfile = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.parser",
            Parser.YANG_FILE)
        self.toscafile = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.parser",
            Parser.TOSCA_FILE)

        host = self.context_cfg["host"]
        user = host.get("user", "ubuntu")
        ip = host.get("ip", None)
        key_filename = host.     get('key_filename', "~/.ssh/id_rsa")

        LOG.info("user:%s, host:%s", user, ip)
        self.client = ssh.SSH(user, ip, key_filename=key_filename)
        self.client.wait(timeout=600)

        # copy scripts to host
        self.client.run("cat > ~/parser.sh",
                        stdin=open(self.target_script, 'rb'))
        self.client.run("cat > ~/yang.yaml",
                        stdin=open(self.yangfile, 'rb'))
        self.client.run("cat > ~/tosca.yaml",
                        stdin=open(self.toscafile, 'rb'))

        self.setup_done = True

    def run(self, result):
        """execute the translation"""

        if not self.setup_done:
            self.setup()

        cmd_args = ""

        cmd = "sudo bash parser.sh %s" % (cmd_args)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        result.update(json.loads(stdout))


def _test():
    '''internal test function'''
    pass

if __name__ == '__main__':
    _test()
