##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

from api import Url


urlpatterns = [
    Url('/yardstick/asynctask', 'v1_async_task'),
    Url('/yardstick/testcases', 'v1_test_case'),
    Url('/yardstick/testcases/release/action', 'v1_release_case'),
    Url('/yardstick/testcases/samples/action', 'v1_sample_case'),
    Url('/yardstick/testcases/<case_name>/docs', 'v1_case_docs'),
    Url('/yardstick/testsuites/action', 'v1_test_suite'),
    Url('/yardstick/results', 'v1_result'),
    Url('/yardstick/env/action', 'v1_env')
]
