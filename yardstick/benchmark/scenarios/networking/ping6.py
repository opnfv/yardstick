##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import pkg_resources
import logging

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Ping6(base.Scenario):  # pragma: no cover
    """Execute ping6 between two hosts

    read link below for more ipv6 info description:
    http://wiki.opnfv.org/ipv6_opnfv_project
    """
    __scenario_type__ = "Ping6"

    TARGET_SCRIPT = 'ping6_benchmark.bash'
    PRE_SETUP_SCRIPT = 'ping6_pre_setup.bash'
    SETUP_SCRIPT = 'ping6_setup.bash'
    SETUP_ODL_SCRIPT = 'ping6_setup_with_odl.bash'
    FIND_HOST_SCRIPT = 'ping6_find_host.bash'
    TEARDOWN_SCRIPT = 'ping6_teardown.bash'
    METADATA_SCRIPT = 'ping6_metadata.txt'
    RADVD_SCRIPT = 'ping6_radvd.conf'
    POST_TEARDOWN_SCRIPT = 'ping6_post_teardown.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False
        self.run_done = False

    def _pre_setup(self):
        for node_name in self.host_list:
            self._ssh_host(node_name)
            self.client.run("cat > ~/pre_setup.sh",
                            stdin=open(self.pre_setup_script, "rb"))
            status, stdout, stderr = self.client.execute(
                "sudo bash pre_setup.sh")

    def _ssh_host(self, node_name):
        # ssh host
        print node_name
        nodes = self.context_cfg['nodes']
        node = nodes.get(node_name, None)
        host_user = node.get('user', 'ubuntu')
        host_ip = node.get('ip', None)
        host_pwd = node.get('password', 'root')
        LOG.debug("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip, password=host_pwd)
        self.client.wait(timeout=600)

    def setup(self):
        '''scenario setup'''
        self.setup_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.SETUP_SCRIPT)

        self.setup_odl_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.SETUP_ODL_SCRIPT)

        self.pre_setup_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.PRE_SETUP_SCRIPT)

        self.ping6_metadata_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.METADATA_SCRIPT)

        self.ping6_radvd_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.RADVD_SCRIPT)

        options = self.scenario_cfg['options']
        host_str = options.get("host", 'host1')
        self.host_list = host_str.split(',')
        self.host_list.sort()
        pre_setup = options.get("pre_setup", True)
        if pre_setup:
            self._pre_setup()

        # ssh host1
        self._ssh_host(self.host_list[0])

        self.client.run("cat > ~/metadata.txt",
                        stdin=open(self.ping6_metadata_script, "rb"))

        # run script to setup ipv6 with nosdn or odl
        sdn = options.get("sdn", 'nosdn')
        if 'odl' in sdn:
            self.client.run("cat > ~/br-ex.radvd.conf",
                            stdin=open(self.ping6_radvd_script, "rb"))
            self.client.run("cat > ~/setup_odl.sh",
                            stdin=open(self.setup_odl_script, "rb"))
            cmd = "sudo bash setup_odl.sh"
        else:
            self.client.run("cat > ~/setup.sh",
                            stdin=open(self.setup_script, "rb"))
            cmd = "sudo bash setup.sh"

        status, stdout, stderr = self.client.execute(cmd)

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""
        # ssh vm1
        self.ping6_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.TARGET_SCRIPT)

        self.ping6_find_host_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.FIND_HOST_SCRIPT)

        if not self.setup_done:
            options = self.scenario_cfg['options']
            host_str = options.get("host", 'host1')
            self.host_list = host_str.split(',')
            self.host_list.sort()
            self._ssh_host(self.host_list[0])

        # find ipv4-int-network1 to ssh VM
        self.client.run("cat > ~/find_host.sh",
                        stdin=open(self.ping6_find_host_script, "rb"))
        cmd = "sudo bash find_host.sh"
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        host_name = stdout.strip()

        # copy vRouterKey to target host
        self.client.run("cat ~/vRouterKey",
                        stdout=open("/tmp/vRouterKey", "w"))
        self._ssh_host(host_name)
        self.client.run("cat > ~/vRouterKey",
                        stdin=open("/tmp/vRouterKey", "rb"))

        # run ping6 benchmark
        self.client.run("cat > ~/ping6.sh",
                        stdin=open(self.ping6_script, "rb"))
        cmd = "sudo bash ping6.sh"
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        # sla
        if stdout:
            result["rtt"] = float(stdout)
            if "sla" in self.scenario_cfg:
                sla_max_rtt = int(self.scenario_cfg["sla"]["max_rtt"])
                assert result["rtt"] <= sla_max_rtt, \
                    "rtt %f > sla:max_rtt(%f); " % (result["rtt"], sla_max_rtt)
        else:
            LOG.error("ping6 timeout")
        self.run_done = True

    def teardown(self):
        """teardown the benchmark"""

        self.post_teardown_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.POST_TEARDOWN_SCRIPT)

        options = self.scenario_cfg['options']
        host_str = options.get("host", 'node1')
        self.host_list = host_str.split(',')
        self.host_list.sort()

        if not self.run_done:
            self._ssh_host(self.host_list[0])

        self.teardown_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.TEARDOWN_SCRIPT)
        self.client.run("cat > ~/teardown.sh",
                        stdin=open(self.teardown_script, "rb"))
        cmd = "sudo bash teardown.sh"
        status, stdout, stderr = self.client.execute(cmd)

        post_teardown = options.get("post_teardown", True)
        if post_teardown:
            self._post_teardown()

        if status:
            raise RuntimeError(stderr)

        if stdout:
            pass
        else:
            LOG.error("ping6 teardown failed")

    def _post_teardown(self):
        for node_name in self.host_list:
            self._ssh_host(node_name)
            self.client.run("cat > ~/post_teardown.sh",
                            stdin=open(self.post_teardown_script, "rb"))
            status, stdout, stderr = self.client.execute(
                "sudo bash post_teardown.sh")
