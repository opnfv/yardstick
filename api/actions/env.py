##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import threading
import subprocess
import time
import json
import os
import sys
import errno
import uuid

from docker import Client

from yardstick.common import constants as config
from yardstick.common import utils as yardstick_utils
from yardstick.common.httpClient import HttpClient
from api import conf as api_conf
from api.utils import influx
from api.utils.common import result_handler

logger = logging.getLogger(__name__)


def createGrafanaContainer(args):
    thread = threading.Thread(target=_create_grafana)
    thread.start()
    result_handler('success', [])


def _create_grafana():
    client = Client(base_url=config.DOCKER_URL)

    try:
        if not _check_image_exist(client, '%s:%s' % (config.GRAFANA_IMAGE,
                                                     config.GRAFANA_TAGS)):
            client.pull(config.GRAFANA_IMAGE, config.GRAFANA_TAGS)

        _create_grafana_container(client)

        time.sleep(5)

        _create_data_source()

        _create_dashboard()
    except Exception as e:
        logger.debug('Error: %s', e)


def _create_dashboard():
    url = 'http://admin:admin@%s:3000/api/dashboards/db' % api_conf.GATEWAY_IP
    data = json.load(file('../dashboard/ping_dashboard.json'))
    HttpClient().post(url, data)


def _create_data_source():
    url = 'http://admin:admin@%s:3000/api/datasources' % api_conf.GATEWAY_IP
    data = {
        "name": "yardstick",
        "type": "influxdb",
        "access": "proxy",
        "url": "http://%s:8086" % api_conf.GATEWAY_IP,
        "password": "root",
        "user": "root",
        "database": "yardstick",
        "basicAuth": True,
        "basicAuthUser": "admin",
        "basicAuthPassword": "admin",
        "isDefault": False,
    }
    HttpClient().post(url, data)


def _create_grafana_container(client):
    ports = [3000]
    port_bindings = {k: k for k in ports}
    host_config = client.create_host_config(port_bindings=port_bindings)

    container = client.create_container(image='%s:%s' % (config.GRAFANA_IMAGE,
                                                         config.GRAFANA_TAGS),
                                        ports=ports,
                                        detach=True,
                                        tty=True,
                                        host_config=host_config)
    client.start(container)


def _check_image_exist(client, t):
    return any(t in a['RepoTags'][0] for a in client.images() if a['RepoTags'])


def createInfluxDBContainer(args):
    thread = threading.Thread(target=_create_influxdb)
    thread.start()
    result_handler('success', [])


def _create_influxdb():
    client = Client(base_url=config.DOCKER_URL)

    try:
        _config_output_file()

        if not _check_image_exist(client, '%s:%s' % (config.INFLUXDB_IMAGE,
                                                     config.INFLUXDB_TAG)):
            client.pull(config.INFLUXDB_IMAGE, tag=config.INFLUXDB_TAG)

        _create_influxdb_container(client)

        time.sleep(5)

        _config_influxdb()
    except Exception as e:
        logger.debug('Error: %s', e)


def _create_influxdb_container(client):

    ports = [8083, 8086]
    port_bindings = {k: k for k in ports}
    host_config = client.create_host_config(port_bindings=port_bindings)

    container = client.create_container(image='%s:%s' % (config.INFLUXDB_IMAGE,
                                                         config.INFLUXDB_TAG),
                                        ports=ports,
                                        detach=True,
                                        tty=True,
                                        host_config=host_config)
    client.start(container)


def _config_influxdb():
    try:
        client = influx.get_data_db_client()
        client.create_user(config.USER, config.PASSWORD, config.DATABASE)
        client.create_database(config.DATABASE)
        logger.info('Success to config influxDB')
    except Exception as e:
        logger.debug('Failed to config influxDB: %s', e)


def _config_output_file():
    yardstick_utils.makedirs(config.YARDSTICK_CONFIG_DIR)
    with open(config.YARDSTICK_CONFIG_FILE, 'w') as f:
        f.write("""\
[DEFAULT]
debug = True
dispatcher = influxdb

[dispatcher_file]
file_path = /tmp/yardstick.out

[dispatcher_http]
timeout = 5
# target = http://127.0.0.1:8000/results

[dispatcher_influxdb]
timeout = 5
target = http://%s:8086
db_name = yardstick
username = root
password = root
"""
                % api_conf.GATEWAY_IP)


def prepareYardstickEnv(args):
    thread = threading.Thread(target=_prepare_env_daemon)
    thread.start()
    result_handler('success', [])


def _prepare_env_daemon():

    installer_ip = os.getenv('INSTALLER_IP', 'undefined')
    installer_type = os.getenv('INSTALLER_TYPE', 'undefined')

    _check_variables(installer_ip, installer_type)

    _create_directories()

    rc_file = config.OPENSTACK_RC_FILE

    _get_remote_rc_file(rc_file, installer_ip, installer_type)

    _source_file(rc_file)

    _append_external_network(rc_file)

    _load_images()


def _check_variables(installer_ip, installer_type):

    if installer_ip == 'undefined':
        sys.exit('Missing INSTALLER_IP')

    if installer_type == 'undefined':
        sys.exit('Missing INSTALLER_TYPE')
    elif installer_type not in config.INSTALLERS:
        sys.exit('INSTALLER_TYPE is not correct')


def _create_directories():
    yardstick_utils.makedirs(config.YARDSTICK_CONFIG_DIR)


def _source_file(rc_file):
    yardstick_utils.source_env(rc_file)


def _get_remote_rc_file(rc_file, installer_ip, installer_type):

    os_fetch_script = os.path.join(config.RELENG_DIR, config.OS_FETCH_SCRIPT)

    try:
        cmd = os_fetch_script + " -d %s -i %s -a %s" % (rc_file,
                                                        installer_type,
                                                        installer_ip)
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        p.communicate()[0]

        if p.returncode != 0:
            logger.debug('Failed to fetch credentials from installer')
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def _append_external_network(rc_file):
    cmd = "neutron net-list|grep -v '+'|grep -v name|awk '{print $2}'"
    network_ids = yardstick_utils.execute_command(cmd)

    def ext_net_filter(network_id):
        try:
            uuid.UUID(network_id)
        except ValueError:
            return False

        cmd = "neutron net-show %s|grep 'router:external' \
            |grep -i 'true'" % network_id
        filter_result = yardstick_utils.execute_command(cmd)
        if filter_result:
            return True

        return False

    ext_net_id = filter(ext_net_filter, network_ids)
    if len(ext_net_id) != 0:
        cmd = "neutron net-list|grep %s|awk '{print $4}'" % ext_net_id[0]
        ext_net = yardstick_utils.execute_command(cmd)[0]

        cmd = 'export EXTERNAL_NETWORK=%s' % ext_net
        with open(rc_file, 'a') as f:
            f.write(cmd + '\n')


def _load_images():
    cmd = 'cd %s && source %s' % (config.RELENG_DIR, config.LOAD_IMAGES_SCRIPT)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,
                         executable='/bin/bash')
    output = p.communicate()[0]
    logger.debug('The result is: %s', output)
