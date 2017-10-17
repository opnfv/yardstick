##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import

import copy
import os

from subprocess import Popen, PIPE, STDOUT

from oslo_serialization import jsonutils
from oslo_utils import encodeutils


class Yardstick(object):
    """Create and represent separate yardstick installation.

    Usage:
        yardstick = yardstick()
        output = yardstick("runner list")

    """

    def __init__(self, fake=False):
        super(Yardstick, self).__init__()
        self.args = ["yardstick"]
        self.env = copy.deepcopy(os.environ)
        self.fake = fake

    def __call__(self, cmd, getjson=False, report_path=None, raw=False,
                 suffix=None, extension=None, keep_old=False,
                 write_report=False):
        """Call yardstick in the shell

        :param cmd: yardstick command
        :param getjson: in cases, when yardstick prints JSON, you can catch
         output deserialized
        TO DO:
        :param report_path: if present, yardstick command and its output will
         be written to file with passed file name
        :param raw: don't write command itself to report file. Only output
            will be written
        """

        if not isinstance(cmd, list):
            cmd = cmd.split(" ")

        process = Popen(self.args + cmd, stdout=PIPE, stderr=STDOUT, env=self.env)
        stdout, _ = process.communicate()
        output = encodeutils.safe_decode(stdout, 'utf-8')

        if getjson:
            return jsonutils.loads(output)
        return output
