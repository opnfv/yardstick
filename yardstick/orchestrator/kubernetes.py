##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import copy

from oslo_serialization import jsonutils

from yardstick.common import constants
from yardstick.common import exceptions
from yardstick.common import kubernetes_utils as k8s_utils
from yardstick.common import utils


class ContainerObject(object):

    SSH_MOUNT_PATH = '/tmp/.ssh/'
    IMAGE_DEFAULT = 'openretriever/yardstick'
    COMMAND_DEFAULT = '/bin/bash'

    def __init__(self, name, ssh_key, **kwargs):
        self._name = name
        self._ssh_key = ssh_key
        self._image = kwargs.get('image', self.IMAGE_DEFAULT)
        self._command = [kwargs.get('command', self.COMMAND_DEFAULT)]
        self._args = kwargs.get('args', [])
        self._volume_mounts = kwargs.get('volumeMounts', [])
        self._security_context = kwargs.get('securityContext')

    def _create_volume_mounts(self):
        """Return all "volumeMounts" items per container"""
        volume_mounts_items = [self._create_volume_mounts_item(vol)
                               for vol in self._volume_mounts]
        ssh_vol = {'name': self._ssh_key,
                   'mountPath': self.SSH_MOUNT_PATH}
        volume_mounts_items.append(self._create_volume_mounts_item(ssh_vol))
        return volume_mounts_items

    @staticmethod
    def _create_volume_mounts_item(volume_mount):
        """Create a "volumeMounts" item"""
        return {'name': volume_mount['name'],
                'mountPath': volume_mount['mountPath'],
                'readOnly': volume_mount.get('readOnly', False)}

    def get_container_item(self):
        """Create a "container" item"""
        container_name = '{}-container'.format(self._name)
        container = {'args': self._args,
                     'command': self._command,
                     'image': self._image,
                     'name': container_name,
                     'volumeMounts': self._create_volume_mounts()}
        if self._security_context:
            container['securityContext'] = self._security_context
        return container


class ReplicationControllerObject(object):

    SSHKEY_DEFAULT = 'yardstick_key'

    def __init__(self, name, **kwargs):
        super(ReplicationControllerObject, self).__init__()
        parameters = copy.deepcopy(kwargs)
        self.name = name
        self.node_selector = parameters.pop('nodeSelector', {})
        self.ssh_key = parameters.pop('ssh_key', self.SSHKEY_DEFAULT)
        self._volumes = parameters.pop('volumes', [])
        self._security_context = parameters.pop('securityContext', None)
        self._networks = parameters.pop('networks', [])

        containers = parameters.pop('containers', None)
        if containers:
            self._containers = [
                ContainerObject(self.name, self.ssh_key, **container)
                for container in containers]
        else:
            self._containers = [
                ContainerObject(self.name, self.ssh_key, **parameters)]

        self.template = {
            "apiVersion": "v1",
            "kind": "ReplicationController",
            "metadata": {
                "name": ""
            },
            "spec": {
                "replicas": 1,
                "template": {
                    "metadata": {
                        "labels": {"app": name}
                    },
                    "spec": {
                        "containers": [],
                        "volumes": [],
                        "nodeSelector": {}
                    }
                }
            }
        }

        self._change_value_according_name(name)
        self._add_containers()
        self._add_node_selector()
        self._add_volumes()
        self._add_security_context()
        self._add_networks()

    def get_template(self):
        return self.template

    def _change_value_according_name(self, name):
        utils.set_dict_value(self.template, 'metadata.name', name)

        utils.set_dict_value(self.template,
                             'spec.template.metadata.labels.app',
                             name)

    def _add_containers(self):
        containers = [container.get_container_item()
                      for container in self._containers]
        utils.set_dict_value(self.template,
                             'spec.template.spec.containers',
                             containers)

    def _add_node_selector(self):
        utils.set_dict_value(self.template,
                             'spec.template.spec.nodeSelector',
                             self.node_selector)

    def _add_volumes(self):
        """Add "volume" items to container specs, including the SSH one"""
        volume_items = [self._create_volume_item(vol) for vol in self._volumes]
        volume_items.append(self._create_ssh_key_volume())
        utils.set_dict_value(self.template,
                             'spec.template.spec.volumes',
                             volume_items)

    def _create_ssh_key_volume(self):
        """Create a "volume" item of type "configMap" for the SSH key"""
        return {'name': self.ssh_key,
                'configMap': {'name': self.ssh_key}}

    @staticmethod
    def _create_volume_item(volume):
        """Create a "volume" item"""
        volume = copy.deepcopy(volume)
        name = volume.pop('name')
        for key in (k for k in volume if k in k8s_utils.get_volume_types()):
            type_name = key
            type_data = volume[key]
            break
        else:
            raise exceptions.KubernetesTemplateInvalidVolumeType(volume=volume)

        return {'name': name,
                type_name: type_data}

    def _add_security_context(self):
        if self._security_context:
            utils.set_dict_value(self.template,
                                 'spec.template.spec.securityContext',
                                 self._security_context)

    def _add_networks(self):
        networks = []
        for net in self._networks:
            networks.append({'name': net})

        if not networks:
            return

        annotations = {'networks': jsonutils.dumps(networks)}
        utils.set_dict_value(self.template,
                             'spec.template.metadata.annotations',
                             annotations)


