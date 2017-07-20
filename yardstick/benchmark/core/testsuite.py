##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'testcase' """
from __future__ import absolute_import
from __future__ import print_function

import os
import logging

from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)


class Testsuite(object):
    """Testcase commands.

       Set of commands to discover and display test cases.
    """

    def list_all(self, args):
        """List existing test cases"""

        testsuite_list = self._get_testsuite_file_list()

        return testsuite_list

    def _get_testsuite_file_list(self):
        try:
            testsuite_files = sorted(os.listdir(consts.TESTSUITE_DIR))
        except OSError:
            LOG.exception('Failed to list dir:\n%s\n', consts.TESTSUITE_DIR)
            raise

        return testsuite_files
