##############################################################################
# Copyright (c) 2017 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import logging
import subprocess

import pkg_resources
from six.moves import range

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base
from yardstick.benchmark.scenarios.networking import sfc_openstack

LOG = logging.getLogger(__name__)


class Sfc(base.Scenario):  # pragma: no cover
    """ SFC scenario class """

    __scenario_type__ = "sfc"

    PRE_SETUP_SCRIPT = 'sfc_pre_setup.bash'
    TACKER_SCRIPT = 'sfc_tacker.bash'
    SERVER_SCRIPT = 'sfc_server.bash'
    TEARDOWN_SCRIPT = "sfc_teardown.bash"
    TACKER_CHANGECLASSI = "sfc_change_classi.bash"

    def __init__(self, scenario_cfg, context_cfg):  # pragma: no cover
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False
        self.teardown_done = False

    def setup(self):
        """scenario setup"""
        self.tacker_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Sfc.TACKER_SCRIPT)

        self.server_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Sfc.SERVER_SCRIPT)

        """ calling Tacker to instantiate VNFs and Service Chains """
        cmd_tacker = "%s" % (self.tacker_script)
        subprocess.call(cmd_tacker, shell=True)

        target = self.context_cfg['target']

        """ webserver start automatically during the vm boot """
        LOG.info("user:%s, target:%s", target['user'], target['ip'])
        self.server = ssh.SSH.from_node(target, defaults={
            "user": "root", "password": "opnfv"
        })
        self.server.wait(timeout=600)
        self.server._put_file_shell(self.server_script, '~/server.sh')
        cmd_server = "sudo bash server.sh"
        LOG.debug("Executing command: %s", cmd_server)
        status, stdout, stderr = self.server.execute(cmd_server)
        LOG.debug("Output server command: %s", status)

        ips = sfc_openstack.get_an_IP()

        target = self.context_cfg['target']

        LOG.info("user:%s, target:%s", target['user'], target['ip'])
        self.server = ssh.SSH.from_node(
            target,
            defaults={"user": "root", "password": "opnfv"},
            # we must override ip
            overrides={"ip": ips[0]}
        )
        self.server.wait(timeout=600)
        cmd_SF1 = ("nohup python vxlan_tool.py -i eth0 "
                   "-d forward -v off -b 80 &")
        LOG.debug("Starting HTTP firewall in SF1")
        self.server.execute(cmd_SF1)
        result = self.server.execute("ps lax | grep python")
        if "vxlan_tool.py" in result[1]:  # pragma: no cover
            LOG.debug("HTTP firewall started")

        LOG.info("user:%s, target:%s", target['user'], target['ip'])
        self.server = ssh.SSH.from_node(
            target,
            defaults={"user": "root", "password": "opnfv"},
            # we must override ip
            overrides={"ip": ips[1]}
        )
        self.server.wait(timeout=600)
        cmd_SF2 = ("nohup python vxlan_tool.py -i eth0 "
                   "-d forward -v off -b 22 &")
        LOG.debug("Starting SSH firewall in SF2")
        self.server.execute(cmd_SF2)

        result = self.server.execute("ps lax | grep python")
        if "vxlan_tool.py" in result[1]:  # pragma: no cover
            LOG.debug("SSH firewall started")

        self.setup_done = True

    def run(self, result):
        """ Creating client and server VMs to perform the test"""
        host = self.context_cfg['host']

        LOG.info("user:%s, host:%s", host['user'], host['ip'])
        self.client = ssh.SSH.from_node(host, defaults={
            "user": "root", "password": "opnfv"
        })
        self.client.wait(timeout=600)

        if not self.setup_done:  # pragma: no cover
            self.setup()

        target = self.context_cfg['target']
        target_ip = target.get('ip', None)

        cmd_client = "nc -w 5 -zv " + target_ip + " 22"
        result = self.client.execute(cmd_client)

        i = 0
        if "timed out" in result[2]:  # pragma: no cover
            LOG.info('\033[92m' + "TEST 1 [PASSED] "
                     "==> SSH BLOCKED" + '\033[0m')
            i = i + 1
        else:  # pragma: no cover
            LOG.debug('\033[91m' + "TEST 1 [FAILED] "
                      "==> SSH NOT BLOCKED" + '\033[0m')
            return

        cmd_client = "nc -w 5 -zv " + target_ip + " 80"
        LOG.info("Executing command: %s", cmd_client)
        result = self.client.execute(cmd_client)
        if "succeeded" in result[2]:  # pragma: no cover
            LOG.info('\033[92m' + "TEST 2 [PASSED] "
                     "==> HTTP WORKS" + '\033[0m')
            i = i + 1
        else:  # pragma: no cover
            LOG.debug('\033[91m' + "TEST 2 [FAILED] "
                      "==> HTTP BLOCKED" + '\033[0m')
            return

        self.tacker_classi = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Sfc.TACKER_CHANGECLASSI)

        """ calling Tacker to change the classifier """
        cmd_tacker = "%s" % (self.tacker_classi)
        subprocess.call(cmd_tacker, shell=True)

        cmd_client = "nc -w 5 -zv " + target_ip + " 80"
        LOG.info("Executing command: %s", cmd_client)
        result = self.client.execute(cmd_client)
        LOG.info("Output client command: %s", result)
        if "timed out" in result[2]:  # pragma: no cover
            LOG.info('\033[92m' + "TEST 3 [WORKS] "
                     "==> HTTP BLOCKED" + '\033[0m')
            i = i + 1
        else:  # pragma: no cover
            LOG.debug('\033[91m' + "TEST 3 [FAILED] "
                      "==> HTTP NOT BLOCKED" + '\033[0m')
            return

        cmd_client = "nc -zv " + target_ip + " 22"
        result = self.client.execute(cmd_client + " \r")
        LOG.debug(result)

        if "succeeded" in result[2]:  # pragma: no cover
            LOG.info('\033[92m' + "TEST 4 [WORKS] "
                     "==> SSH WORKS" + '\033[0m')
            i = i + 1
        else:  # pragma: no cover
            LOG.debug('\033[91m' + "TEST 4 [FAILED] "
                      "==> SSH BLOCKED" + '\033[0m')
            return

        if i == 4:  # pragma: no cover
            for x in range(0, 5):
                LOG.info('\033[92m' + "SFC TEST WORKED"
                         " :) \n" + '\033[0m')

    def teardown(self):
        """ for scenario teardown remove tacker VNFs, chains and classifiers"""
        self.teardown_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.networking",
            Sfc.TEARDOWN_SCRIPT)
        subprocess.call(self.teardown_script, shell=True)
        self.teardown_done = True


"""def _test():  # pragma: no cover

    internal test function
    logger = logging.getLogger("Sfc Yardstick")
    logger.setLevel(logging.DEBUG)

    result = {}

    sfc = Sfc(scenario_cfg, context_cfg)
    sfc.setup()
    sfc.run(result)
    print(result)
    sfc.teardown()

if __name__ == '__main__':  # pragma: no cover
    _test()"""
