##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from oslo_utils import uuidutils
import unittest
import mock

from yardstick.common import openstack_utils


class GetCredentialsTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.os')
    def test_get_credentials(self, _):
        with mock.patch.dict('os.environ', {'OS_IDENTITY_API_VERSION': '2'},
                             clear=True):
            openstack_utils.get_credentials()


class GetHeatApiVersionTestCase(unittest.TestCase):

    def test_get_heat_api_version_check_result(self):
        API = 'HEAT_API_VERSION'
        expected_result = '2'

        with mock.patch.dict('os.environ', {API: '2'}, clear=True):
            api_version = openstack_utils.get_heat_api_version()
            self.assertEqual(api_version, expected_result)


class GetNetworkIdTestCase(unittest.TestCase):

    def test_get_network_id(self):
        _uuid = uuidutils.generate_uuid()
        mock_shade_client = mock.Mock()
        mock_shade_client.list_networks = mock.Mock()
        mock_shade_client.list_networks.return_value = [{'id': _uuid}]

        output = openstack_utils.get_network_id(mock_shade_client,
                                                'network_name')
        self.assertEqual(_uuid, output)

    def test_get_network_id_no_network(self):
        mock_shade_client = mock.Mock()
        mock_shade_client.list_networks = mock.Mock()
        mock_shade_client.list_networks.return_value = None

        output = openstack_utils.get_network_id(mock_shade_client,
                                                'network_name')
        self.assertEqual(None, output)
