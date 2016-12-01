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
import os
import sys
import errno

from docker import Client

from yardstick.common import constants as config
from yardstick.common import utils as yardstick_utils
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


def prepareYardstickEnv(args):
    thread = threading.Thread(target=_prepare_env_daemon)
    thread.start()


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
    yardstick_utils.source_script(rc_file)


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
        cmd = "neutron net-show %s|grep 'router:external' \
            |grep -i 'true'" % network_id
        filter_result = yardstick_utils.execute_command(cmd)
        if len(filter_result) != 0:
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
    cmd = 'cd %s && source %s' % ('/home/opnfv/repos/yardstick',
                                  config.LOAD_IMAGES_SCRIPT)
    subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,
                     executable='/bin/bash')
