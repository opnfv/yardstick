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

import logging

import pkg_resources
from oslo_serialization import jsonutils

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


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
        host_user = host.get('user', 'ubuntu')
        host_ssh_port = host.get('ssh_port', ssh.DEFAULT_PORT)
        host_ip = host.get('ip', None)
        host_key_filename = host.get('key_filename', '~/.ssh/id_rsa')
        target = self.context_cfg['target']
        target_user = target.get('user', 'ubuntu')
        target_ssh_port = target.get('ssh_port', ssh.DEFAULT_PORT)
        target_ip = target.get('ip', None)
        target_key_filename = target.get('key_filename', '~/.ssh/id_rsa')

        LOG.info("user:%s, target:%s", target_user, target_ip)
        self.server = ssh.SSH(target_user, target_ip,
                              key_filename=target_key_filename,
                              port=target_ssh_port)
        self.server.wait(timeout=600)

        LOG.info("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip,
                              key_filename=host_key_filename,
                              port=host_ssh_port)
        self.client.wait(timeout=600)

        # copy script to host
        self.client._put_file_shell(self.target_script, '~/pktgen.sh')

        self.setup_done = True

    def multiqueue_setup(self):
        '''multiqueue setup'''
        if not self._is_irqbalance_disabled():
            self._disable_irqbalance()

        vnic_type = self._get_vnic_type()
        if "ixgbevf" in vnic_type:
            self.vnic_type = "ixgbevf"
            self.queue_number = self._get_sriov_queue_number()
            self._setup_irqmapping_sriov(self.queue_number)
        else:
            self.vnic_type = "ovs"
            self.queue_number = self._enable_ovs_multiqueue()
            self._setup_irqmapping_ovs(self.queue_number)

        self.multiqueue_setup_done = True

    def _get_vnic_type(self):
        cmd = "ethtool -i eth0 | grep driver | awk '{print $2}'"
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        return (stdout)

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

            cmd = "echo $((1<<%s)) | sudo tee /proc/irq/%s/smp_affinity" \
                % (i, int(stdout))
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

            cmd = "echo $((1<<%s)) | sudo tee /proc/irq/%s/smp_affinity" \
                % (i, int(stdout))
            status, stdout, stderr = self.server.execute(cmd)
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)

    def _setup_irqmapping_sriov(self, queue_number):
        cmd = "grep 'eth0-TxRx-0' /proc/interrupts |" \
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
            cmd = "grep 'eth0-TxRx-%s' /proc/interrupts |" \
                  "awk '{match($0,/ +[0-9]+/)} " \
                  "{print substr($1,RSTART,RLENGTH-1)}'" % (i)
            status, stdout, stderr = self.server.execute(cmd)
            if status:
                raise RuntimeError(stderr)

            cmd = "echo $((1<<%s)) | sudo tee /proc/irq/%s/smp_affinity" \
                % (i, int(stdout))
            status, stdout, stderr = self.server.execute(cmd)
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)

    def _get_sriov_queue_number(self):
        """Get queue number from server as both VMs are the same"""
        cmd = "grep eth0-TxRx- /proc/interrupts | wc -l"
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        return int(stdout)

    def _get_available_queue_number(self):
        """Get queue number from client as both VMs are the same"""
        cmd = "sudo ethtool -l eth0 | grep Combined | head -1 |" \
              "awk '{printf $2}'"
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        return int(stdout)

    def _get_usable_queue_number(self):
        """Get queue number from client as both VMs are the same"""
        cmd = "sudo ethtool -l eth0 | grep Combined | tail -1 |" \
              "awk '{printf $2}'"
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
            cmd = "sudo ethtool -L eth0 combined %s" % available_queue_number
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
        status, _, stderr = self.server.execute(cmd)
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
        if self.vnic_type == "ovs" and not ovs_dpdk and queue_number > 1:
            queue_number = queue_number / 2

        cmd = "sudo bash pktgen.sh %s %s %s %s %s %s" \
            % (ipaddr, self.number_of_ports, packetsize,
               duration, queue_number, pps)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        result.update(jsonutils.loads(stdout))

        result['packets_received'] = self._iptables_get_result()
        result['packetsize'] = packetsize

        if "sla" in self.scenario_cfg:
            sent = result['packets_sent']
            received = result['packets_received']
            ppm = 1000000 * (sent - received) / sent
            # Added by Jing
            ppm += (sent - received) % sent > 0
            LOG.debug("Lost packets %d - Lost ppm %d", (sent - received), ppm)
            sla_max_ppm = int(self.scenario_cfg["sla"]["max_ppm"])
            assert ppm <= sla_max_ppm, "ppm %d > sla_max_ppm %d; " \
                % (ppm, sla_max_ppm)


def _test():
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
