##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
from __future__ import print_function

import os
import logging
import math

import pkg_resources
from oslo_serialization import jsonutils

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)

SSH_TIMEOUT = 60
VNIC_TYPE_LIST = ["ovs", "sriov"]
SRIOV_DRIVER_LIST = ["ixgbevf", "i40evf"]


class Pktgen(base.Scenario):
    """Execute pktgen between two hosts

  Parameters
    packetsize - packet size in bytes without the CRC
        type:    int
        unit:    bytes
        default: 60
    number_of_ports - number of UDP ports to test
        type:    int
        unit:    na
        default: 10
    duration - duration of the test
        type:    int
        unit:    seconds
        default: 20
    """
    __scenario_type__ = "Pktgen"

    TARGET_SCRIPT = 'pktgen_benchmark.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.vnic_name = "eth0"
        self.vnic_type = "ovs"
        self.queue_number = 1
        self.setup_done = False
        self.multiqueue_setup_done = False

    def setup(self):
        """scenario setup"""
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Pktgen.TARGET_SCRIPT)
        host = self.context_cfg['host']
        target = self.context_cfg['target']

        LOG.info("user:%s, target:%s", target['user'], target['ip'])
        self.server = ssh.SSH.from_node(target, defaults={"user": "ubuntu"})
        self.server.wait(timeout=600)

        LOG.info("user:%s, host:%s", host['user'], host['ip'])
        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        # copy script to host
        self.client._put_file_shell(self.target_script, '~/pktgen.sh')

        self.setup_done = True

    def multiqueue_setup(self):
        # one time setup stuff
        cmd = "sudo sysctl -w net.core.netdev_budget=3000"
        self.server.send_command(cmd)
        self.client.send_command(cmd)

        cmd = "sudo sysctl -w net.core.netdev_max_backlog=100000"
        self.server.send_command(cmd)
        self.client.send_command(cmd)

        """multiqueue setup"""
        if not self._is_irqbalance_disabled():
            self._disable_irqbalance()

        vnic_driver_name = self._get_vnic_driver_name()
        if vnic_driver_name in SRIOV_DRIVER_LIST:
            self.vnic_type = "sriov"

            # one time setup stuff
            cmd = "sudo ethtool -G %s rx 4096 tx 4096" % self.vnic_name
            self.server.send_command(cmd)
            self.client.send_command(cmd)

            self.queue_number = self._get_sriov_queue_number()
            self._setup_irqmapping_sriov(self.queue_number)
        else:
            self.vnic_type = "ovs"
            self.queue_number = self._enable_ovs_multiqueue()
            self._setup_irqmapping_ovs(self.queue_number)

        self.multiqueue_setup_done = True

    def _get_vnic_driver_name(self):
        cmd = "readlink /sys/class/net/%s/device/driver" % self.vnic_name
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        return os.path.basename(stdout.strip())

    def _is_irqbalance_disabled(self):
        """Did we disable irqbalance already in the guest?"""
        is_disabled = False
        cmd = "grep ENABLED /etc/default/irqbalance"
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        if "0" in stdout:
            is_disabled = True

        return is_disabled

    def _disable_irqbalance(self):
        cmd = "sudo sed -i -e 's/ENABLED=\"1\"/ENABLED=\"0\"/g' " \
              "/etc/default/irqbalance"
        status, stdout, stderr = self.server.execute(cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        cmd = "sudo service irqbalance stop"
        status, stdout, stderr = self.server.execute(cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        cmd = "sudo service irqbalance disable"
        status, stdout, stderr = self.server.execute(cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

    def _setup_irqmapping_ovs(self, queue_number):
        cmd = "grep 'virtio0-input.0' /proc/interrupts |" \
              "awk '{match($0,/ +[0-9]+/)} " \
              "{print substr($1,RSTART,RLENGTH-1)}'"
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        cmd = "echo 1 | sudo tee /proc/irq/%s/smp_affinity" % (int(stdout))
        status, stdout, stderr = self.server.execute(cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        cmd = "grep 'virtio0-output.0' /proc/interrupts |" \
              "awk '{match($0,/ +[0-9]+/)} " \
              "{print substr($1,RSTART,RLENGTH-1)}'"
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        cmd = "echo 1 | sudo tee /proc/irq/%s/smp_affinity" % (int(stdout))
        status, stdout, stderr = self.server.execute(cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        if queue_number == 1:
            return

        for i in range(1, queue_number):
            cmd = "grep 'virtio0-input.%s' /proc/interrupts |" \
                  "awk '{match($0,/ +[0-9]+/)} " \
                  "{print substr($1,RSTART,RLENGTH-1)}'" % (i)
            status, stdout, stderr = self.server.execute(cmd)
            if status:
                raise RuntimeError(stderr)

            cmd = "echo %s | sudo tee /proc/irq/%s/smp_affinity" \
                % (1 << i, int(stdout))
            status, stdout, stderr = self.server.execute(cmd)
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)

            cmd = "grep 'virtio0-output.%s' /proc/interrupts |" \
                  "awk '{match($0,/ +[0-9]+/)} " \
                  "{print substr($1,RSTART,RLENGTH-1)}'" % (i)
            status, stdout, stderr = self.server.execute(cmd)
            if status:
                raise RuntimeError(stderr)

            cmd = "echo %s | sudo tee /proc/irq/%s/smp_affinity" \
                % (1 << i, int(stdout))
            status, stdout, stderr = self.server.execute(cmd)
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)

    def _setup_irqmapping_sriov(self, queue_number):
        cmd = "grep '%s-TxRx-0' /proc/interrupts |" \
              "awk '{match($0,/ +[0-9]+/)} " \
              "{print substr($1,RSTART,RLENGTH-1)}'" % self.vnic_name
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        cmd = "echo 1 | sudo tee /proc/irq/%s/smp_affinity" % (int(stdout))
        status, stdout, stderr = self.server.execute(cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        if queue_number == 1:
            return

        for i in range(1, queue_number):
            cmd = "grep '%s-TxRx-%s' /proc/interrupts |" \
                  "awk '{match($0,/ +[0-9]+/)} " \
                  "{print substr($1,RSTART,RLENGTH-1)}'" % (self.vnic_name, i)
            status, stdout, stderr = self.server.execute(cmd)
            if status:
                raise RuntimeError(stderr)

            cmd = "echo %s | sudo tee /proc/irq/%s/smp_affinity" \
                % (1 << i, int(stdout))
            status, stdout, stderr = self.server.execute(cmd)
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)

    def _get_sriov_queue_number(self):
        """Get queue number from server as both VMs are the same"""
        cmd = "grep %s-TxRx- /proc/interrupts | wc -l" % self.vnic_name
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        return int(stdout)

    def _get_available_queue_number(self):
        """Get queue number from client as both VMs are the same"""
        cmd = "sudo ethtool -l %s | grep Combined | head -1 |" \
              "awk '{printf $2}'" % self.vnic_name
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        return int(stdout)

    def _get_usable_queue_number(self):
        """Get queue number from client as both VMs are the same"""
        cmd = "sudo ethtool -l %s | grep Combined | tail -1 |" \
              "awk '{printf $2}'" % self.vnic_name
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        return int(stdout)

    def _enable_ovs_multiqueue(self):
        available_queue_number = self._get_available_queue_number()
        usable_queue_number = self._get_usable_queue_number()
        if available_queue_number > 1 and \
           available_queue_number != usable_queue_number:
            cmd = "sudo ethtool -L %s combined %s" % \
                (self.vnic_name, available_queue_number)
            LOG.debug("Executing command: %s", cmd)
            status, stdout, stderr = self.server.execute(cmd)
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)
        return available_queue_number

    def _iptables_setup(self):
        """Setup iptables on server to monitor for received packets"""
        cmd = "sudo iptables -F; " \
              "sudo iptables -A INPUT -p udp --dport 1000:%s -j DROP" \
              % (1000 + self.number_of_ports)
        LOG.debug("Executing command: %s", cmd)
        status, _, stderr = self.server.execute(cmd, timeout=SSH_TIMEOUT)
        if status:
            raise RuntimeError(stderr)

    def _iptables_get_result(self):
        """Get packet statistics from server"""
        cmd = "sudo iptables -L INPUT -vnx |" \
              "awk '/dpts:1000:%s/ {{printf \"%%s\", $1}}'" \
              % (1000 + self.number_of_ports)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        return int(stdout)

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        ipaddr = self.context_cfg["target"].get("ipaddr", '127.0.0.1')

        options = self.scenario_cfg['options']
        packetsize = options.get("packetsize", 60)
        self.number_of_ports = options.get("number_of_ports", 10)
        self.vnic_name = options.get("vnic_name", "eth0")
        ovs_dpdk = options.get("ovs_dpdk", False)
        pps = options.get("pps", 1000000)
        multiqueue = options.get("multiqueue", False)

        if multiqueue and not self.multiqueue_setup_done:
            self.multiqueue_setup()

        # if run by a duration runner
        duration_time = self.scenario_cfg["runner"].get("duration", None) \
            if "runner" in self.scenario_cfg else None
        # if run by an arithmetic runner
        arithmetic_time = options.get("duration", None)

        if duration_time:
            duration = duration_time
        elif arithmetic_time:
            duration = arithmetic_time
        else:
            duration = 20

        self._iptables_setup()

        queue_number = self.queue_number

        # For native OVS, half of vCPUs are used by vhost kernel threads
        # hence set the queue_number to half number of vCPUs
        # e.g. set queue_number to 2 if there are 4 vCPUs
        if self.vnic_type == "ovs" and not ovs_dpdk and self.queue_number > 1:
            queue_number = self.queue_number / 2

        cmd = "sudo bash pktgen.sh %s %s %s %s %s %s" \
            % (ipaddr, self.number_of_ports, packetsize,
               duration, queue_number, pps)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd, timeout=SSH_TIMEOUT)

        if status:
            raise RuntimeError(stderr)

        result.update(jsonutils.loads(stdout))

        received = result['packets_received'] = self._iptables_get_result()
        sent = result['packets_sent']
        result['packetsize'] = packetsize
        # compatible with python3 /
        ppm = math.ceil(1000000.0 * (sent - received) / sent)

        result['ppm'] = ppm

        if "sla" in self.scenario_cfg:
            LOG.debug("Lost packets %d - Lost ppm %d", (sent - received), ppm)
            sla_max_ppm = int(self.scenario_cfg["sla"]["max_ppm"])
            assert ppm <= sla_max_ppm, "ppm %d > sla_max_ppm %d; " \
                % (ppm, sla_max_ppm)


def _test():  # pragma: no cover
    """internal test function"""
    key_filename = pkg_resources.resource_filename('yardstick.resources',
                                                   'files/yardstick_key')
    ctx = {
        'host': {
            'ip': '10.229.47.137',
            'user': 'root',
            'key_filename': key_filename
        },
        'target': {
            'ip': '10.229.47.137',
            'user': 'root',
            'key_filename': key_filename,
            'ipaddr': '10.229.47.137',
        }
    }

    logger = logging.getLogger('yardstick')
    logger.setLevel(logging.DEBUG)

    options = {'packetsize': 120}
    args = {'options': options}
    result = {}

    p = Pktgen(args, ctx)
    p.run(result)
    print(result)

if __name__ == '__main__':
    _test()
