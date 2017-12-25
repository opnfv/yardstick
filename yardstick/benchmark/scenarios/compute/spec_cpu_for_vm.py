##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import logging
import pkg_resources
import os

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base
from yardstick.common.constants import YARDSTICK_ROOT_PATH

LOG = logging.getLogger(__name__)


class SpecCPUforVM(base.Scenario):
    """Spec CPU2006 benchmark for Virtual Machine

    Parameters
        benchmark_subset - Specifies a subset of SPEC CPU2006 benchmarks to run
            type:       string
            unit:       na
            default:    na

        SPECint_benchmark - A SPECint benchmark to run
            type:       string
            unit:       na
            default:    na

        SPECfp_benchmark - A SPECfp benchmark to run
            type:       string
            unit:       na
            default:    na

        output_format - Desired report format
            type:       string
            unit:       na
            default:    na

        runspec_config - SPEC CPU2006 config file provided to the runspec binary
            type:       string
            unit:       na
            default:    "Example-linux64-amd64-gcc43+.cfg"

        runspec_iterations - The number of benchmark iterations to execute.
                             For a reportable run, must be 3.
            type:       int
            unit:       na
            default:    na

        runspec_tune - Tuning to use (base, peak, or all). For a reportable run, must be either
                       base or all. Reportable runs do base first, then (optionally) peak.
            type:       string
            unit:       na
            default:    na

        runspec_size - Size of input data to run (test, train, or ref). Reportable runs ensure
                       that your binaries can produce correct results with the test and train
                       workloads.
            type:       string
            unit:       na
            default:    na
    """
    __scenario_type__ = "SpecCPU2006_for_VM"
    CPU2006_ISO = "cpu2006-1.2.iso"
    CPU2006_DIR = "~/cpu2006"
    CPU2006_RESULT_FILE = os.path.join(CPU2006_DIR, "result/CINT2006.001.ref.txt")

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False
        self.options = self.scenario_cfg['options']

    def setup(self):
        """scenario setup"""
        host = self.context_cfg['host']
        LOG.info("user:%s, host:%s", host['user'], host['ip'])
        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        spec_cpu_iso = os.path.join(YARDSTICK_ROOT_PATH,
                                    "yardstick/resources/files/",
                                    self.CPU2006_ISO)

        self.client.put(spec_cpu_iso, "~/cpu2006-1.2.iso")
        self.client.execute("sudo mount -t iso9660 -o ro,exec ~/cpu2006-1.2.iso /mnt")
        self.client.execute("/mnt/install.sh -fd ~/cpu2006")

        if "runspec_config" in self.options:
            self.runspec_config = self.options["runspec_config"]

            self.runspec_config_file = pkg_resources.resource_filename(
                "yardstick.resources", 'files/' + self.runspec_config)

            # copy SPEC CPU2006 config file to host if given
            cfg_path = os.path.join(self.CPU2006_DIR,
                                    'config/yardstick_spec_cpu2006.cfg')
            self.client._put_file_shell(self.runspec_config_file, cfg_path)
        else:
            self.runspec_config = "Example-linux64-amd64-gcc43+.cfg"

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        cmd = "cd %s && . ./shrc && runspec --config %s" % (
            self.CPU2006_DIR, self.runspec_config)
        cmd_args = ""

        if "rate" in self.options:
            cmd_args += " --rate %s" % self.options["runspec_rate"]

        if "output_format" in self.options:
            cmd_args += " --output_format %s" % self.options["output_format"]

        if "runspec_tune" in self.options:
            cmd_args += " --tune %s" % self.options["runspec_tune"]

        benchmark_subset = self.options.get('benchmark_subset', None)
        specint_benchmark = self.options.get('SPECint_benchmark', None)
        specfp_benchmark = self.options.get('SPECfp_benchmark', None)

        if benchmark_subset:
            cmd_args += " %s" % benchmark_subset
        else:
            cmd_args += " --noreportable"

            if "runspec_iterations" in self.options:
                cmd_args += " --iterations %s" % self.options["runspec_iterations"]

            if "runspec_size" in self.options:
                cmd_args += " --size %s" % self.options["runspec_size"]

            if specint_benchmark:
                cmd_args += " %s" % specint_benchmark

            if specfp_benchmark:
                cmd_args += " %s" % specfp_benchmark

        cmd += "%s" % cmd_args

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd, timeout=86400)
        if status:
            raise RuntimeError(stderr)

        cmd = "cat %s" % self.CPU2006_RESULT_FILE
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd, timeout=30)
        if status:
            raise RuntimeError(stderr)
        if stdout:
            LOG.info("SPEC CPU2006 result is:\n%s", stdout)

        result.update({"SPEC_CPU_result": stdout})
        # fetch SPEC CPU2006 result files
        self.client.get('~/cpu2006/result', '/tmp/')
        LOG.info('SPEC CPU2006 benchmark completed, please find benchmark reports \
                  at /tmp/result directory')
