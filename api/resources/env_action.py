##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import errno
import json
import logging
import os
import subprocess
import threading
import time
import uuid

from six.moves import configparser

from api import conf as api_conf
from api.database.handler import AsyncTaskHandler
from api.utils import influx
from api.utils.common import result_handler
from docker import Client
from yardstick.common import constants as config
from yardstick.common import utils as yardstick_utils
from yardstick.common import openstack_utils
from yardstick.common.httpClient import HttpClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def createGrafanaContainer(args):
    task_id = str(uuid.uuid4())

    thread = threading.Thread(target=_create_grafana, args=(task_id,))
    thread.start()

    return result_handler('success', {'task_id': task_id})


def _create_grafana(task_id):
    _create_task(task_id)

    client = Client(base_url=config.DOCKER_URL)

    try:
        if not _check_image_exist(client, '%s:%s' % (config.GRAFANA_IMAGE,
                                                     config.GRAFANA_TAGS)):
            client.pull(config.GRAFANA_IMAGE, config.GRAFANA_TAGS)

        _create_grafana_container(client)

        time.sleep(5)

        _create_data_source()

        _create_dashboard()

        _update_task_status(task_id)
    except Exception as e:
        _update_task_error(task_id, str(e))
        logger.debug('Error: %s', e)


def _create_dashboard():
    url = 'http://admin:admin@%s:3000/api/dashboards/db' % api_conf.GATEWAY_IP
    with open('../dashboard/ping_dashboard.json') as dashboard_json:
        data = json.load(dashboard_json)
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
    task_id = str(uuid.uuid4())

    thread = threading.Thread(target=_create_influxdb, args=(task_id,))
    thread.start()

    return result_handler('success', {'task_id': task_id})


def _create_influxdb(task_id):
    _create_task(task_id)

    client = Client(base_url=config.DOCKER_URL)

    try:
        _change_output_to_influxdb()

        if not _check_image_exist(client, '%s:%s' % (config.INFLUXDB_IMAGE,
                                                     config.INFLUXDB_TAG)):
            client.pull(config.INFLUXDB_IMAGE, tag=config.INFLUXDB_TAG)

        _create_influxdb_container(client)

        time.sleep(5)

        _config_influxdb()

        _update_task_status(task_id)
    except Exception as e:
        _update_task_error(task_id, str(e))
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


def _change_output_to_influxdb():
    yardstick_utils.makedirs(config.YARDSTICK_CONFIG_DIR)

    parser = configparser.ConfigParser()
    parser.read(config.YARDSTICK_CONFIG_SAMPLE_FILE)

    parser.set('DEFAULT', 'dispatcher', 'influxdb')
    parser.set('dispatcher_influxdb', 'target',
               'http://%s:8086' % api_conf.GATEWAY_IP)

    with open(config.YARDSTICK_CONFIG_FILE, 'w') as f:
        parser.write(f)


def prepareYardstickEnv(args):
    task_id = str(uuid.uuid4())

    thread = threading.Thread(target=_prepare_env_daemon, args=(task_id,))
    thread.start()

    return result_handler('success', {'task_id': task_id})


def _prepare_env_daemon(task_id):
    _create_task(task_id)

    installer_ip = os.environ.get('INSTALLER_IP', 'undefined')
    installer_type = os.environ.get('INSTALLER_TYPE', 'undefined')

    try:
        _check_variables(installer_ip, installer_type)

        _create_directories()

        rc_file = config.OPENSTACK_RC_FILE

        _get_remote_rc_file(rc_file, installer_ip, installer_type)

        _source_file(rc_file)

        _append_external_network(rc_file)

        # update the external_network
        _source_file(rc_file)

        _clean_images()

        _load_images()

        _update_task_status(task_id)
    except Exception as e:
        _update_task_error(task_id, str(e))
        logger.debug('Error: %s', e)


def _check_variables(installer_ip, installer_type):

    if installer_ip == 'undefined':
        raise SystemExit('Missing INSTALLER_IP')

    if installer_type == 'undefined':
        raise SystemExit('Missing INSTALLER_TYPE')
    elif installer_type not in config.INSTALLERS:
        raise SystemExit('INSTALLER_TYPE is not correct')


def _create_directories():
    yardstick_utils.makedirs(config.YARDSTICK_CONFIG_DIR)


def _source_file(rc_file):
    yardstick_utils.source_env(rc_file)


def _get_remote_rc_file(rc_file, installer_ip, installer_type):

    os_fetch_script = os.path.join(config.RELENG_DIR, config.OS_FETCH_SCRIPT)

    try:
        cmd = [os_fetch_script, '-d', rc_file, '-i', installer_type,
               '-a', installer_ip]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        p.communicate()

        if p.returncode != 0:
            logger.debug('Failed to fetch credentials from installer')
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def _append_external_network(rc_file):
    neutron_client = openstack_utils.get_neutron_client()
    networks = neutron_client.list_networks()['networks']
    try:
        ext_network = next(n['name'] for n in networks if n['router:external'])
    except StopIteration:
        logger.warning("Can't find external network")
    else:
        cmd = 'export EXTERNAL_NETWORK=%s' % ext_network
        try:
            with open(rc_file, 'a') as f:
                f.write(cmd + '\n')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def _clean_images():
    cmd = [config.CLEAN_IMAGES_SCRIPT]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         cwd=config.YARDSTICK_REPOS_DIR)
    output = p.communicate()[0]
    logger.debug('The result is: %s', output)


def _load_images():
    cmd = [config.LOAD_IMAGES_SCRIPT]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         cwd=config.YARDSTICK_REPOS_DIR)
    output = p.communicate()[0]
    logger.debug('The result is: %s', output)


def _create_task(task_id):
    async_handler = AsyncTaskHandler()
    task_dict = {
        'task_id': task_id,
        'status': 0
    }
    async_handler.insert(task_dict)


def _update_task_status(task_id):
    async_handler = AsyncTaskHandler()

    task = async_handler.get_task_by_taskid(task_id)
    async_handler.update_status(task, 1)


def _update_task_error(task_id, error):
    async_handler = AsyncTaskHandler()

    task = async_handler.get_task_by_taskid(task_id)
    async_handler.update_status(task, 2)
    async_handler.update_error(task, error)
