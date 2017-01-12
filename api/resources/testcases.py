# ############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# ############################################################################
from yardstick.benchmark.core.testcase import Testcase
from yardstick.benchmark.core import Param
from api.utils import common as common_utils


def default(args):
    return listAllTestcases(args)


def listAllTestcases(args):
    param = Param(args)
    testcase_list = Testcase().list_all(param)
    return common_utils.result_handler(1, testcase_list)
