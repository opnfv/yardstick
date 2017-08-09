##############################################################################
# Copyright (c) 2016 Juan Qiu
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import subprocess
import traceback

LOG = logging.getLogger(__name__)


def buildshellparams(param, remote=True):
    result = '/bin/bash -s' if remote else ''
    result += "".join(" {%d}" % i for i in range(len(param)))
    return result


def execute_shell_command(command):
    """execute shell script with error handling"""
    exitcode = 0
    output = []
    try:
        LOG.debug("the command is: %s", command)
        output = subprocess.check_output(command, shell=True)
    except Exception:
        exitcode = -1
        output = traceback.format_exc()
        LOG.error("exec command '%s' error:\n ", command)
        LOG.error(traceback.format_exc())
    return exitcode, output

PREFIX = '$'


def build_shell_command(param_config, remote=True, intermediate_variables=None):
    param_template = '/bin/bash -s' if remote else ''
    if intermediate_variables:
        for key, val in param_config.items():
            if str(val).startswith(PREFIX):
                try:
                    param_config[key] = intermediate_variables[val]
                except KeyError:
                    pass
    result = param_template + "".join(" {}".format(v) for v in param_config.values())
    LOG.debug("THE RESULT OF build_shell_command IS: %s", result)
    return result


def read_stdout_item(stdout, key):
    if key == "all":
        return stdout
    for item in stdout.splitlines():
        if key in item:
            attributes = item.split("|")
            if attributes[1].lstrip().startswith(key):
                return attributes[2].strip()
    return None
