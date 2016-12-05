##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import logging

import six.moves.configparser as ConfigParser
from six.moves.urllib.parse import urlsplit
from influxdb import InfluxDBClient

from api import conf

logger = logging.getLogger(__name__)


def get_data_db_client():
    parser = ConfigParser.ConfigParser()
    try:
        parser.read(conf.OUTPUT_CONFIG_FILE_PATH)
        dispatcher = parser.get('DEFAULT', 'dispatcher')

        if 'influxdb' != dispatcher:
            raise RuntimeError

        ip = _get_ip(parser.get('dispatcher_influxdb', 'target'))
        username = parser.get('dispatcher_influxdb', 'username')
        password = parser.get('dispatcher_influxdb', 'password')
        db_name = parser.get('dispatcher_influxdb', 'db_name')
        return InfluxDBClient(ip, conf.PORT, username, password, db_name)
    except ConfigParser.NoOptionError:
        logger.error('can not find the key')
        raise


def _get_ip(url):
    return urlsplit(url).hostname


def _write_data(measurement, field, timestamp, tags):
    point = {
        'measurement': measurement,
        'fields': field,
        'time': timestamp,
        'tags': tags
    }

    try:
        client = get_data_db_client()

        logger.debug('Start to write data: %s', point)
        client.write_points([point])
    except RuntimeError:
        logger.debug('dispatcher is not influxdb')


def write_data_tasklist(task_id, timestamp, status, error=''):
    field = {'status': status, 'error': error}
    tags = {'task_id': task_id}
    _write_data('tasklist', field, timestamp, tags)


def query(query_sql):
    try:
        client = get_data_db_client()
        logger.debug('Start to query: %s', query_sql)
        return list(client.query(query_sql).get_points())
    except RuntimeError:
        logger.error('dispatcher is not influxdb')
        raise
