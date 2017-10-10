##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import print_function
from __future__ import absolute_import

import logging

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class DeleteKeypair(base.OpenstackScenario):
    """Delete an OpenStack keypair"""

    __scenario_type__ = "DeleteKeypair"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        "key_name": "yardstick_key",
    }

    def _run(self, result):
        """execute the test"""

        status = self.nova_delete_keypair(self.key_name)
        if status:
            result.update({"delete_keypair": 1})
            LOG.info("Delete keypair successful!")
        else:
            result.update({"delete_keypair": 0})
            LOG.info("Delete keypair failed!")
