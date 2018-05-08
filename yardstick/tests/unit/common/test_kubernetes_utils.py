# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
from kubernetes import client
from kubernetes.client import rest
from kubernetes import config

from yardstick.common import constants
from yardstick.common import exceptions
from yardstick.common import kubernetes_utils
from yardstick.tests.unit import base


class GetExtensionsV1betaApiTestCase(base.BaseUnitTestCase):

    @mock.patch.object(client, 'ApiextensionsV1beta1Api', return_value='api')
    @mock.patch.object(config, 'load_kube_config')
    def test_execute_correct(self, mock_load_kube_config, mock_api):
        self.assertEqual('api', kubernetes_utils.get_extensions_v1beta_api())
        mock_load_kube_config.assert_called_once_with(
            config_file=constants.K8S_CONF_FILE)
        mock_api.assert_called_once()

    @mock.patch.object(config, 'load_kube_config')
    def test_execute_exception(self, mock_load_kube_config):
        mock_load_kube_config.side_effect = IOError
        with self.assertRaises(exceptions.KubernetesConfigFileNotFound):
            kubernetes_utils.get_extensions_v1beta_api()


class CreateCustomResourceDefinitionTestCase(base.BaseUnitTestCase):

    @mock.patch.object(client, 'V1beta1CustomResourceDefinition',
                       return_value='crd_obj')
    @mock.patch.object(kubernetes_utils, 'get_extensions_v1beta_api')
    def test_execute_correct(self, mock_get_api, mock_crd):
        mock_create_crd = mock.Mock()
        mock_get_api.return_value = mock_create_crd
        body = {'spec': 'fake_spec', 'metadata': 'fake_metadata'}

        kubernetes_utils.create_custom_resource_definition(body)
        mock_get_api.assert_called_once()
        mock_crd.assert_called_once_with(spec='fake_spec',
                                         metadata='fake_metadata')
        mock_create_crd.create_custom_resource_definition.\
            assert_called_once_with('crd_obj')

    @mock.patch.object(client, 'V1beta1CustomResourceDefinition',
                       return_value='crd_obj')
    @mock.patch.object(kubernetes_utils, 'get_extensions_v1beta_api')
    def test_execute_exception(self, mock_get_api, mock_crd):
        mock_create_crd = mock.Mock()
        mock_create_crd.create_custom_resource_definition.\
            side_effect = rest.ApiException
        mock_get_api.return_value = mock_create_crd
        body = {'spec': 'fake_spec', 'metadata': 'fake_metadata'}

        with self.assertRaises(exceptions.KubernetesApiException):
            kubernetes_utils.create_custom_resource_definition(body)
        mock_get_api.assert_called_once()
        mock_crd.assert_called_once_with(spec='fake_spec',
                                         metadata='fake_metadata')
        mock_create_crd.create_custom_resource_definition.\
            assert_called_once_with('crd_obj')


class DeleteCustomResourceDefinitionTestCase(base.BaseUnitTestCase):

    @mock.patch.object(client, 'V1DeleteOptions', return_value='del_obj')
    @mock.patch.object(kubernetes_utils, 'get_extensions_v1beta_api')
    def test_execute_correct(self, mock_get_api, mock_delobj):
        mock_delete_crd = mock.Mock()
        mock_get_api.return_value = mock_delete_crd

        kubernetes_utils.delete_custom_resource_definition('name')
        mock_get_api.assert_called_once()
        mock_delobj.assert_called_once()
        mock_delete_crd.delete_custom_resource_definition.\
            assert_called_once_with('name', 'del_obj')

    @mock.patch.object(client, 'V1DeleteOptions', return_value='del_obj')
    @mock.patch.object(kubernetes_utils, 'get_extensions_v1beta_api')
    def test_execute_exception(self, mock_get_api, mock_delobj):
        mock_delete_crd = mock.Mock()
        mock_delete_crd.delete_custom_resource_definition.\
            side_effect = rest.ApiException
        mock_get_api.return_value = mock_delete_crd

        with self.assertRaises(exceptions.KubernetesApiException):
            kubernetes_utils.delete_custom_resource_definition('name')
        mock_delobj.assert_called_once()
        mock_delete_crd.delete_custom_resource_definition.\
            assert_called_once_with('name', 'del_obj')
