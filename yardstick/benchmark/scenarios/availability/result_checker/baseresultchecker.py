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
import time

import yardstick.common.utils as utils
from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)

resultchecker_conf_path = pkg_resources.resource_filename(
    "yardstick.benchmark.scenarios.availability",
    "result_checker_conf.yaml")


class ResultCheckerMgr(object):

    def __init__(self):
        self._result_checker_list = []

    def init_ResultChecker(self, resultchecker_cfgs, context):
        LOG.debug("resultcheckerMgr confg: %s", resultchecker_cfgs)

        for cfg in resultchecker_cfgs:
            resultchecker_type = cfg['checker_type']
            resultchecker_cls = BaseResultChecker.get_resultchecker_cls(
                resultchecker_type)
            resultchecker_ins = resultchecker_cls(cfg, context)
            resultchecker_ins.key = cfg['key']
            resultchecker_ins.setup()
            self._result_checker_list.append(resultchecker_ins)

    def __getitem__(self, item):
        for obj in self._result_checker_list:
            if(obj.key == item):
                return obj
        raise KeyError("No such result checker instance of key - %s" % item)

    def verify(self):
        result = True
        for obj in self._result_checker_list:
            result &= obj.success
        return result

    def store_result(self, result_store):
        for checker in self._result_checker_list:
            checker_result = checker.result()
            for (k, v) in checker_result.items():
                result_store[checker.key + "_" + k] = v


class BaseResultChecker(object):

    resultchecker_cfgs = {}

    def __init__(self, config, context):
        if not BaseResultChecker.resultchecker_cfgs:
            with open(resultchecker_conf_path) as stream:
                BaseResultChecker.resultchecker_cfgs = yaml_load(stream)
        self.actualResult = object()
        self.expectedResult = object()
        self.success = False

        self._config = config
        self._context = context
        self.setup_done = False
        self._result = {}

    @staticmethod
    def get_resultchecker_cls(type):
        """return resultchecker instance of specified type"""
        resultchecker_type = type
        for checker_cls in utils.itersubclasses(BaseResultChecker):
            if resultchecker_type == checker_cls.__result_checker__type__:
                return checker_cls
        raise RuntimeError("No such runner_type %s" % resultchecker_type)

    def get_script_fullpath(self, path):
        base_path = os.path.dirname(resultchecker_conf_path)
        return os.path.join(base_path, path)

    def setup(self):
        pass

    def verify(self):
        if(self.actualResult == self.expectedResult):
            self.success = True
        return self.success

    def check(self):
        check_time = self._config.get("max_check_time", 0)

        begin_time = time.time()

        while True:
            try:
                exit_status = self.verify()
            except Exception:
                LOG.exception("Exception occured when run the resultchecker.")
                exit_status = False

            one_check_end_time = time.time()

            if exit_status:
                LOG.debug("the check result is as expected.")
                break
            LOG.debug("the check_time is %s, and have checked %s", check_time, one_check_end_time - begin_time)
            if one_check_end_time - begin_time > check_time:
                LOG.debug("the resultchecker max_time finished and exit!")
                break
            else:
                time.sleep(1)

        end_time = time.time()
        total_time = end_time - begin_time

        LOG.debug("the resultchecker has completed in %s seconds and the result is %s",
                  total_time, self.success)

        self._result = {"check_time": total_time, "check_result": self.success}

    def result(self):
        return self._result
