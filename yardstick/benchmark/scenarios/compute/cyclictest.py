##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
from __future__ import print_function

import logging
import os
import re
import time

import pkg_resources
from oslo_serialization import jsonutils

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class Cyclictest(base.Scenario):
    """Execute cyclictest benchmark on guest vm

  Parameters
    affinity - run thread #N on processor #N, if possible
        type:    int
        unit:    na
        default: 1
    interval - base interval of thread
        type:    int
        unit:    us
        default: 1000
    loops - number of loops, 0 for endless
        type:    int
        unit:    na
        default: 1000
    priority - priority of highest prio thread
        type:    int
        unit:    na
        default: 99
    threads - number of threads
        type:    int
        unit:    na
        default: 1
    histogram - dump a latency histogram to stdout after the run
                here set the max time to be tracked
        type:    int
        unit:    ms
        default: 90

    Read link below for more fio args description:
        https://rt.wiki.kernel.org/index.php/Cyclictest
    """
    __scenario_type__ = "Cyclictest"

    TARGET_SCRIPT = "cyclictest_benchmark.bash"
    WORKSPACE = "/root/workspace/"
    REBOOT_CMD_PATTERN = r";\s*reboot\b"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def _put_files(self, client):
        setup_options = self.scenario_cfg["setup_options"]
        rpm_dir = setup_options["rpm_dir"]
        script_dir = setup_options["script_dir"]
        image_dir = setup_options["image_dir"]
        LOG.debug("Send RPMs from %s to workspace %s",
                  rpm_dir, self.WORKSPACE)
        client.put(rpm_dir, self.WORKSPACE, recursive=True)
        LOG.debug("Send scripts from %s to workspace %s",
                  script_dir, self.WORKSPACE)
        client.put(script_dir, self.WORKSPACE, recursive=True)
        LOG.debug("Send guest image from %s to workspace %s",
                  image_dir, self.WORKSPACE)
        client.put(image_dir, self.WORKSPACE, recursive=True)

    def _connect_host(self):
        host = self.context_cfg["host"]

        self.host = ssh.SSH.from_node(host, defaults={"user": "root"})
        self.host.wait(timeout=600)

    def _connect_guest(self):
        host = self.context_cfg["host"]
        # why port 5555?
        self.guest = ssh.SSH.from_node(host,
                                       defaults={
                                           "user": "root", "ssh_port": 5555
                                       })
        self.guest.wait(timeout=600)

    def _run_setup_cmd(self, client, cmd):
        LOG.debug("Run cmd: %s", cmd)
        status, stdout, stderr = client.execute(cmd)
        if status:
            if re.search(self.REBOOT_CMD_PATTERN, cmd):
                LOG.debug("Error on reboot")
            else:
                raise RuntimeError(stderr)

    def _run_host_setup_scripts(self, scripts):
        setup_options = self.scenario_cfg["setup_options"]
        script_dir = os.path.basename(setup_options["script_dir"])

        for script in scripts:
            cmd = "cd %s/%s; export PATH=./:$PATH; %s" %\
                  (self.WORKSPACE, script_dir, script)
            self._run_setup_cmd(self.host, cmd)

            if re.search(self.REBOOT_CMD_PATTERN, cmd):
                time.sleep(3)
                self._connect_host()

    def _run_guest_setup_scripts(self, scripts):
        setup_options = self.scenario_cfg["setup_options"]
        script_dir = os.path.basename(setup_options["script_dir"])

        for script in scripts:
            cmd = "cd %s/%s; export PATH=./:$PATH; %s" %\
                  (self.WORKSPACE, script_dir, script)
            self._run_setup_cmd(self.guest, cmd)

            if re.search(self.REBOOT_CMD_PATTERN, cmd):
                time.sleep(3)
                self._connect_guest()

    def setup(self):
        """scenario setup"""
        setup_options = self.scenario_cfg["setup_options"]
        host_setup_seqs = setup_options["host_setup_seqs"]
        guest_setup_seqs = setup_options["guest_setup_seqs"]

        self._connect_host()
        self._put_files(self.host)
        self._run_host_setup_scripts(host_setup_seqs)

        self._connect_guest()
        self._put_files(self.guest)
        self._run_guest_setup_scripts(guest_setup_seqs)

        # copy script to host
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Cyclictest.TARGET_SCRIPT)
        self.guest._put_file_shell(
            self.target_script, '~/cyclictest_benchmark.sh')

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""
        default_args = "-m -n -q --notrace"

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg["options"]
        affinity = options.get("affinity", 1)
        breaktrace = options.get("breaktrace", 1000)
        interval = options.get("interval", 1000)
        priority = options.get("priority", 99)
        loops = options.get("loops", 1000)
        threads = options.get("threads", 1)
        histogram = options.get("histogram", 90)

        cmd_args = "-a %s -b %s -i %s -p %s -l %s -t %s -h %s %s" \
                   % (affinity, breaktrace, interval, priority, loops,
                      threads, histogram, default_args)
        cmd = "bash cyclictest_benchmark.sh %s" % (cmd_args)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.guest.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        result.update(jsonutils.loads(stdout))

        if "sla" in self.scenario_cfg:
            sla_error = ""
            for t, latency in result.items():
                if 'max_%s_latency' % t not in self.scenario_cfg['sla']:
                    continue

                sla_latency = int(self.scenario_cfg['sla'][
                                  'max_%s_latency' % t])
                latency = int(latency)
                if latency > sla_latency:
                    sla_error += "%s latency %d > sla:max_%s_latency(%d); " % \
                        (t, latency, t, sla_latency)
            assert sla_error == "", sla_error


def _test():    # pragma: no cover
    """internal test function"""
    key_filename = pkg_resources.resource_filename("yardstick.resources",
                                                   "files/yardstick_key")
    ctx = {
        "host": {
            "ip": "10.229.47.137",
            "user": "root",
            "key_filename": key_filename
        }
    }

    logger = logging.getLogger("yardstick")
    logger.setLevel(logging.DEBUG)

    options = {
        "affinity": 2,
        "breaktrace": 1000,
        "interval": 100,
        "priority": 88,
        "loops": 10000,
        "threads": 2,
        "histogram": 80
    }
    sla = {
        "max_min_latency": 100,
        "max_avg_latency": 500,
        "max_max_latency": 1000,
    }
    args = {
        "options": options,
        "sla": sla
    }
    result = {}

    cyclictest = Cyclictest(args, ctx)
    cyclictest.run(result)
    print(result)


if __name__ == '__main__':    # pragma: no cover
    _test()
