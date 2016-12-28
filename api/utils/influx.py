##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import ConfigParser
from urlparse import urlsplit

from influxdb import InfluxDBClient

from api import conf

logger = logging.getLogger(__name__)


def get_data_db_client():
    parser = ConfigParser.ConfigParser()
    try:
        parser.read(conf.OUTPUT_CONFIG_FILE_PATH)

        if 'influxdb' != parser.get('DEFAULT', 'dispatcher'):
            raise RuntimeError

        return _get_client(parser)
    except ConfigParser.NoOptionError:
        logger.error('can not find the key')
        raise


def _get_client(parser):
    ip = _get_ip(parser.get('dispatcher_influxdb', 'target'))
    username = parser.get('dispatcher_influxdb', 'username')
    password = parser.get('dispatcher_influxdb', 'password')
    db_name = parser.get('dispatcher_influxdb', 'db_name')
    return InfluxDBClient(ip, conf.PORT, username, password, db_name)


def _get_ip(url):
    return urlsplit(url).hostname


def query(query_sql):
    try:
        client = get_data_db_client()
        logger.debug('Start to query: %s', query_sql)
        return list(client.query(query_sql).get_points())
    except RuntimeError:
        logger.error('dispatcher is not influxdb')
        raise
