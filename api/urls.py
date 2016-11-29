##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from api import views
from api.utils.common import Url


urlpatterns = [
    Url('/yardstick/testcases/release/action', views.Release, 'release'),
    Url('/yardstick/testcases/samples/action', views.Samples, 'samples'),
    Url('/yardstick/results', views.Results, 'results'),
    Url('/yardstick/env/action', views.Env, 'env')
]
