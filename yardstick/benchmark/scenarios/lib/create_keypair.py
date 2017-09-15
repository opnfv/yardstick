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
import paramiko

from yardstick.benchmark.scenarios import base
import yardstick.common.openstack_utils as op_utils

LOG = logging.getLogger(__name__)


class CreateKeypair(base.Scenario):
    """Create an OpenStack keypair"""

    __scenario_type__ = "CreateKeypair"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.key_name = self.options.get("key_name", "yardstick_key")
        self.key_filename = self.options.get("key_path", "/tmp/yardstick_key")

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        rsa_key = paramiko.RSAKey.generate(bits=2048, progress_func=None)
        rsa_key.write_private_key_file(self.key_filename)
        LOG.info("Writing key_file %s ...", self.key_filename)
        with open(self.key_filename + ".pub", "w") as pubkey_file:
            pubkey_file.write(
                "%s %s\n" % (rsa_key.get_name(), rsa_key.get_base64()))
        del rsa_key

        keypair = op_utils.create_keypair(self.key_name,
                                          self.key_filename + ".pub")

        if keypair:
            result.update({"keypair_create": 1})
            LOG.info("Create keypair successful!")
        else:
            result.update({"keypair_create": 0})
            LOG.info("Create keypair failed!")
        try:
            keys = self.scenario_cfg.get('output', '').split()
        except KeyError:
            pass
        else:
            values = [keypair.id]
            return self._push_to_outputs(keys, values)
