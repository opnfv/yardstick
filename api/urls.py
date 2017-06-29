##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

from api import views
from api.utils.common import Url


urlpatterns = [
    Url('/yardstick/asynctask', views.Asynctask, 'asynctask'),
    Url('/yardstick/testcases', views.Testcases, 'testcases'),
    Url('/yardstick/testcases/release/action', views.ReleaseAction, 'release'),
    Url('/yardstick/testcases/samples/action', views.SamplesAction, 'samples'),
    Url('/yardstick/testcases/<case_name>/docs', views.CaseDocs, 'casedocs'),
    Url('/yardstick/testsuites/action', views.TestsuitesAction, 'testsuites'),
    Url('/yardstick/results', views.Results, 'results'),
    Url('/yardstick/env/action', views.EnvAction, 'env')
]
