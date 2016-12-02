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
import time
import json

from docker import Client

from yardstick.common import constants as config
from yardstick.common import utils as yardstick_utils
from yardstick.common.httpClient import HttpClient
from api import conf as api_conf
from api.utils import influx

logger = logging.getLogger(__name__)


def createGrafanaContainer(args):
    thread = threading.Thread(target=_create_grafana)
    thread.start()


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
    yardstick_utils.makedirs('/etc/yardstick')
    with open('/etc/yardstick/yardstick.conf', 'w') as f:
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