class ServiceNodePortObject(object):

    def __init__(self, name, **kwargs):
        """Service kind "NodePort" object

        :param name: (string) name of the Service
        :param kwargs: (dict) node_ports -> (list) port, name, targetPort,
                                                   nodePort
        """
        self._name = '{}-service'.format(name)
        self.template = {
            'metadata': {'name': '{}-service'.format(name)},
            'spec': {
                'type': 'NodePort',
                'ports': [],
                'selector': {'app': name}
            }
        }

        self._add_port(22, protocol='TCP')
        node_ports = copy.deepcopy(kwargs.get('node_ports', []))
        for port in node_ports:
            port_number = port.pop('port')
            self._add_port(port_number, **port)

    def _add_port(self, port, protocol=None, name=None, targetPort=None,
                  nodePort=None):
        _port = {'port': port}
        if protocol:
            _port['protocol'] = protocol
        if name:
            _port['name'] = name
        if targetPort:
            _port['targetPort'] = targetPort
        if nodePort:
            _port['nodePort'] = nodePort
        self.template['spec']['ports'].append(_port)

    def create(self):
        k8s_utils.create_service(self.template)

    def delete(self):
        k8s_utils.delete_service(self._name)


class CustomResourceDefinitionObject(object):

    MANDATORY_PARAMETERS = {'name'}

    def __init__(self, ctx_name, **kwargs):
        if not self.MANDATORY_PARAMETERS.issubset(kwargs):
            missing_parameters = ', '.join(
                str(param) for param in
                (self.MANDATORY_PARAMETERS - set(kwargs)))
            raise exceptions.KubernetesCRDObjectDefinitionError(
                missing_parameters=missing_parameters)

        singular = kwargs['name']
        plural = singular + 's'
        kind = singular.title()
        version = kwargs.get('version', 'v1')
        scope = kwargs.get('scope', constants.SCOPE_NAMESPACED)
        group = ctx_name + '.com'
        self._name = metadata_name = plural + '.' + group

        self._template = {
            'metadata': {
                'name': metadata_name
            },
            'spec': {
                'group': group,
                'version': version,
                'scope': scope,
                'names': {'plural': plural,
                          'singular': singular,
                          'kind': kind}
            }
        }

    def create(self):
        k8s_utils.create_custom_resource_definition(self._template)

    def delete(self):
        k8s_utils.delete_custom_resource_definition(self._name)


class NetworkObject(object):

    MANDATORY_PARAMETERS = {'name', 'plugin', 'args'}
    KIND = 'Network'

    def __init__(self, **kwargs):
        if not self.MANDATORY_PARAMETERS.issubset(kwargs):
            missing_parameters = ', '.join(
                str(param) for param in
                (self.MANDATORY_PARAMETERS - set(kwargs)))
            raise exceptions.KubernetesNetworkObjectDefinitionError(
                missing_parameters=missing_parameters)

        self._name = kwargs['name']
        self._plugin = kwargs['plugin']
        self._args = kwargs['args']
        self._crd = None
        self._template = None
        self._group = None
        self._version = None
        self._plural = None
        self._scope = None

    @property
    def crd(self):
        if self._crd:
            return self._crd
        crd = k8s_utils.get_custom_resource_definition(self.KIND)
        if not crd:
            raise exceptions.KubernetesNetworkObjectKindMissing()
        self._crd = crd
        return self._crd

    @property
    def group(self):
        if self._group:
            return self._group
        self._group = self.crd.spec.group
        return self._group

    @property
    def version(self):
        if self._version:
            return self._version
        self._version = self.crd.spec.version
        return self._version

    @property
    def plural(self):
        if self._plural:
            return self._plural
        self._plural = self.crd.spec.names.plural
        return self._plural

    @property
    def scope(self):
        if self._scope:
            return self._scope
        self._scope = self.crd.spec.scope
        return self._scope

    @property
    def template(self):
        """"Network" object template

        This template can be rendered only once the CRD "Network" is created in
        Kubernetes. This function call must be delayed until the creation of
        the CRD "Network".
        """
        if self._template:
            return self._template

        self._template = {
            'apiVersion': '{}/{}'.format(self.group, self.version),
            'kind': self.KIND,
            'metadata': {
                'name': self._name
            },
            'plugin': self._plugin,
            'args': self._args
        }
        return self._template

    def create(self):
        k8s_utils.create_network(self.scope, self.group, self.version,
                                 self.plural, self.template)

    def delete(self):
        k8s_utils.delete_network(self.scope, self.group, self.version,
                                 self.plural, self._name)


class KubernetesTemplate(object):

    def __init__(self, name, context_cfg):
        """KubernetesTemplate object initialization

        :param name: (str) name of the Kubernetes context
        :param context_cfg: (dict) context definition
        """
        context_cfg = copy.deepcopy(context_cfg)
        servers_cfg = context_cfg.pop('servers', {})
        crd_cfg = context_cfg.pop('custom_resources', [])
        networks_cfg = context_cfg.pop('networks', [])
        self.name = name
        self.ssh_key = '{}-key'.format(name)

        self.rcs = {self._get_rc_name(rc): cfg
                    for rc, cfg in servers_cfg.items()}
        self.k8s_objs = [ReplicationControllerObject(
            rc, ssh_key=self.ssh_key, **cfg) for rc, cfg in self.rcs.items()]
        self.service_objs = [ServiceNodePortObject(rc, **cfg)
                             for rc, cfg in self.rcs.items()]
        self.crd = [CustomResourceDefinitionObject(self.name, **crd)
                    for crd in crd_cfg]
        self.network_objs = [NetworkObject(**nobj) for nobj in networks_cfg]
        self.pods = []

    def _get_rc_name(self, rc_name):
        return '{}-{}'.format(rc_name, self.name)

    def get_rc_pods(self):
        resp = k8s_utils.get_pod_list()
        self.pods = [p.metadata.name for p in resp.items for s in self.rcs
                     if p.metadata.name.startswith(s)]

        return self.pods
