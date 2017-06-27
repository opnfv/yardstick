##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
import logging
import os
import time

import paramiko
from kubernetes import client
from kubernetes import config

from yardstick.benchmark.contexts.base import Context
from yardstick.orchestrator.kubernetes import KubernetesObject
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)


class KubernetesContext(Context):
    """Class that handle nodes info"""

    __context_type__ = "Kubernetes"

    def __init__(self):
        self.name = ''
        self.servers = {}
        self.task_id = ''
        self.key_path = ''
        self.ssh_key = ''

        config.load_kube_config(config_file='/root/admin.conf')
        self.instance = client.CoreV1Api()

        super(KubernetesContext, self).__init__()

    def init(self, attrs):
        self.name = attrs.get('name', '')
        self.servers = attrs.get('servers', {})
        self.ssh_key = '{}-key'.format(self.name)

        self.task_id = self.name.split('-')[-1]
        k = 'yardstick/resources/files/yardstick_key-{}'.format(self.task_id)
        self.key_path = os.path.join(consts.YARDSTICK_ROOT_PATH, k)

    def deploy(self):
        LOG.info('Creating ssh key')
        self._set_ssh_key()

        LOG.info('Launch containers')
        for server in self.servers:
            server = '{}-{}'.format(server, self.name)
            kubernetes_obj = KubernetesObject(server, ssh_key=self.ssh_key)
            template = kubernetes_obj.get_template()
            self.instance.create_namespaced_replication_controller(
                body=template, namespace="default")

        time.sleep(60)

    def _delete_containers(self):
        body = client.V1DeleteOptions()
        for server in self.servers:
            server = '{}-{}'.format(server, self.name)
            self.instance.delete_namespaced_replication_controller(server,
                                                                   'default',
                                                                   body)

        self._delete_pods()

    def _delete_pods(self):
        resp = self.instance.list_namespaced_pod(namespace='default')
        servers = ['{}-{}'.format(s, self.name) for s in self.servers]
        pods = [p.metadata.name for p in resp.items for s in servers
                if p.metadata.name.startswith(s)]

        body = client.V1DeleteOptions()
        for pod in pods:
            self.instance.delete_namespaced_pod(pod, 'default', body)

    def _set_ssh_key(self):
        rsa_key = paramiko.RSAKey.generate(bits=2048)

        LOG.info('Writing private key')
        rsa_key.write_private_key_file(self.key_path)

        LOG.info('Writing public key')
        public_key_path = '{}.pub'.format(self.key_path)
        with open(public_key_path, 'w') as f:
            key = '{} {}\n'.format(rsa_key.get_name(), rsa_key.get_base64())
            f.write(key)

        LOG.info('Create configmap for ssh key')
        metadata = client.V1ObjectMeta(name=self.ssh_key)
        body = client.V1ConfigMap(data={'authorized_keys': key},
                                  metadata=metadata)
        self.instance.create_namespaced_config_map('default', body)

    def _delete_ssh_key(self):
        body = client.V1DeleteOptions()
        self.instance.delete_namespaced_config_map(self.ssh_key,
                                                   'default',
                                                   body)

    def _remove_key_file(self):
        public_key_path = '{}.pub'.format(self.key_path)
        os.remove(self.key_path)
        os.remove(public_key_path)

    def undeploy(self):
        self._delete_ssh_key()
        self._delete_containers()
        self._remove_key_file()

    def _get_server(self, name):
        resp = self.instance.list_namespaced_pod(namespace='default')
        hosts = ({'name': n.metadata.name,
                  'ip': n.status.pod_ip,
                  'user': 'root',
                  'key_filename': self.key_path,
                  'private_ip': n.status.pod_ip}
                 for n in resp.items if n.metadata.name.startswith(name))

        try:
            return next(hosts)
        except StopIteration:
            return None
