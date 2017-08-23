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


class QemuMigrate(base.Scenario):
    """
    Execute a live migration for two host using qemu

    """

    __scenario_type__ = "QemuMigrate"

    TARGET_SCRIPT = "qemu_migrate_benchmark.bash"
    WORKSPACE = "/root/workspace"
    REBOOT_CMD_PATTERN = r";\s*reboot\b"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def _connect_host(self):
        host = self.context_cfg["host"]
        self.host = ssh.SSH.from_node(host, defaults={"user": "root"})
        self.host.wait(timeout=600)

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

    def setup(self):
        """scenario setup"""
        setup_options = self.scenario_cfg["setup_options"]
        host_setup_seqs = setup_options["host_setup_seqs"]

        self._connect_host()
        self._put_files(self.host)
        self._run_host_setup_scripts(host_setup_seqs)

        # copy script to host
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            QemuMigrate.TARGET_SCRIPT)
        self.host.put_file(self.target_script, "~/qemu_migrate_benchmark.sh")

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""

        options = self.scenario_cfg["options"]
        smp = options.get("smp", 2)
        qmp_sock_src = options.get("qmp_src_path", "/tmp/qmp-sock-src")
        qmp_sock_dst = options.get("qmp_dst_path", "/tmp/qmp-sock-dst")
        incoming_ip = options.get("incoming_ip", 0)
        migrate_to_port = options.get("migrate_to_port", 4444)
        max_down_time = options.get("max_down_time", 0.10)
        cmd_args = " %s %s %s %s %s %s" %\
                   (smp, qmp_sock_src, qmp_sock_dst, incoming_ip,
                    migrate_to_port, max_down_time)
        cmd = "bash migrate_benchmark.sh %s" % (cmd_args)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.host.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        result.update(jsonutils.loads(stdout))

        if "sla" in self.scenario_cfg:
            sla_error = ""
            for t, timevalue in result.items():
                if 'max_%s' % t not in self.scenario_cfg['sla']:
                    continue

                sla_time = int(self.scenario_cfg['sla'][
                               'max_%s' % t])
                timevalue = int(timevalue)
                if timevalue > sla_time:
                    sla_error += "%s timevalue %d > sla:max_%s(%d); " % \
                        (t, timevalue, t, sla_time)
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
        "smp": 2,
        "migrate_to_port": 4444,
        "incoming_ip": 0,
        "qmp_sock_src": "/tmp/qmp-sock-src",
        "qmp_sock_dst": "/tmp/qmp-sock-dst",
        "max_down_time": 0.10
    }
    sla = {
        "max_totaltime": 10,
        "max_downtime": 0.10,
        "max_setuptime": 0.50,
    }
    args = {
        "options": options,
        "sla": sla
    }
    result = {}

    migrate = QemuMigrate(args, ctx)
    migrate.run(result)
    print(result)

if __name__ == '__main__':    # pragma: no cover
    _test()
