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
    i = 0
    values = []
    result = '/bin/bash -s' if remote else ''
    for key in param.keys():
        values.append(param[key])
        result += " {%d}" % i
        i = i + 1
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


def get_prefix():
    return "$"


def build_shell_command(param_config, remote=True,
                        intermediate_variables=None):
    i = 0
    param_template = '/bin/bash -s' if remote else ''
    for key in param_config.keys():
        if str(param_config[key]).startswith(get_prefix()):
            var_name = param_config[key]
            if type(None) != type(intermediate_variables) \
                    and var_name in intermediate_variables:
                param_config[key] = intermediate_variables[var_name]
        param_template += " {%d}" % i
        i += 1
    l = list(item for item in param_config.values())
    result = param_template.format(*l)
    LOG.debug("THE RESULT OF build_shell_command IS: %s", result)
    return result


def read_stdout_item(stdout, key):
    strs = stdout.split("\n")
    for item in strs:
        if item.find(key) != -1:
            attributes = item.split("|")
            if (attributes[1].lstrip().find(key) == 0):
                return attributes[2].strip()
    return None
