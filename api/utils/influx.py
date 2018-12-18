##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
# Copyright (c) 2019 Intel Corporation
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import logging

from six.moves import configparser as ConfigParser
# NOTE(ralonsoh): pylint E0401 import error
# https://github.com/PyCQA/pylint/issues/1640
from six.moves.urllib.parse import urlsplit  # pylint: disable=relative-import
from influxdb import client as influxdb_client

from yardstick.common import constants as consts
from yardstick.common import exceptions
from yardstick import dispatcher


logger = logging.getLogger(__name__)

def get_data_db_client(db=None):
    parser = ConfigParser.ConfigParser()
    try:
        parser.read(consts.CONF_FILE)
        return _get_influxdb_client(parser, db)
    except ConfigParser.NoOptionError:
        logger.error('Can not find the key')
        raise

def _get_influxdb_client(parser, db=None):
    if dispatcher.INFLUXDB not in parser.get('DEFAULT', 'dispatcher'):
        raise exceptions.InfluxDBConfigurationMissing()

    ip = _get_ip(parser.get('dispatcher_influxdb', 'target'))
    user = parser.get('dispatcher_influxdb', 'username')
    password = parser.get('dispatcher_influxdb', 'password')
    if db is None:
        db_name = parser.get('dispatcher_influxdb', 'db_name')
    else:
        db_name = db

    return influxdb_client.InfluxDBClient(ip, consts.INFLUXDB_PORT, user,
                                          password, db_name)


def _get_ip(url):
    return urlsplit(url).hostname


def query(query_sql, db=None):
    try:
        client = get_data_db_client(db)
        logger.debug('Start to query: %s', query_sql)
        return list(client.query(query_sql).get_points())
    except RuntimeError:
        logger.error('dispatcher is not influxdb')
        raise
