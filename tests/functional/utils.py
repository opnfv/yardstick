##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import copy
import os

from oslo_serialization import jsonutils

from yardstick.common import process


class Yardstick(object):
    """Create and represent separate yardstick installation.

    Usage:
        yardstick = yardstick()
        output = yardstick("runner list")

    """

    def __init__(self):
        self._args = ["yardstick"]
        self.env = copy.deepcopy(os.environ)

    def __call__(self, cmd, getjson=False):
        """Call yardstick in the shell

        :param cmd: Yardstick command.
        :param getjson: If the output is a JSON object, it's deserialized.
        :return Command output string.
        """

        if not isinstance(cmd, list):
            cmd = cmd.split(" ")
        cmd = self._args + cmd
        output = process.execute(cmd=cmd)
        if getjson:
            return jsonutils.loads(output)
        return output
