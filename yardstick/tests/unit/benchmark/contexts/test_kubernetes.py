##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import collections
import time

import mock
import unittest

from yardstick.benchmark import contexts
from yardstick.benchmark.contexts import base
from yardstick.benchmark.contexts import kubernetes
from yardstick.common import constants
from yardstick.orchestrator import kubernetes as orchestrator_kubernetes


CONTEXT_CFG = {
    'type': contexts.CONTEXT_KUBERNETES,
    'name': 'k8s',
    'task_id': '1234567890',
    'servers': {
        'host': {
            'image': 'openretriever/yardstick',
            'command': '/bin/bash',
            'args': ['-c', 'chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; '
                     'service ssh restart;while true ; do sleep 10000; done']
        },
        'target': {
            'image': 'openretriever/yardstick',
            'command': '/bin/bash',
            'args': ['-c', 'chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; '
                     'service ssh restart;while true ; do sleep 10000; done']
        }
    },
    'networks': {
        'flannel': {
            'args': 'flannel_args',
            'plugin': 'flannel'
        },
        'sriov01': {
            'args': 'sriov_args',
            'plugin': 'sriov'
        },
    }
}

prefix = 'yardstick.benchmark.contexts.kubernetes'


class KubernetesTestCase(unittest.TestCase):

    def setUp(self):
        self.k8s_context = kubernetes.KubernetesContext()
        self.addCleanup(self._remove_contexts)
        self.k8s_context.init(CONTEXT_CFG)

    @staticmethod
    def _remove_contexts():
        for context in base.Context.list:
            context._delete_context()
        base.Context.list = []

    @mock.patch.object(kubernetes.KubernetesContext, '_delete_services')
    @mock.patch.object(kubernetes.KubernetesContext, '_delete_ssh_key')
    @mock.patch.object(kubernetes.KubernetesContext, '_delete_rcs')
    @mock.patch.object(kubernetes.KubernetesContext, '_delete_pods')
    @mock.patch.object(kubernetes.KubernetesContext, '_delete_networks')
    @mock.patch.object(kubernetes.KubernetesContext, '_delete_crd')
    def test_undeploy(self, mock_delete_pods, mock_delete_rcs,
                      mock_delete_ssh, mock_delete_services,
                      mock_delete_networks, mock_delete_crd):

        self.k8s_context.undeploy()
        mock_delete_ssh.assert_called_once()
        mock_delete_rcs.assert_called_once()
        mock_delete_pods.assert_called_once()
        mock_delete_services.assert_called_once()
        mock_delete_networks.assert_called_once()
        mock_delete_crd.assert_called_once()

    @mock.patch.object(kubernetes.KubernetesContext, '_create_services')
    @mock.patch.object(kubernetes.KubernetesContext, '_wait_until_running')
    @mock.patch.object(orchestrator_kubernetes.KubernetesTemplate,
                       'get_rc_pods')
    @mock.patch.object(kubernetes.KubernetesContext, '_create_rcs')
    @mock.patch.object(kubernetes.KubernetesContext, '_set_ssh_key')
    @mock.patch.object(kubernetes.KubernetesContext, '_create_networks')
    @mock.patch.object(kubernetes.KubernetesContext, '_create_crd')
    def test_deploy(self, mock_set_ssh_key, mock_create_rcs, mock_get_rc_pods,
                    mock_wait_until_running, mock_create_services,
                    mock_create_networks, mock_create_crd):

        with mock.patch.object(time, 'sleep'):
            self.k8s_context.deploy()
        mock_set_ssh_key.assert_called_once()
        mock_create_rcs.assert_called_once()
        mock_create_services.assert_called_once()
        mock_get_rc_pods.assert_called_once()
        mock_wait_until_running.assert_called_once()
        mock_create_networks.assert_called_once()
        mock_create_crd.assert_called_once()

    @mock.patch.object(kubernetes, 'paramiko', **{"resource_filename.return_value": ""})
    @mock.patch.object(kubernetes, 'pkg_resources', **{"resource_filename.return_value": ""})
    @mock.patch.object(kubernetes, 'utils')
    @mock.patch.object(kubernetes, 'open', create=True)
    @mock.patch.object(kubernetes.k8s_utils, 'delete_config_map')
    @mock.patch.object(kubernetes.k8s_utils, 'create_config_map')
    def test_ssh_key(self, mock_create, mock_delete, *args):
        self.k8s_context._set_ssh_key()
        self.k8s_context._delete_ssh_key()

        mock_create.assert_called_once()
        mock_delete.assert_called_once()

    @mock.patch.object(kubernetes.k8s_utils, 'read_pod_status')
    def test_wait_until_running(self, mock_read_pod_status):

        self.k8s_context.template.pods = ['server']
        mock_read_pod_status.return_value = 'Running'
        self.k8s_context._wait_until_running()

    @mock.patch.object(kubernetes.k8s_utils, 'get_pod_by_name')
    @mock.patch.object(kubernetes.KubernetesContext, '_get_node_ip')
    @mock.patch.object(kubernetes.k8s_utils, 'get_service_by_name')
    def test_get_server(self,
                        mock_get_service_by_name,
                        mock_get_node_ip,
                        mock_get_pod_by_name):
        class Service(object):
            def __init__(self):
                self.node_port = 30000
                self.port = constants.SSH_PORT

        class Services(object):
            def __init__(self):
                self.ports = [Service()]

        class Status(object):
            def __init__(self):
                self.pod_ip = '172.16.10.131'

        class Pod(object):
            def __init__(self):
                self.status = Status()

        mock_get_service_by_name.return_value = Services()
        mock_get_pod_by_name.return_value = Pod()
        mock_get_node_ip.return_value = '172.16.10.131'
        server = self.k8s_context._get_server('server_name')
        self.assertEqual('server_name', server['name'])
        self.assertEqual(30000, server['ssh_port'])

    @mock.patch.object(kubernetes.KubernetesContext, '_create_rc')
    def test_create_rcs(self, mock_create_rc):
        self.k8s_context._create_rcs()
        mock_create_rc.assert_called()

    @mock.patch.object(kubernetes.k8s_utils, 'create_replication_controller')
    def test_create_rc(self, mock_create_replication_controller):
        self.k8s_context._create_rc({})
        mock_create_replication_controller.assert_called_once()

    @mock.patch.object(kubernetes.KubernetesContext, '_delete_rc')
    def test_delete_rcs(self, mock_delete_rc):
        self.k8s_context._delete_rcs()
        mock_delete_rc.assert_called()

    @mock.patch.object(kubernetes.k8s_utils, 'delete_replication_controller')
    def test_delete_rc(self, mock_delete_replication_controller):
        self.k8s_context._delete_rc({})
        mock_delete_replication_controller.assert_called_once()

    @mock.patch.object(kubernetes.k8s_utils, 'get_node_list')
    def test_get_node_ip(self, mock_get_node_list):
        self.k8s_context._get_node_ip()
        mock_get_node_list.assert_called_once()

    @mock.patch.object(orchestrator_kubernetes.ServiceNodePortObject, 'create')
    def test_create_services(self, mock_create):
        self.k8s_context._create_services()
        mock_create.assert_called()

    @mock.patch.object(orchestrator_kubernetes.ServiceNodePortObject, 'delete')
    def test_delete_services(self, mock_delete):
        self.k8s_context._delete_services()
        mock_delete.assert_called()

    def test_init(self):
        self.k8s_context._delete_context()
        with mock.patch.object(orchestrator_kubernetes, 'KubernetesTemplate',
                return_value='fake_template') as mock_k8stemplate:
            self.k8s_context = kubernetes.KubernetesContext()
            self.k8s_context.init(CONTEXT_CFG)
        mock_k8stemplate.assert_called_once_with(self.k8s_context.name,
                                                 CONTEXT_CFG)
        self.assertEqual('fake_template', self.k8s_context.template)
        self.assertEqual(2, len(self.k8s_context._networks))
        self.assertIn('flannel', self.k8s_context._networks.keys())
        self.assertIn('sriov01', self.k8s_context._networks.keys())

    def test__get_physical_nodes(self):
        result = self.k8s_context._get_physical_nodes()
        self.assertIsNone(result)

    def test__get_physical_node_for_server(self):
        result = self.k8s_context._get_physical_node_for_server("fake")
        self.assertIsNone(result)

    def test__get_network(self):
        networks = collections.OrderedDict([('n1', 'data1'), ('n2', 'data2')])
        self.k8s_context._networks = networks
        self.assertEqual({'name': 'n1'}, self.k8s_context._get_network('n1'))
        self.assertEqual({'name': 'n2'}, self.k8s_context._get_network('n2'))
        self.assertIsNone(self.k8s_context._get_network('n3'))

    @mock.patch.object(orchestrator_kubernetes.KubernetesTemplate,
                       'get_rc_by_name')
    def test__get_interfaces(self, mock_get_rc):
        rc = orchestrator_kubernetes.ReplicationControllerObject('rc_name')
        rc._networks = ['net1', 'net2']
        mock_get_rc.return_value = rc
        expected = {'net1': {'network_name': 'net1',
                             'local_mac': None,
                             'local_ip': None},
                    'net2': {'network_name': 'net2',
                             'local_mac': None,
                             'local_ip': None}}
        self.assertEqual(expected, self.k8s_context._get_interfaces('rc_name'))

    @mock.patch.object(orchestrator_kubernetes.KubernetesTemplate,
                       'get_rc_by_name')
    def test__get_interfaces_no_networks(self, mock_get_rc):
        rc = orchestrator_kubernetes.ReplicationControllerObject('rc_name')
        mock_get_rc.return_value = rc
        self.assertEqual({}, self.k8s_context._get_interfaces('rc_name'))

    @mock.patch.object(orchestrator_kubernetes.KubernetesTemplate,
                       'get_rc_by_name', return_value=None)
    def test__get_interfaces_no_rc(self, *args):
        self.assertEqual({}, self.k8s_context._get_interfaces('rc_name'))
