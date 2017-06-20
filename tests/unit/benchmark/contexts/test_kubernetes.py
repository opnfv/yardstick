#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.contexts.kubernetes

from __future__ import absolute_import
import unittest
import mock

from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.contexts.kubernetes import KubernetesContext


context_cfg = {
    'type': 'Kubernetes',
    'name': 'k8s',
    'servers': {
        'host': {
            'image': 'openretriever/yardstick',
            'command': '/bin/bash',
            'args': ['-c', 'chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; \
service ssh restart;while true ; do sleep 10000; done']
        },
        'target': {
            'image': 'openretriever/yardstick',
            'command': '/bin/bash',
            'args': ['-c', 'chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; \
service ssh restart;while true ; do sleep 10000; done']
        }
    }
}

prefix = 'yardstick.benchmark.contexts.kubernetes'


class KubernetesTestCase(unittest.TestCase):

    def tearDown(self):
        # clear kubernetes contexts from global list so we don't break other tests
        Context.list = []

    @mock.patch('{}.KubernetesContext._delete_ssh_key'.format(prefix))
    @mock.patch('{}.KubernetesContext._delete_rcs'.format(prefix))
    @mock.patch('{}.KubernetesContext._delete_pods'.format(prefix))
    def test_undeploy(self,
                      mock_delete_pods,
                      mock_delete_rcs,
                      mock_delete_ssh):

        k8s_context = KubernetesContext()
        k8s_context.init(context_cfg)
        k8s_context.undeploy()
        self.assertTrue(mock_delete_ssh.called)
        self.assertTrue(mock_delete_rcs.called)
        self.assertTrue(mock_delete_pods.called)

    @mock.patch('{}.KubernetesContext._wait_until_running'.format(prefix))
    @mock.patch('{}.KubernetesTemplate.get_rc_pods'.format(prefix))
    @mock.patch('{}.KubernetesContext._create_rcs'.format(prefix))
    @mock.patch('{}.KubernetesContext._set_ssh_key'.format(prefix))
    def test_deploy(self,
                    mock_set_ssh_key,
                    mock_create_rcs,
                    mock_get_rc_pods,
                    mock_wait_until_running):

        k8s_context = KubernetesContext()
        k8s_context.init(context_cfg)
        with mock.patch("yardstick.benchmark.contexts.kubernetes.time"):
            k8s_context.deploy()
        self.assertTrue(mock_set_ssh_key.called)
        self.assertTrue(mock_create_rcs.called)
        self.assertTrue(mock_get_rc_pods.called)
        self.assertTrue(mock_wait_until_running.called)

    @mock.patch('{}.k8s_utils.delete_config_map'.format(prefix))
    @mock.patch('{}.k8s_utils.create_config_map'.format(prefix))
    def test_ssh_key(self, mock_create, mock_delete):

        k8s_context = KubernetesContext()
        k8s_context.init(context_cfg)
        k8s_context._set_ssh_key()
        k8s_context._delete_ssh_key()
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_delete.called)

    @mock.patch('{}.k8s_utils.read_pod_status'.format(prefix))
    def test_wait_until_running(self, mock_read_pod_status):

        k8s_context = KubernetesContext()
        k8s_context.init(context_cfg)
        k8s_context.template.pods = ['server']
        mock_read_pod_status.return_value = 'Running'
        k8s_context._wait_until_running()

    @mock.patch('{}.k8s_utils.get_pod_list'.format(prefix))
    def test_get_server(self, mock_get_pod_list):
        k8s_context = KubernetesContext()
        k8s_context.init(context_cfg)

        mock_get_pod_list.return_value.items = []
        server = k8s_context._get_server('server')
        self.assertIsNone(server)

    @mock.patch('{}.KubernetesContext._create_rc'.format(prefix))
    def test_create_rcs(self, mock_create_rc):
        k8s_context = KubernetesContext()
        k8s_context.init(context_cfg)
        k8s_context._create_rcs()
        self.assertTrue(mock_create_rc.called)

    @mock.patch('{}.k8s_utils.create_replication_controller'.format(prefix))
    def test_create_rc(self, mock_create_replication_controller):
        k8s_context = KubernetesContext()
        k8s_context.init(context_cfg)
        k8s_context._create_rc({})
        self.assertTrue(mock_create_replication_controller.called)

    @mock.patch('{}.KubernetesContext._delete_rc'.format(prefix))
    def test_delete_rcs(self, mock_delete_rc):
        k8s_context = KubernetesContext()
        k8s_context.init(context_cfg)
        k8s_context._delete_rcs()
        self.assertTrue(mock_delete_rc.called)

    @mock.patch('{}.k8s_utils.delete_replication_controller'.format(prefix))
    def test_delete_rc(self, mock_delete_replication_controller):
        k8s_context = KubernetesContext()
        k8s_context.init(context_cfg)
        k8s_context._delete_rc({})
        self.assertTrue(mock_delete_replication_controller.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
