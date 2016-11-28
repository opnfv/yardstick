##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import os
import threading
import time

from docker import Client

from yardstick.common import constants as config
from api import conf as api_conf
from api.utils import common as common_utils
from api.utils import influx

logger = logging.getLogger(__name__)


def createInfluxDBContainer(args):
    try:
        container = _create_influxdb_container()
        _config_output_file()
        thread = threading.Thread(target=_config_influxdb)
        thread.start()
        return common_utils.result_handler('success', container)
    except Exception as e:
        message = 'Failed to create influxdb container: %s' % e
        return common_utils.error_handler(message)


def _create_influxdb_container():
    client = Client(base_url=config.DOCKER_URL)

    ports = [8083, 8086]
    port_bindings = {k: k for k in ports}
    host_config = client.create_host_config(port_bindings=port_bindings)

    container = client.create_container(image='tutum/influxdb',
                                        ports=ports,
                                        detach=True,
                                        tty=True,
                                        host_config=host_config)
    client.start(container)
    return container


def _config_influxdb():
    time.sleep(20)
    try:
        client = influx.get_data_db_client()
        client.create_user(config.USER, config.PASSWORD, config.DATABASE)
        client.create_database(config.DATABASE)
        logger.info('Success to config influxDB')
    except Exception as e:
        logger.debug('Failed to config influxDB: %s', e)


def _config_output_file():
    if not os.path.exists('/etc/yardstick'):
        os.makedirs('/etc/yardstick')
    with open('/etc/yardstick/yardstick.conf', 'w') as f:
        f.write('''[DEFAULT]
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
                ''' % api_conf.GATEWAY_IP)
