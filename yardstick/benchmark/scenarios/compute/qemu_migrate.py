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
        script_dir = setup_options["script_dir"]
        LOG.debug("Send scripts from %s to workspace %s",
                  script_dir, self.WORKSPACE)
        client.put(script_dir, self.WORKSPACE, recursive=True)

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
        self.host.run("cat > ~/qemu_migrate_benchmark.sh",
                      stdin=open(self.target_script, "rb"))

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
        cmd_args = " %s %s %s %s %s" %\
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
            max_totaltime = int(self.scenario_cfg['sla']['max_totaltime'])
            totaltime = result["total_time"]
            if totaltime > max_totaltime:
                sla_error += "Total time %f < " \
                             "sla:max_totaltime %f)" % (totaltime, max_totaltime)
            assert sla_error == "", sla_error
            max_downtime = float(self.scenario_cfg['sla']['max_downtime'])
            downtime = result["down_time"]
            if downtime > max_downtime:
                sla_error += "downtime %f < " \
                             "sla:max_downtime %f)" % (downtime, max_downtime)
            assert sla_error == "", sla_error
            max_setuptime = int(self.scenario_cfg['sla']['max_setuptime'])
            setuptime = result["setup_time"]
            if setuptime > max_setuptime:
                sla_error += "setuptime %d < " \
                  "sla:max_setuptime %d)" % (setuptime, max_setuptime)
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
    args = {
        "options": options
    }
    result = {}
    migrate = QemuMigrate(args, ctx)
    migrate.run(result)
    print(result)

if __name__ == '__main__':    # pragma: no cover
    _test()
