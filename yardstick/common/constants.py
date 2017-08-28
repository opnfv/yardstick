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
from functools import reduce

import pkg_resources

from yardstick.common.utils import parse_yaml

dirname = os.path.dirname
abspath = os.path.abspath
join = os.path.join
sep = os.path.sep

CONF = {}


def get_param(key, default=''):

    # we have to defer this to runtime so that we can mock os.environ.get in unittests
    conf_file = os.environ.get('CONF_FILE', '/etc/yardstick/yardstick.yaml')

    # don't re-parse yaml for each lookup
    if not CONF:
        CONF.update(parse_yaml(conf_file))
    try:
        return reduce(lambda a, b: a[b], key.split('.'), CONF)
    except KeyError:
        if not default:
            raise
        return default


try:
    SERVER_IP = get_param('api.server_ip')
except KeyError:
    try:
        from pyroute2 import IPDB
    except ImportError:
        SERVER_IP = '172.17.0.1'
    else:
        with IPDB() as ip:
            try:
                SERVER_IP = ip.routes['default'].gateway
            except KeyError:
                # during unittests ip.routes['default'] can be invalid
                SERVER_IP = '127.0.0.1'

if not SERVER_IP:
    SERVER_IP = '127.0.0.1'


# dir
CONF_DIR = get_param('dir.conf', '/etc/yardstick')
IMAGE_DIR = get_param('dir.images', '/home/opnfv/images/')
REPOS_DIR = get_param('dir.repos', '/home/opnfv/repos/yardstick')
RELENG_DIR = get_param('dir.releng', '/home/opnfv/repos/releng')
LOG_DIR = get_param('dir.log', '/tmp/yardstick/')
YARDSTICK_ROOT_PATH = dirname(
    dirname(abspath(pkg_resources.resource_filename(__name__, "")))) + sep
TASK_LOG_DIR = get_param('dir.tasklog', '/var/log/yardstick/')
CONF_SAMPLE_DIR = join(REPOS_DIR, 'etc/yardstick/')
ANSIBLE_DIR = join(REPOS_DIR, 'ansible')
SAMPLE_CASE_DIR = join(REPOS_DIR, 'samples')
TESTCASE_DIR = join(YARDSTICK_ROOT_PATH, 'tests/opnfv/test_cases/')
TESTSUITE_DIR = join(YARDSTICK_ROOT_PATH, 'tests/opnfv/test_suites/')
DOCS_DIR = join(REPOS_DIR, 'docs/testing/user/userguide/')
OPENSTACK_CONF_DIR = '/etc/openstack'

# file
OPENRC = get_param('file.openrc', '/etc/yardstick/openstack.creds')
ETC_HOSTS = get_param('file.etc_hosts', '/etc/hosts')
CONF_FILE = join(CONF_DIR, 'yardstick.conf')
POD_FILE = join(CONF_DIR, 'pod.yaml')
CLOUDS_CONF = join(OPENSTACK_CONF_DIR, 'clouds.yml')
K8S_CONF_FILE = join(CONF_DIR, 'admin.conf')
CONF_SAMPLE_FILE = join(CONF_SAMPLE_DIR, 'yardstick.conf.sample')
FETCH_SCRIPT = get_param('file.fetch_script', 'utils/fetch_os_creds.sh')
FETCH_SCRIPT = join(RELENG_DIR, FETCH_SCRIPT)
CLEAN_IMAGES_SCRIPT = get_param('file.clean_image_script',
                                'tests/ci/clean_images.sh')
CLEAN_IMAGES_SCRIPT = join(REPOS_DIR, CLEAN_IMAGES_SCRIPT)
LOAD_IMAGES_SCRIPT = get_param('file.load_image_script',
                               'tests/ci/load_images.sh')
LOAD_IMAGES_SCRIPT = join(REPOS_DIR, LOAD_IMAGES_SCRIPT)
DEFAULT_OUTPUT_FILE = get_param('file.output_file', '/tmp/yardstick.out')
DEFAULT_HTML_FILE = get_param('file.html_file', '/tmp/yardstick.htm')
REPORTING_FILE = get_param('file.reporting_file', '/tmp/report.html')

# influxDB
INFLUXDB_IP = get_param('influxdb.ip', SERVER_IP)
INFLUXDB_PORT = get_param('influxdb.port', 8086)
INFLUXDB_USER = get_param('influxdb.username', 'root')
INFLUXDB_PASS = get_param('influxdb.password', 'root')
INFLUXDB_DB_NAME = get_param('influxdb.db_name', 'yardstick')
INFLUXDB_IMAGE = get_param('influxdb.image', 'tutum/influxdb')
INFLUXDB_TAG = get_param('influxdb.tag', '0.13')
INFLUXDB_DASHBOARD_PORT = 8083

# grafana
GRAFANA_IP = get_param('grafana.ip', SERVER_IP)
GRAFANA_PORT = get_param('grafana.port', 3000)
GRAFANA_USER = get_param('grafana.username', 'admin')
GRAFANA_PASS = get_param('grafana.password', 'admin')
GRAFANA_IMAGE = get_param('grafana.image', 'grafana/grafana')
GRAFANA_TAG = get_param('grafana.tag', '4.4.3')
GRAFANA_MAPPING_PORT = 1948

# api
API_PORT = 5000
DOCKER_URL = 'unix://var/run/docker.sock'
INSTALLERS = ['apex', 'compass', 'fuel', 'joid']
SQLITE = 'sqlite:////tmp/yardstick.db'

API_SUCCESS = 1
API_ERROR = 2
TASK_NOT_DONE = 0
TASK_DONE = 1
TASK_FAILED = 2

BASE_URL = 'http://localhost:5000'
ENV_ACTION_API = BASE_URL + '/yardstick/env/action'
ASYNC_TASK_API = BASE_URL + '/yardstick/asynctask'

# general
TESTCASE_PRE = 'opnfv_yardstick_'
TESTSUITE_PRE = 'opnfv_'
