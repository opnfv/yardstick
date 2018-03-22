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

from shade import exc
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


class DeleteNeutronNetTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()

    def test_delete_neutron_net(self):
        self.mock_shade_client.delete_network.return_value = True
        output = openstack_utils.delete_neutron_net(self.mock_shade_client,
                                                    'network_name_or_id')
        self.assertTrue(output)

    def test_delete_neutron_net_fail(self):
        self.mock_shade_client.delete_network.return_value = False
        output = openstack_utils.delete_neutron_net(self.mock_shade_client,
                                                    'network_name_or_id')
        self.assertFalse(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_delete_neutron_net_exception(self, mock_logger):
        self.mock_shade_client.delete_network.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.delete_neutron_net(self.mock_shade_client,
                                                    'network_name_or_id')
        self.assertFalse(output)
        mock_logger.error.assert_called_once()


class CreateNeutronNetTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.network_name = 'name'
        self.mock_shade_client.create_network = mock.Mock()

    def test_create_neutron_net(self):
        _uuid = uuidutils.generate_uuid()
        self.mock_shade_client.create_network.return_value = {'id': _uuid}
        output = openstack_utils.create_neutron_net(self.mock_shade_client,
                                                    self.network_name)
        self.assertEqual(_uuid, output)

    @mock.patch.object(openstack_utils, 'log')
    def test_create_neutron_net_exception(self, mock_logger):
        self.mock_shade_client.create_network.side_effect = (
            exc.OpenStackCloudException('error message'))

        output = openstack_utils.create_neutron_net(self.mock_shade_client,
                                                    self.network_name)
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)


class CreateNeutronSubnetTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.network_name_or_id = 'name_or_id'
        self.mock_shade_client.create_subnet = mock.Mock()

    def test_create_neutron_subnet(self):
        _uuid = uuidutils.generate_uuid()
        self.mock_shade_client.create_subnet.return_value = {'id': _uuid}
        output = openstack_utils.create_neutron_subnet(
            self.mock_shade_client, self.network_name_or_id)
        self.assertEqual(_uuid, output)

    @mock.patch.object(openstack_utils, 'log')
    def test_create_neutron_subnet_exception(self, mock_logger):
        self.mock_shade_client.create_subnet.side_effect = (
            exc.OpenStackCloudException('error message'))

        output = openstack_utils.create_neutron_subnet(
            self.mock_shade_client, self.network_name_or_id)
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)


class DeleteNeutronRouterTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.mock_shade_client.delete_router = mock.Mock()

    def test_delete_neutron_router(self):
        self.mock_shade_client.delete_router.return_value = True
        output = openstack_utils.delete_neutron_router(self.mock_shade_client,
                                                       'router_id')
        self.assertTrue(output)

    def test_delete_neutron_router_fail(self):
        self.mock_shade_client.delete_router.return_value = False
        output = openstack_utils.delete_neutron_router(self.mock_shade_client,
                                                       'router_id')
        self.assertFalse(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_delete_neutron_router_exception(self, mock_logger):
        self.mock_shade_client.delete_router.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.delete_neutron_router(self.mock_shade_client,
                                                       'router_id')
        mock_logger.error.assert_called_once()
        self.assertFalse(output)


class CreateNeutronRouterTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.mock_shade_client.create_subnet = mock.Mock()

    def test_create_neutron_router(self):
        _uuid = uuidutils.generate_uuid()
        self.mock_shade_client.create_router.return_value = {'id': _uuid}
        output = openstack_utils.create_neutron_router(
            self.mock_shade_client)
        self.assertEqual(_uuid, output)

    @mock.patch.object(openstack_utils, 'log')
    def test_create_neutron_subnet_exception(self, mock_logger):
        self.mock_shade_client.create_router.side_effect = (
            exc.OpenStackCloudException('error message'))

        output = openstack_utils.create_neutron_router(
            self.mock_shade_client)
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)


class RemoveRouterInterfaceTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.router = 'router'
        self.mock_shade_client.remove_router_interface = mock.Mock()

    def test_remove_router_interface(self):
        self.mock_shade_client.remove_router_interface.return_value = True
        output = openstack_utils.remove_router_interface(
            self.mock_shade_client, self.router)
        self.assertTrue(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_remove_router_interface_exception(self, mock_logger):
        self.mock_shade_client.remove_router_interface.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.remove_router_interface(
            self.mock_shade_client, self.router)
        mock_logger.error.assert_called_once()
        self.assertFalse(output)


class CreateFloatingIpTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.network_name_or_id = 'name'
        self.mock_shade_client.create_floating_ip = mock.Mock()

    def test_create_floating_ip(self):
        self.mock_shade_client.create_floating_ip.return_value = \
            {'floating_ip_address': 'value1', 'id': 'value2'}
        output = openstack_utils.create_floating_ip(self.mock_shade_client,
                                                    self.network_name_or_id)
        self.assertEqual({'fip_addr': 'value1', 'fip_id': 'value2'}, output)

    @mock.patch.object(openstack_utils, 'log')
    def test_create_floating_ip_exception(self, mock_logger):
        self.mock_shade_client.create_floating_ip.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.create_floating_ip(
            self.mock_shade_client, self.network_name_or_id)
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)


class DeleteFloatingIpTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.floating_ip_id = 'floating_ip_id'
        self.mock_shade_client.delete_floating_ip = mock.Mock()

    def test_delete_floating_ip(self):
        self.mock_shade_client.delete_floating_ip.return_value = True
        output = openstack_utils.delete_floating_ip(self.mock_shade_client,
                                                    'floating_ip_id')
        self.assertTrue(output)

    def test_delete_floating_ip_fail(self):
        self.mock_shade_client.delete_floating_ip.return_value = False
        output = openstack_utils.delete_floating_ip(self.mock_shade_client,
                                                    'floating_ip_id')
        self.assertFalse(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_delete_floating_ip_exception(self, mock_logger):
        self.mock_shade_client.delete_floating_ip.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.delete_floating_ip(self.mock_shade_client,
                                                    'floating_ip_id')
        mock_logger.error.assert_called_once()
        self.assertFalse(output)


class CreateSecurityGroupRuleTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.secgroup_name_or_id = 'sg_name_id'
        self.mock_shade_client.create_security_group_rule = mock.Mock()

    def test_create_security_group_rule(self):
        self.mock_shade_client.create_security_group_rule.return_value = (
            {'security_group_rule'})
        output = openstack_utils.create_security_group_rule(
            self.mock_shade_client, self.secgroup_name_or_id)
        self.assertTrue(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_create_security_group_rule_exception(self, mock_logger):
        self.mock_shade_client.create_security_group_rule.side_effect = (
            exc.OpenStackCloudException('error message'))

        output = openstack_utils.create_security_group_rule(
            self.mock_shade_client, self.secgroup_name_or_id)
        mock_logger.error.assert_called_once()
        self.assertFalse(output)


class ListImageTestCase(unittest.TestCase):

    def test_list_images(self):
        mock_shade_client = mock.MagicMock()
        mock_shade_client.list_images.return_value = []
        openstack_utils.list_images(mock_shade_client)

    @mock.patch.object(openstack_utils, 'log')
    def test_list_images_exception(self, mock_logger):
        mock_shade_client = mock.MagicMock()
        mock_shade_client.list_images = mock.MagicMock()
        mock_shade_client.list_images.side_effect = (
            exc.OpenStackCloudException('error message'))
        images = openstack_utils.list_images(mock_shade_client)
        mock_logger.error.assert_called_once()
        self.assertFalse(images)


class SecurityGroupTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.sg_name = 'sg_name'
        self.sg_description = 'sg_description'
        self._uuid = uuidutils.generate_uuid()

    def test_create_security_group_full_existing_security_group(self):
        self.mock_shade_client.get_security_group.return_value = (
            {'name': 'name', 'id': self._uuid})
        output = openstack_utils.create_security_group_full(
            self.mock_shade_client, self.sg_name, self.sg_description)
        self.mock_shade_client.get_security_group.assert_called_once()
        self.assertEqual(self._uuid, output)

    @mock.patch.object(openstack_utils, 'log')
    def test_create_security_group_full_non_existing_security_group(
            self, mock_logger):
        self.mock_shade_client.get_security_group.return_value = None
        self.mock_shade_client.create_security_group.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.create_security_group_full(
            self.mock_shade_client, self.sg_name, self.sg_description)
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)

    @mock.patch.object(openstack_utils, 'create_security_group_rule')
    @mock.patch.object(openstack_utils, 'log')
    def test_create_security_group_full_create_rule_fail(
            self, mock_logger, mock_create_security_group_rule):
        self.mock_shade_client.get_security_group.return_value = None
        self.mock_shade_client.create_security_group.return_value = (
            {'name': 'name', 'id': self._uuid})
        mock_create_security_group_rule.return_value = False
        output = openstack_utils.create_security_group_full(
            self.mock_shade_client, self.sg_name, self.sg_description)
        mock_create_security_group_rule.assert_called()
        self.mock_shade_client.delete_security_group(self.sg_name)
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)

    @mock.patch.object(openstack_utils, 'create_security_group_rule')
    def test_create_security_group_full(
            self, mock_create_security_group_rule):
        self.mock_shade_client.get_security_group.return_value = None
        self.mock_shade_client.create_security_group.return_value = (
            {'name': 'name', 'id': self._uuid})
        mock_create_security_group_rule.return_value = True
        output = openstack_utils.create_security_group_full(
            self.mock_shade_client, self.sg_name, self.sg_description)
        mock_create_security_group_rule.assert_called()
        self.mock_shade_client.delete_security_group(self.sg_name)
        self.assertEqual(self._uuid, output)

# *********************************************
#   NOVA
# *********************************************


class CreateInstanceTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.name = 'name'
        self.image = 'image_name'
        self.flavor = 'flavor_name'

    def test_create_instance_and_wait_for_active(self):
        self.mock_shade_client.create_server.return_value = (
            {'name': 'server-name', 'image': 'image_name',
             'flavor': 'flavor-name'})
        output = openstack_utils.create_instance_and_wait_for_active(
            self.mock_shade_client, self.name, self.image, self.flavor)
        self.assertEqual(
            {'name': 'server-name', 'image': 'image_name',
             'flavor': 'flavor-name'},
            output)

    @mock.patch.object(openstack_utils, 'log')
    def test_create_instance_and_wait_for_active_fail(self, mock_logger):
        self.mock_shade_client.create_server.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.create_instance_and_wait_for_active(
            self.mock_shade_client, self.name, self.image, self.flavor)
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)
