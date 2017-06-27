from __future__ import absolute_import
from __future__ import print_function

from yardstick.common import utils


class KubernetesObject(object):

    def __init__(self, name, **kwargs):
        self.name = name
        self.ssh_key = kwargs.get('ssh_key', 'yardstick_key')
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
        container = {
            "args": [
                "-c",
                "chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; service ssh restart; \
while true ; do sleep 10000; done"
            ],
            "command": [
                "/bin/sh"
            ],
            "image": "openretriever/yardstick",
            "name": '{}-container'.format(self.name),
            "volumeMounts": [
                {
                    "mountPath": "/root/.ssh/",
                    "name": self.ssh_key
                }
            ]
        }
        return container

    def _add_volumes(self):
        volumes = [self._add_volume()]
        utils.set_dict_value(self.template,
                             'spec.template.spec.volumes',
                             volumes)

    def _add_volume(self):
        volume = {
            "configMap": {
                "name": self.ssh_key
            },
            "name": self.ssh_key
        }
        return volume
