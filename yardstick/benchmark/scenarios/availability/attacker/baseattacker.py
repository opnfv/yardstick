##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import pkg_resources
import yaml
import logging
import os

import yardstick.common.utils as utils

LOG = logging.getLogger(__name__)

attacker_conf_path = pkg_resources.resource_filename(
    "yardstick.benchmark.scenarios.availability",
    "attacker_conf.yaml")


class BaseAttacker(object):

    attacker_cfgs = {}

    def __init__(self, config, context):
        if not BaseAttacker.attacker_cfgs:
            with open(attacker_conf_path) as stream:
                BaseAttacker.attacker_cfgs = yaml.load(stream)

        self._config = config
        self._context = context
        self.setup_done = False

    @staticmethod
    def get_attacker_cls(attacker_cfg):
        '''return attacker instance of specified type'''
        attacker_type = attacker_cfg['fault_type']
        for attacker_cls in utils.itersubclasses(BaseAttacker):
            if attacker_type == attacker_cls.__attacker_type__:
                return attacker_cls
        raise RuntimeError("No such runner_type %s" % attacker_type)

    def get_script_fullpath(self, path):
        base_path = os.path.dirname(attacker_conf_path)
        return os.path.join(base_path, path)
