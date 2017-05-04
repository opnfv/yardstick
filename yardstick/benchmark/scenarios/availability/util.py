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
