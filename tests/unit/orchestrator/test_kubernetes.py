#!/usr/bin/env python

##############################################################################
# Copyright (c) 2017 Intel Corporation
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.orchestrator.heat
import unittest

from yardstick.orchestrator.kubernetes import KubernetesObject


class GetTemplateTestCase(unittest.TestCase):

    def test_get_template(self):
        output_t = {
            "apiVersion": "v1",
            "kind": "ReplicationController",
            "metadata": {
                "name": "host-k8s-86096c30"
            },
            "spec": {
                "replicas": 1,
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "host-k8s-86096c30"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "args": [
                                    "-c",
                                    "chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; \
service ssh restart;while true ; do sleep 10000; done"
                                ],
                                "command": [
                                    "/bin/bash"
                                ],
                                "image": "openretriever/yardstick",
                                "name": "host-k8s-86096c30-container",
                                "volumeMounts": [
                                    {
                                        "mountPath": "/root/.ssh/",
                                        "name": "k8s-86096c30-key"
                                    }
                                ]
                            }
                        ],
                        "volumes": [
                            {
                                "configMap": {
                                    "name": "k8s-86096c30-key"
                                },
                                "name": "k8s-86096c30-key"
                            }
                        ]
                    }
                }
            }
        }
        input_s = {
            'command': '/bin/bash',
            'args': ['-c', 'chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; \
service ssh restart;while true ; do sleep 10000; done'],
            'ssh_key': 'k8s-86096c30-key'
        }
        name = 'host-k8s-86096c30'
        output_r = KubernetesObject(name, **input_s).get_template()
        self.assertEqual(output_r, output_t)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
