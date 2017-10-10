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

from yardstick import ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class CreateKeypair(base.OpenstackScenario):
    """Create an OpenStack keypair"""

    __scenario_type__ = "CreateKeypair"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        'key_name': 'yardstick_key',
        'key_path': '/tmp/yardstick_key',
    }

    def _run(self, result):
        """execute the test"""

        pub_filename = ssh.SSH.gen_keys(self.key_name)
        keypair = self.nova_create_keypair(self.key_name, pub_filename)

        try:
            value = keypair.id
        except AttributeError:
            result["keypair_create"] = 0
            LOG.info("Create keypair failed!")
            return []
        else:
            result["keypair_create"] = 1
            LOG.info("Create keypair successful!")
            return [value]
