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
    Url('/yardstick/env/action', 'v1_env'),

    # api v2
    Url('/api/v2/yardstick/environments', 'v2_environments'),
    Url('/api/v2/yardstick/environments/action', 'v2_environments'),
    Url('/api/v2/yardstick/environments/<environment_id>', 'v2_environment'),

    Url('/api/v2/yardstick/openrcs', 'v2_openrcs'),
    Url('/api/v2/yardstick/openrcs/action', 'v2_openrcs'),
    Url('/api/v2/yardstick/openrcs/<openrc_id>', 'v2_openrc'),

    Url('/api/v2/yardstick/pods', 'v2_pods'),
    Url('/api/v2/yardstick/pods/action', 'v2_pods'),
    Url('/api/v2/yardstick/pods/<pod_id>', 'v2_pod'),

    Url('/api/v2/yardstick/images', 'v2_images'),
    Url('/api/v2/yardstick/images/action', 'v2_images'),
    Url('/api/v2/yardstick/images/<image_id>', 'v2_image'),

    Url('/api/v2/yardstick/containers', 'v2_containers'),
    Url('/api/v2/yardstick/containers/action', 'v2_containers'),
    Url('/api/v2/yardstick/containers/<container_id>', 'v2_container'),

    Url('/api/v2/yardstick/projects', 'v2_projects'),
    Url('/api/v2/yardstick/projects/action', 'v2_projects'),
    Url('/api/v2/yardstick/projects/<project_id>', 'v2_project'),

    Url('/api/v2/yardstick/tasks', 'v2_tasks'),
    Url('/api/v2/yardstick/tasks/action', 'v2_tasks'),
    Url('/api/v2/yardstick/tasks/<task_id>', 'v2_task'),
    Url('/api/v2/yardstick/tasks/<task_id>/log', 'v2_task_log'),

    Url('/api/v2/yardstick/testcases', 'v2_testcases'),
    Url('/api/v2/yardstick/testcases/action', 'v2_testcases'),
    Url('/api/v2/yardstick/testcases/<case_name>', 'v2_testcase'),

    Url('/api/v2/yardstick/testsuites', 'v2_testsuites'),
    Url('/api/v2/yardstick/testsuites/action', 'v2_testsuites'),
    Url('/api/v2/yardstick/testsuites/<suite_name>', 'v2_testsuite')
]
