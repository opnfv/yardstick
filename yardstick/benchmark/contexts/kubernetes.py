##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import collections
import logging
import pkg_resources
import time

import paramiko

from yardstick.benchmark import contexts
from yardstick.benchmark.contexts import base as ctx_base
from yardstick.benchmark.contexts import model
from yardstick.common import constants
from yardstick.common import exceptions
from yardstick.common import kubernetes_utils as k8s_utils
from yardstick.common import utils
from yardstick.orchestrator import kubernetes


LOG = logging.getLogger(__name__)
BITS_LENGTH = 2048


class KubernetesContext(ctx_base.Context):
    """Class that handle nodes info"""

    __context_type__ = contexts.CONTEXT_KUBERNETES

    def __init__(self):
        self.ssh_key = ''
        self.key_path = ''
        self.public_key_path = ''
        self.template = None
        super(KubernetesContext, self).__init__(host_name_separator='-')

    def init(self, attrs):
        super(KubernetesContext, self).init(attrs)

        networks = attrs.get('networks', {})
        self.template = kubernetes.KubernetesTemplate(self.name, attrs)
        self.ssh_key = '{}-key'.format(self.name)
        self.key_path = self._get_key_path()
        self.public_key_path = '{}.pub'.format(self.key_path)
        self._networks = collections.OrderedDict(
            (net_name, model.Network(net_name, self, network))
            for net_name, network in networks.items())

    def deploy(self):
        LOG.info('Creating ssh key')
        self._set_ssh_key()

        self._create_crd()
        self._create_networks()
        LOG.info('Launch containers')
        self._create_rcs()
        self._create_services()
        time.sleep(1)
        self.template.get_rc_pods()

        self._wait_until_running()

    def undeploy(self):
        self._delete_ssh_key()
        self._delete_rcs()
        self._delete_pods()
        self._delete_services()
        self._delete_networks()
        self._delete_crd()

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

    def _create_services(self):
        for obj in self.template.service_objs:
            obj.create()

    def _delete_services(self):
        for obj in self.template.service_objs:
            obj.delete()

    def _create_rcs(self):
        for obj in self.template.rc_objs:
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
        k8s_utils.delete_pod(pod, skip_codes=[404])

    def _create_crd(self):
        LOG.info('Create Custom Resource Definition elements')
        for crd in self.template.crd:
            crd.create()

    def _delete_crd(self):
        LOG.info('Delete Custom Resource Definition elements')
        for crd in self.template.crd:
            crd.delete()

    def _create_networks(self):  # pragma: no cover
        LOG.info('Create Network elements')
        for net in self.template.network_objs:
            net.create()

    def _delete_networks(self):  # pragma: no cover
        LOG.info('Create Network elements')
        for net in self.template.network_objs:
            net.delete()

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
        k8s_utils.delete_config_map(self.ssh_key, skip_codes=[404])
        utils.remove_file(self.key_path)
        utils.remove_file(self.public_key_path)

    def _get_server(self, name):
        node_ports = self._get_service_ports(name)
        for sn_port in (sn_port for sn_port in node_ports
                        if sn_port['port'] == constants.SSH_PORT):
            node_port = sn_port['node_port']
            break
        else:
            raise exceptions.KubernetesSSHPortNotDefined()

        return {
            'name': name,
            'ip': self._get_node_ip(),
            'private_ip': k8s_utils.get_pod_by_name(name).status.pod_ip,
            'ssh_port': node_port,
            'user': 'root',
            'key_filename': self.key_path,
            'interfaces': self._get_interfaces(name),
            'service_ports': node_ports
        }

    def _get_network(self, net_name):
        """Retrieves the network object, searching by name

        :param net_name: (str) replication controller name
        :return: (dict) network information (name)
        """
        network = self._networks.get(net_name)
        if not network:
            return
        return {'name': net_name}

    def _get_interfaces(self, rc_name):
        """Retrieves the network list of a replication controller

        :param rc_name: (str) replication controller name
        :return: (dict) names and information of the networks used in this
                 replication controller; those networks must be defined in the
                 Kubernetes cluster
        """
        rc = self.template.get_rc_by_name(rc_name)
        if not rc:
            return {}
        return {name: {'network_name': name,
                       'local_mac': None,
                       'local_ip': None}
                for name in rc.networks}

    def _get_node_ip(self):
        return k8s_utils.get_node_list().items[0].status.addresses[0].address

    def _get_physical_nodes(self):
        return None

    def _get_physical_node_for_server(self, server_name):
        return None

    def _get_service_ports(self, name):
        service_name = '{}-service'.format(name)
        service = k8s_utils.get_service_by_name(service_name)
        if not service:
            raise exceptions.KubernetesServiceObjectNotDefined()
        ports = []
        for port in service.ports:
            ports.append({'name': port.name,
                          'node_port': port.node_port,
                          'port': port.port,
                          'protocol': port.protocol,
                          'target_port': port.target_port})
        return ports
