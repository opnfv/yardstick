##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import copy

from yardstick.common import exceptions
from yardstick.common import utils
from yardstick.common import kubernetes_utils as k8s_utils


class KubernetesObject(object):

    SSH_MOUNT_PATH = '/tmp/.ssh/'

    def __init__(self, name, **kwargs):
        super(KubernetesObject, self).__init__()
        self.name = name
        self.image = kwargs.get('image', 'openretriever/yardstick')
        self.command = [kwargs.get('command', '/bin/bash')]
        self.args = kwargs.get('args', [])
        self.ssh_key = kwargs.get('ssh_key', 'yardstick_key')
        self.node_selector = kwargs.get('nodeSelector', {})
        self._volumes = kwargs.get('volumes', [])
        self._volume_mounts = kwargs.get('volumeMounts', [])

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
                        "labels": {
                            "app": name
                        }
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

    def get_template(self):
        return self.template

    def _change_value_according_name(self, name):
        utils.set_dict_value(self.template, 'metadata.name', name)

        utils.set_dict_value(self.template,
                             'spec.template.metadata.labels.app',
                             name)

    def _add_containers(self):
        containers = [self._add_container()]
        utils.set_dict_value(self.template,
                             'spec.template.spec.containers',
                             containers)

    def _add_container(self):
        container_name = '{}-container'.format(self.name)
        return {'args': self.args,
                'command': self.command,
                'image': self.image,
                'name': container_name,
                'volumeMounts': self._create_volume_mounts()}

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

    def _create_volume_mounts(self):
        """Return all "volumeMounts" items per container"""
        volume_mounts_items = [self._create_volume_mounts_item(vol)
                               for vol in self._volume_mounts]
        ssh_vol = {'mountPath': self.SSH_MOUNT_PATH,
                   'name': self.ssh_key}
        volume_mounts_items.append(self._create_volume_mounts_item(ssh_vol))
        return volume_mounts_items

    @staticmethod
    def _create_volume_mounts_item(volume_mount):
        """Create a "volumeMounts" item"""
        return {}




class ServiceObject(object):

    def __init__(self, name):
        self.name = '{}-service'.format(name)
        self.template = {
            'metadata': {
                'name': '{}-service'.format(name)
            },
            'spec': {
                'type': 'NodePort',
                'ports': [
                    {
                        'port': 22,
                        'protocol': 'TCP'
                    }
                ],
                'selector': {
                    'app': name
                }
            }
        }

    def create(self):
        k8s_utils.create_service(self.template)

    def delete(self):
        k8s_utils.delete_service(self.name)


class KubernetesTemplate(object):

    CONTEXT_CFG_PARAMETERS = {'volumes': []}

    def __init__(self, name, context_cfg):
        """KubernetesTemplate object initialization

        :param name: (str) name of the Kubernetes context
        :param context_cfg: (dict) context definition
        """
        context_cfg = copy.deepcopy(context_cfg)
        servers_cfg = context_cfg.pop('servers', {})
        self.name = name
        self.ssh_key = '{}-key'.format(name)

        self.rcs = [self._get_rc_name(rc) for rc in servers_cfg]
        self.k8s_objs = []
        for rc, cfg in servers_cfg.items():
            for param, def_value in self.CONTEXT_CFG_PARAMETERS.items():
                cfg.update({param: context_cfg.get(param, def_value)})
            self.k8s_objs.append(
                KubernetesObject(self._get_rc_name(rc),
                                 ssh_key=self.ssh_key, **cfg))
        self.service_objs = [ServiceObject(s) for s in self.rcs]

        self.pods = []

    def _get_rc_name(self, rc_name):
        return '{}-{}'.format(rc_name, self.name)

    def get_rc_pods(self):
        resp = k8s_utils.get_pod_list()
        self.pods = [p.metadata.name for p in resp.items for s in self.rcs
                     if p.metadata.name.startswith(s)]

        return self.pods
