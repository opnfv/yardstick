##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import pkg_resources
import logging
import os

import yardstick.common.utils as utils
from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)

operation_conf_path = pkg_resources.resource_filename(
    "yardstick.benchmark.scenarios.availability",
    "operation_conf.yaml")


class OperationMgr(object):

    def __init__(self):
        self._operation_list = []

    def init_operations(self, operation_cfgs, context):
        LOG.debug("operationMgr confg: %s", operation_cfgs)
        for cfg in operation_cfgs:
            operation_type = cfg['operation_type']
            operation_cls = BaseOperation.get_operation_cls(operation_type)
            operation_ins = operation_cls(cfg, context)
            operation_ins.key = cfg['key']
            operation_ins.setup()
            self._operation_list.append(operation_ins)

    def __getitem__(self, item):
        for obj in self._operation_list:
            if(obj.key == item):
                return obj
        raise KeyError("No such operation instance of key - %s" % item)

    def rollback(self):
        for _instance in self._operation_list:
            _instance.rollback()


class BaseOperation(object):

    operation_cfgs = {}

    def __init__(self, config, context):
        if not BaseOperation.operation_cfgs:
            with open(operation_conf_path) as stream:
                BaseOperation.operation_cfgs = yaml_load(stream)
        self.key = ''
        self._config = config
        self._context = context
        self.intermediate_variables = {}

    @staticmethod
    def get_operation_cls(type):
        """return operation instance of specified type"""
        operation_type = type
        for operation_cls in utils.itersubclasses(BaseOperation):
            if operation_type == operation_cls.__operation__type__:
                return operation_cls
        raise RuntimeError("No such runner_type %s" % operation_type)

    def get_script_fullpath(self, path):
        base_path = os.path.dirname(operation_conf_path)
        return os.path.join(base_path, path)

    def setup(self):
        pass

    def run(self):
        pass

    def rollback(self):
        pass
