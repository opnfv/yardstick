##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
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
        self.nodes = context_cfg['nodes']
        self.options = scenario_cfg['options']
        self.setup_done = False
        self.run_done = False
        self.external_network = self.options.get("external_network", "ext-net")
        self.ping_options = "-s %s -c %s" % \
            (self.options.get("packetsize", '56'),
             self.options.get("ping_count", '5'))
        self.openrc = self.options.get("openrc", "/opt/admin-openrc.sh")

    def _ssh_host(self, node_name):
        # ssh host
        node = self.nodes.get(node_name, None)
        self.client = ssh.SSH.from_node(node, defaults={"user": "ubuntu"})
        self.client.wait(timeout=60)

    def _pre_setup(self):
        for node_name in self.host_list:
            self._ssh_host(node_name)
            self.client._put_file_shell(
                self.pre_setup_script, '~/pre_setup.sh')
            status, stdout, stderr = self.client.execute(
                "sudo bash pre_setup.sh")

    def _get_controller_node(self, host_list):
        for host_name in host_list:
            node = self.nodes.get(host_name, None)
            node_role = node.get('role', None)
            if node_role == 'Controller':
                return host_name
        return None

    def setup(self):
        """scenario setup"""
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

        host_str = self.options.get("host", 'host1')
        self.host_list = host_str.split(',')
        self.host_list.sort()
        pre_setup = self.options.get("pre_setup", True)
        if pre_setup:
            self._pre_setup()

        # log in a contronller node to setup
        controller_node_name = self._get_controller_node(self.host_list)
        LOG.debug("The Controller Node is: %s", controller_node_name)
        if controller_node_name is None:
            LOG.exception("Can't find controller node in the context!!!")
        self._ssh_host(controller_node_name)
        self.client._put_file_shell(
            self.ping6_metadata_script, '~/metadata.txt')

        # run script to setup ipv6 with nosdn or odl
        sdn = self.options.get("sdn", 'nosdn')
        if 'odl' in sdn:
            self.client._put_file_shell(
                self.ping6_radvd_script, '~/br-ex.radvd.conf')
            self.client._put_file_shell(
                self.setup_odl_script, '~/setup_odl.sh')
            setup_bash_file = "setup_odl.sh"
        else:
            self.client._put_file_shell(self.setup_script, '~/setup.sh')
            setup_bash_file = "setup.sh"
        cmd = "sudo bash %s %s %s" % \
              (setup_bash_file, self.openrc, self.external_network)
        LOG.debug("Executing setup command: %s", cmd)
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
            host_str = self.options.get("host", 'host1')
            self.host_list = host_str.split(',')
            self.host_list.sort()
            self._ssh_host(self.host_list[0])

        # find ipv4-int-network1 to ssh VM
        self.client._put_file_shell(
            self.ping6_find_host_script, '~/find_host.sh')
        cmd = "sudo bash find_host.sh %s" % self.openrc
        LOG.debug("Executing find_host command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        host_name = stdout.strip()

        # copy vRouterKey to target host
        self.client.run("cat ~/vRouterKey",
                        stdout=open("/tmp/vRouterKey", "w"))
        self._ssh_host(host_name)
        self.client.run("cat > ~/vRouterKey",
                        stdin=open("/tmp/vRouterKey", "rb"))

        # run ping6 benchmark
        self.client._put_file_shell(self.ping6_script, '~/ping6.sh')
        cmd = "sudo bash ping6.sh %s %s" % (self.openrc, self.ping_options)
        LOG.debug("Executing ping6 command: %s", cmd)
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
            LOG.error("ping6 timeout!!!")
        self.run_done = True

    def teardown(self):
        """teardown the benchmark"""

        self.post_teardown_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.POST_TEARDOWN_SCRIPT)

        host_str = self.options.get("host", 'node1')
        self.host_list = host_str.split(',')
        self.host_list.sort()

        if not self.run_done:
            self._ssh_host(self.host_list[0])

        self.teardown_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.TEARDOWN_SCRIPT)
        self.client._put_file_shell(self.teardown_script, '~/teardown.sh')
        cmd = "sudo bash teardown.sh %s %s" % \
              (self.openrc, self.external_network)
        status, stdout, stderr = self.client.execute(cmd)

        post_teardown = self.options.get("post_teardown", True)
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
            self.client._put_file_shell(
                self.post_teardown_script, '~/post_teardown.sh')
            status, stdout, stderr = self.client.execute(
                "sudo bash post_teardown.sh")
