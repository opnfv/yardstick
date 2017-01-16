##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import os

DOCKER_URL = 'unix://var/run/docker.sock'

# database config
USER = 'root'
PASSWORD = 'root'
DATABASE = 'yardstick'

INFLUXDB_IMAGE = 'tutum/influxdb'
INFLUXDB_TAG = '0.13'

GRAFANA_IMAGE = 'grafana/grafana'
GRAFANA_TAGS = '3.1.1'

dirname = os.path.dirname
abspath = os.path.abspath
join = os.path.join
sep = os.path.sep

INSTALLERS = ['apex', 'compass', 'fuel', 'joid']

YARDSTICK_ROOT_PATH = dirname(dirname(dirname(abspath(__file__)))) + sep

TESTCASE_DIR = join(YARDSTICK_ROOT_PATH, 'tests/opnfv/test_cases/')

TESTSUITE_DIR = join(YARDSTICK_ROOT_PATH, 'tests/opnfv/test_suites/')

YARDSTICK_REPOS_DIR = '/home/opnfv/repos/yardstick'

YARDSTICK_LOG_DIR = '/tmp/yardstick/'

YARDSTICK_CONFIG_DIR = '/etc/yardstick/'

YARDSTICK_CONFIG_FILE = join(YARDSTICK_CONFIG_DIR, 'yardstick.conf')

YARDSTICK_CONFIG_SAMPLE_DIR = join(YARDSTICK_ROOT_PATH, 'etc/yardstick/')

YARDSTICK_CONFIG_SAMPLE_FILE = join(YARDSTICK_CONFIG_SAMPLE_DIR,
                                    'yardstick.conf.sample')

RELENG_DIR = '/home/opnfv/repos/releng'

OS_FETCH_SCRIPT = 'utils/fetch_os_creds.sh'

CLEAN_IMAGES_SCRIPT = 'tests/ci/clean_images.sh'

LOAD_IMAGES_SCRIPT = 'tests/ci/load_images.sh'

OPENSTACK_RC_FILE = join(YARDSTICK_CONFIG_DIR, 'openstack.creds')

BASE_URL = 'http://localhost:5000'
ENV_ACTION_API = BASE_URL + '/yardstick/env/action'
ASYNC_TASK_API = BASE_URL + '/yardstick/asynctask'

SQLITE = 'sqlite:////tmp/yardstick.db'

DEFAULT_OUTPUT_FILE = '/tmp/yardstick.out'
