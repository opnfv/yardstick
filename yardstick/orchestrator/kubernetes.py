##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
from __future__ import print_function

from yardstick.common import utils
from yardstick.common import kubernetes_utils as k8s_utils


class KubernetesObject(object):

    def __init__(self, name, **kwargs):
        super(KubernetesObject, self).__init__()
        self.name = name
        self.image = kwargs.get('image', 'openretriever/yardstick')
        self.command = [kwargs.get('command', '/bin/bash')]
        self.args = kwargs.get('args', [])
        self.ssh_key = kwargs.get('ssh_key', 'yardstick_key')

        self.volumes = []

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
                            "app": ""
                        }
                    },
                    "spec": {
                        "containers": [],
                        "volumes": []
                    }
                }
            }
        }

        self._change_value_according_name(name)
        self._add_containers()
        self._add_ssh_key_volume()
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
        ssh_key_mount_path = "/root/.ssh/"

        container = {
            "args": self.args,
            "command": self.command,
            "image": self.image,
            "name": container_name,
            "volumeMounts": [
                {
                    "mountPath": ssh_key_mount_path,
                    "name": self.ssh_key
                }
            ]
        }

        return container

    def _add_volumes(self):
        utils.set_dict_value(self.template,
                             'spec.template.spec.volumes',
                             self.volumes)

    def _add_volume(self, volume):
        self.volumes.append(volume)

    def _add_ssh_key_volume(self):
        key_volume = {
            "configMap": {
                "name": self.ssh_key
            },
            "name": self.ssh_key
        }
        self._add_volume(key_volume)


class KubernetesTemplate(object):

    def __init__(self, name, template_cfg):
        self.name = name
        self.ssh_key = '{}-key'.format(name)

        self.rcs = [self._get_rc_name(rc) for rc in template_cfg]
        self.k8s_objs = [KubernetesObject(self._get_rc_name(rc),
                                          ssh_key=self.ssh_key,
                                          **cfg)
                         for rc, cfg in template_cfg.items()]
        self.pods = []

    def _get_rc_name(self, rc_name):
        return '{}-{}'.format(rc_name, self.name)

    def get_rc_pods(self):
        resp = k8s_utils.get_pod_list()
        self.pods = [p.metadata.name for p in resp.items for s in self.rcs
                     if p.metadata.name.startswith(s)]

        return self.pods
