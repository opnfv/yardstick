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
import logging
import os
import subprocess
import threading
import time
import uuid
import glob
import yaml
import collections

from six.moves import configparser
from oslo_serialization import jsonutils
from docker import Client

from api.database.v1.handlers import AsyncTaskHandler
from api.utils import influx
from api import ApiResource
from yardstick.common import constants as consts
from yardstick.common import utils
from yardstick.common.utils import result_handler
from yardstick.common import openstack_utils
from yardstick.common.httpClient import HttpClient
from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

async_handler = AsyncTaskHandler()


class V1Env(ApiResource):

    def post(self):
        return self._dispatch_post()

    def create_grafana(self, args):
        task_id = str(uuid.uuid4())

        thread = threading.Thread(target=self._create_grafana, args=(task_id,))
        thread.start()

        return result_handler(consts.API_SUCCESS, {'task_id': task_id})

    def _create_grafana(self, task_id):
        self._create_task(task_id)

        client = Client(base_url=consts.DOCKER_URL)

        try:
            LOG.info('Checking if grafana image exist')
            image = '{}:{}'.format(consts.GRAFANA_IMAGE, consts.GRAFANA_TAG)
            if not self._check_image_exist(client, image):
                LOG.info('Grafana image not exist, start pulling')
                client.pull(consts.GRAFANA_IMAGE, consts.GRAFANA_TAG)

            LOG.info('Createing grafana container')
            container = self._create_grafana_container(client)
            LOG.info('Grafana container is created')

            time.sleep(5)

            container = client.inspect_container(container['Id'])
            ip = container['NetworkSettings']['Networks']['bridge']['IPAddress']
            LOG.debug('container ip is: %s', ip)

            LOG.info('Creating data source for grafana')
            self._create_data_source(ip)

            LOG.info('Creating dashboard for grafana')
            self._create_dashboard(ip)

            self._update_task_status(task_id)
            LOG.info('Finished')
        except Exception as e:
            self._update_task_error(task_id, str(e))
            LOG.exception('Create grafana failed')

    def _create_dashboard(self, ip):
        url = 'http://admin:admin@{}:{}/api/dashboards/db'.format(ip, consts.GRAFANA_PORT)
        path = os.path.join(consts.REPOS_DIR, 'dashboard', 'opnfv_yardstick_tc*.json')

        for i in sorted(glob.iglob(path)):
            with open(i) as f:
                data = jsonutils.load(f)
            try:
                HttpClient().post(url, {"dashboard": data})
            except Exception:
                LOG.exception('Create dashboard %s failed', i)
                raise

    def _create_data_source(self, ip):
        url = 'http://admin:admin@{}:{}/api/datasources'.format(ip, consts.GRAFANA_PORT)
        influx_conf = utils.parse_ini_file(consts.CONF_FILE)

        try:
            influx_url = influx_conf['dispatcher_influxdb']['target']
        except KeyError:
            LOG.exception('influxdb url not set in yardstick.conf')
            raise

        data = {
            "name": "yardstick",
            "type": "influxdb",
            "access": "proxy",
            "url": influx_url,
            "password": "root",
            "user": "root",
            "database": "yardstick",
            "basicAuth": True,
            "basicAuthUser": "admin",
            "basicAuthPassword": "admin",
            "isDefault": True,
        }
        try:
            HttpClient().post(url, data)
        except Exception:
            LOG.exception('Create datasources failed')
            raise

    def _create_grafana_container(self, client):
        ports = [consts.GRAFANA_PORT]
        port_bindings = {consts.GRAFANA_PORT: consts.GRAFANA_MAPPING_PORT}
        restart_policy = {"MaximumRetryCount": 0, "Name": "always"}
        host_config = client.create_host_config(port_bindings=port_bindings,
                                                restart_policy=restart_policy)

        LOG.info('Creating container')
        container = client.create_container(image='%s:%s' %
                                            (consts.GRAFANA_IMAGE,
                                             consts.GRAFANA_TAG),
                                            ports=ports,
                                            detach=True,
                                            tty=True,
                                            host_config=host_config)
        LOG.info('Starting container')
        client.start(container)
        return container

    def _check_image_exist(self, client, t):
        return any(t in a['RepoTags'][0]
                   for a in client.images() if a['RepoTags'])

    def create_influxdb(self, args):
        task_id = str(uuid.uuid4())

        thread = threading.Thread(target=self._create_influxdb, args=(task_id,))
        thread.start()

        return result_handler(consts.API_SUCCESS, {'task_id': task_id})

    def _create_influxdb(self, task_id):
        self._create_task(task_id)

        client = Client(base_url=consts.DOCKER_URL)

        try:
            LOG.info('Checking if influxdb image exist')
            if not self._check_image_exist(client, '%s:%s' %
                                           (consts.INFLUXDB_IMAGE,
                                            consts.INFLUXDB_TAG)):
                LOG.info('Influxdb image not exist, start pulling')
                client.pull(consts.INFLUXDB_IMAGE, tag=consts.INFLUXDB_TAG)

            LOG.info('Createing influxdb container')
            container = self._create_influxdb_container(client)
            LOG.info('Influxdb container is created')

            time.sleep(5)

            container = client.inspect_container(container['Id'])
            ip = container['NetworkSettings']['Networks']['bridge']['IPAddress']
            LOG.debug('container ip is: %s', ip)

            LOG.info('Changing output to influxdb')
            self._change_output_to_influxdb(ip)

            LOG.info('Config influxdb')
            self._config_influxdb()

            self._update_task_status(task_id)

            LOG.info('Finished')
        except Exception as e:
            self._update_task_error(task_id, str(e))
            LOG.exception('Creating influxdb failed')

    def _create_influxdb_container(self, client):

        ports = [consts.INFLUXDB_DASHBOARD_PORT, consts.INFLUXDB_PORT]
        port_bindings = {k: k for k in ports}
        restart_policy = {"MaximumRetryCount": 0, "Name": "always"}
        host_config = client.create_host_config(port_bindings=port_bindings,
                                                restart_policy=restart_policy)

        LOG.info('Creating container')
        container = client.create_container(image='%s:%s' %
                                            (consts.INFLUXDB_IMAGE,
                                             consts.INFLUXDB_TAG),
                                            ports=ports,
                                            detach=True,
                                            tty=True,
                                            host_config=host_config)
        LOG.info('Starting container')
        client.start(container)
        return container

    def _config_influxdb(self):
        try:
            client = influx.get_data_db_client()
            client.create_user(consts.INFLUXDB_USER,
                               consts.INFLUXDB_PASS,
                               consts.INFLUXDB_DB_NAME)
            client.create_database(consts.INFLUXDB_DB_NAME)
            LOG.info('Success to config influxDB')
        except Exception:
            LOG.exception('Config influxdb failed')

    def _change_output_to_influxdb(self, ip):
        utils.makedirs(consts.CONF_DIR)

        parser = configparser.ConfigParser()
        LOG.info('Reading output sample configuration')
        parser.read(consts.CONF_SAMPLE_FILE)

        LOG.info('Set dispatcher to influxdb')
        parser.set('DEFAULT', 'dispatcher', 'influxdb')
        parser.set('dispatcher_influxdb', 'target',
                   'http://{}:{}'.format(ip, consts.INFLUXDB_PORT))

        LOG.info('Writing to %s', consts.CONF_FILE)
        with open(consts.CONF_FILE, 'w') as f:
            parser.write(f)

    def prepare_env(self, args):
        task_id = str(uuid.uuid4())

        thread = threading.Thread(target=self._prepare_env_daemon,
                                  args=(task_id,))
        thread.start()

        return result_handler(consts.API_SUCCESS, {'task_id': task_id})

    def _already_source_openrc(self):
        """Check if openrc is sourced already"""
        return all(os.environ.get(k) for k in ['OS_AUTH_URL',
                                               'OS_USERNAME',
                                               'OS_PASSWORD',
                                               'EXTERNAL_NETWORK'])

    def _prepare_env_daemon(self, task_id):
        self._create_task(task_id)

        try:
            self._create_directories()

            rc_file = consts.OPENRC

            LOG.info('Checkout Openrc Environment variable')
            if not self._already_source_openrc():
                LOG.info('Openrc variable not found in Environment')
                if not os.path.exists(rc_file):
                    LOG.info('Openrc file not found')
                    installer_ip = os.environ.get('INSTALLER_IP',
                                                  '192.168.200.2')
                    installer_type = os.environ.get('INSTALLER_TYPE', 'compass')
                    LOG.info('Getting openrc file from %s', installer_type)
                    self._get_remote_rc_file(rc_file,
                                             installer_ip,
                                             installer_type)
                    LOG.info('Source openrc file')
                    self._source_file(rc_file)
                    LOG.info('Appending external network')
                    self._append_external_network(rc_file)
                LOG.info('Openrc file exist, source openrc file')
                self._source_file(rc_file)

            LOG.info('Cleaning images')
            self._clean_images()

            LOG.info('Loading images')
            self._load_images()

            self._update_task_status(task_id)
            LOG.info('Finished')
        except Exception as e:
            self._update_task_error(task_id, str(e))
            LOG.exception('Prepare env failed')

    def _create_directories(self):
        utils.makedirs(consts.CONF_DIR)

    def _source_file(self, rc_file):
        utils.source_env(rc_file)

    def _get_remote_rc_file(self, rc_file, installer_ip, installer_type):

        os_fetch_script = os.path.join(consts.RELENG_DIR, consts.FETCH_SCRIPT)

        try:
            cmd = [os_fetch_script, '-d', rc_file, '-i', installer_type,
                   '-a', installer_ip]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            p.communicate()

            if p.returncode != 0:
                LOG.error('Failed to fetch credentials from installer')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def _append_external_network(self, rc_file):
        neutron_client = openstack_utils.get_neutron_client()
        networks = neutron_client.list_networks()['networks']
        try:
            ext_network = next(n['name']
                               for n in networks if n['router:external'])
        except StopIteration:
            LOG.warning("Can't find external network")
        else:
            cmd = 'export EXTERNAL_NETWORK=%s' % ext_network
            try:
                with open(rc_file, 'a') as f:
                    f.write(cmd + '\n')
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

    def _clean_images(self):
        cmd = [consts.CLEAN_IMAGES_SCRIPT]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=consts.REPOS_DIR)
        output = p.communicate()[0]
        LOG.debug(output)

    def _load_images(self):
        cmd = [consts.LOAD_IMAGES_SCRIPT]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=consts.REPOS_DIR)
        output = p.communicate()[0]
        LOG.debug(output)

    def _create_task(self, task_id):
        async_handler.insert({'status': 0, 'task_id': task_id})

    def _update_task_status(self, task_id):
        async_handler.update_attr(task_id, {'status': 1})

    def _update_task_error(self, task_id, error):
        async_handler.update_attr(task_id, {'status': 2, 'error': error})

    def update_openrc(self, args):
        try:
            openrc_vars = args['openrc']
        except KeyError:
            return result_handler(consts.API_ERROR, 'openrc must be provided')
        else:
            if not isinstance(openrc_vars, collections.Mapping):
                return result_handler(consts.API_ERROR, 'args should be a dict')

        lines = ['export {}={}\n'.format(k, v) for k, v in openrc_vars.items()]
        LOG.debug('Writing: %s', ''.join(lines))

        LOG.info('Writing openrc: Writing')
        utils.makedirs(consts.CONF_DIR)

        with open(consts.OPENRC, 'w') as f:
            f.writelines(lines)
        LOG.info('Writing openrc: Done')

        LOG.info('Source openrc: Sourcing')
        try:
            self._source_file(consts.OPENRC)
        except Exception as e:
            LOG.exception('Failed to source openrc')
            return result_handler(consts.API_ERROR, str(e))
        LOG.info('Source openrc: Done')

        return result_handler(consts.API_SUCCESS, {'openrc': openrc_vars})

    def upload_pod_file(self, args):
        try:
            pod_file = args['file']
        except KeyError:
            return result_handler(consts.API_ERROR, 'file must be provided')

        LOG.info('Checking file')
        data = yaml_load(pod_file.read())
        if not isinstance(data, collections.Mapping):
            return result_handler(consts.API_ERROR, 'invalid yaml file')

        LOG.info('Writing file')
        with open(consts.POD_FILE, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        LOG.info('Writing finished')

        return result_handler(consts.API_SUCCESS, {'pod_info': data})

    def update_pod_file(self, args):
        try:
            pod_dic = args['pod']
        except KeyError:
            return result_handler(consts.API_ERROR, 'pod must be provided')
        else:
            if not isinstance(pod_dic, collections.Mapping):
                return result_handler(consts.API_ERROR, 'pod should be a dict')

        LOG.info('Writing file')
        with open(consts.POD_FILE, 'w') as f:
            yaml.dump(pod_dic, f, default_flow_style=False)
        LOG.info('Writing finished')

        return result_handler(consts.API_SUCCESS, {'pod_info': pod_dic})

    def update_hosts(self, hosts_ip):
        if not isinstance(hosts_ip, collections.Mapping):
            return result_handler(consts.API_ERROR, 'args should be a dict')
        LOG.info('Writing hosts: Writing')
        LOG.debug('Writing: %s', hosts_ip)
        cmd = ["sudo", "python", "write_hosts.py"]
        p = subprocess.Popen(cmd,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             cwd=os.path.join(consts.REPOS_DIR,
                                              "api/resources"))
        _, err = p.communicate(jsonutils.dumps(hosts_ip))
        if p.returncode != 0:
            return result_handler(consts.API_ERROR, err)
        LOG.info('Writing hosts: Done')
        return result_handler(consts.API_SUCCESS, 'success')
