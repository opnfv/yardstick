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
import threading
import time
import uuid

from six.moves import configparser
from oslo_serialization import jsonutils
from docker import Client

from api import ApiResource
from api.utils import influx
from api.database.v2.handlers import V2ContainerHandler
from api.database.v2.handlers import V2EnvironmentHandler
from yardstick.common import constants as consts
from yardstick.common import utils
from yardstick.common.utils import result_handler
from yardstick.common.utils import get_free_port


LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

environment_handler = V2EnvironmentHandler()
container_handler = V2ContainerHandler()


class V2Containers(ApiResource):

    def post(self):
        return self._dispatch_post()

    def create_influxdb(self, args):
        try:
            environment_id = args['environment_id']
        except KeyError:
            return result_handler(consts.API_ERROR, 'environment_id must be provided')

        try:
            uuid.UUID(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid environment id')

        try:
            environment = environment_handler.get_by_uuid(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such environment id')

        container_info = environment.container_id
        container_info = jsonutils.loads(container_info) if container_info else {}

        if container_info.get('influxdb'):
            return result_handler(consts.API_ERROR, 'influxdb container already exist')

        name = 'influxdb-{}'.format(environment_id[:8])
        port = get_free_port()
        container_id = str(uuid.uuid4())
        LOG.info('%s will launch on : %s', name, port)

        LOG.info('launch influxdb background')
        args = (name, port, container_id)
        thread = threading.Thread(target=self._create_influxdb, args=args)
        thread.start()

        LOG.info('record container in database')
        container_init_data = {
            'uuid': container_id,
            'environment_id': environment_id,
            'name': name,
            'port': port,
            'status': 0
        }
        container_handler.insert(container_init_data)

        LOG.info('update container in environment')
        container_info['influxdb'] = container_id
        environment_info = {'container_id': jsonutils.dumps(container_info)}
        environment_handler.update_attr(environment_id, environment_info)

        return result_handler(consts.API_SUCCESS, {'uuid': container_id})

    def _check_image_exist(self, client, t):
        return any(t in a['RepoTags'][0]
                   for a in client.images() if a['RepoTags'])

    def _create_influxdb(self, name, port, container_id):
        client = Client(base_url=consts.DOCKER_URL)

        try:
            LOG.info('Checking if influxdb image exist')
            if not self._check_image_exist(client, '%s:%s' %
                                           (consts.INFLUXDB_IMAGE,
                                            consts.INFLUXDB_TAG)):
                LOG.info('Influxdb image not exist, start pulling')
                client.pull(consts.INFLUXDB_IMAGE, tag=consts.INFLUXDB_TAG)

            LOG.info('Createing influxdb container')
            container = self._create_influxdb_container(client, name, port)
            LOG.info('Influxdb container is created')

            time.sleep(5)

            container = client.inspect_container(container['Id'])
            ip = container['NetworkSettings']['Networks']['bridge']['IPAddress']
            LOG.debug('container ip is: %s', ip)

            LOG.info('Changing output to influxdb')
            self._change_output_to_influxdb(ip, port)

            LOG.info('Config influxdb')
            self._config_influxdb(port)

            container_handler.update_attr(container_id, 'status', 1)

            LOG.info('Finished')
        except Exception:
            container_handler.update_attr(container_id, 'status', 2)
            LOG.exception('Creating influxdb failed')

    def _create_influxdb_container(self, client, name, port):

        ports = [port]
        port_bindings = {8086: port}
        restart_policy = {"MaximumRetryCount": 0, "Name": "always"}
        host_config = client.create_host_config(port_bindings=port_bindings,
                                                restart_policy=restart_policy)

        LOG.info('Creating container')
        container = client.create_container(image='%s:%s' %
                                            (consts.INFLUXDB_IMAGE,
                                             consts.INFLUXDB_TAG),
                                            ports=ports,
                                            name=name,
                                            detach=True,
                                            tty=True,
                                            host_config=host_config)
        LOG.info('Starting container')
        client.start(container)
        return container

    def _config_influxdb(self, port):
        try:
            client = influx.get_data_db_client()
            client.create_user(consts.INFLUXDB_USER,
                               consts.INFLUXDB_PASS,
                               consts.INFLUXDB_DB_NAME)
            client.create_database(consts.INFLUXDB_DB_NAME)
            LOG.info('Success to config influxDB')
        except Exception:
            LOG.exception('Config influxdb failed')

    def _change_output_to_influxdb(self, ip, port):
        utils.makedirs(consts.CONF_DIR)

        parser = configparser.ConfigParser()
        LOG.info('Reading output sample configuration')
        parser.read(consts.CONF_SAMPLE_FILE)

        LOG.info('Set dispatcher to influxdb')
        parser.set('DEFAULT', 'dispatcher', 'influxdb')
        parser.set('dispatcher_influxdb', 'target',
                   'http://{}:{}'.format(ip, port))

        LOG.info('Writing to %s', consts.CONF_FILE)
        with open(consts.CONF_FILE, 'w') as f:
            parser.write(f)
