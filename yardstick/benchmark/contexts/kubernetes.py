##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
import logging
import time
import pkg_resources

import paramiko

from yardstick.benchmark.contexts.base import Context
from yardstick.orchestrator.kubernetes import KubernetesTemplate
from yardstick.common import kubernetes_utils as k8s_utils
from yardstick.common import utils

LOG = logging.getLogger(__name__)
BITS_LENGTH = 2048


class KubernetesContext(Context):
    """Class that handle nodes info"""

    __context_type__ = "Kubernetes"

    def __init__(self):
        self.name = ''
        self.ssh_key = ''
        self.key_path = ''
        self.public_key_path = ''
        self.template = None

        super(KubernetesContext, self).__init__()

    def init(self, attrs):
        self.name = attrs.get('name', '')

        template_cfg = attrs.get('servers', {})
        self.template = KubernetesTemplate(self.name, template_cfg)

        self.ssh_key = '{}-key'.format(self.name)

        self.key_path = self._get_key_path()
        self.public_key_path = '{}.pub'.format(self.key_path)

    def deploy(self):
        LOG.info('Creating ssh key')
        self._set_ssh_key()

        LOG.info('Launch containers')
        self._create_rcs()
        time.sleep(1)
        self.template.get_rc_pods()

        self._wait_until_running()

    def undeploy(self):
        self._delete_ssh_key()
        self._delete_rcs()
        self._delete_pods()

        super(KubernetesContext, self).undeploy()

    def _wait_until_running(self):
        while not all(self._check_pod_status(p) for p in self.template.pods):
            time.sleep(1)

    def _check_pod_status(self, pod):
        status = k8s_utils.read_pod_status(pod)
        LOG.debug('%s:%s', pod, status)
        if status == 'Failed':
            LOG.error('Pod %s status is failed', pod)
            raise RuntimeError
        if status != 'Running':
            return False
        return True

    def _create_rcs(self):
        for obj in self.template.k8s_objs:
            self._create_rc(obj.get_template())

    def _create_rc(self, template):
        k8s_utils.create_replication_controller(template)

    def _delete_rcs(self):
        for rc in self.template.rcs:
            self._delete_rc(rc)

    def _delete_rc(self, rc):
        k8s_utils.delete_replication_controller(rc)

    def _delete_pods(self):
        for pod in self.template.pods:
            self._delete_pod(pod)

    def _delete_pod(self, pod):
        k8s_utils.delete_pod(pod)

    def _get_key_path(self):
        task_id = self.name.split('-')[-1]
        k = 'files/yardstick_key-{}'.format(task_id)
        return pkg_resources.resource_filename('yardstick.resources', k)

    def _set_ssh_key(self):
        rsa_key = paramiko.RSAKey.generate(bits=BITS_LENGTH)

        LOG.info('Writing private key')
        rsa_key.write_private_key_file(self.key_path)

        LOG.info('Writing public key')
        key = '{} {}\n'.format(rsa_key.get_name(), rsa_key.get_base64())
        with open(self.public_key_path, 'w') as f:
            f.write(key)

        LOG.info('Create configmap for ssh key')
        k8s_utils.create_config_map(self.ssh_key, {'authorized_keys': key})

    def _delete_ssh_key(self):
        k8s_utils.delete_config_map(self.ssh_key)
        utils.remove_file(self.key_path)
        utils.remove_file(self.public_key_path)

    def _get_server(self, name):
        resp = k8s_utils.get_pod_list()
        hosts = ({'name': n.metadata.name,
                  'ip': n.status.pod_ip,
                  'user': 'root',
                  'key_filename': self.key_path,
                  'private_ip': n.status.pod_ip}
                 for n in resp.items if n.metadata.name.startswith(name))

        return next(hosts, None)

    def _get_network(self, attr_name):
        return None
