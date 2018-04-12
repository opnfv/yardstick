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


class DeleteInstanceTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()

    def test_delete_instance(self):
        self.mock_shade_client.delete_server.return_value = True
        output = openstack_utils.delete_instance(self.mock_shade_client,
                                                 'instance_name_id')
        self.assertTrue(output)

    def test_delete_instance_fail(self):
        self.mock_shade_client.delete_server.return_value = False
        output = openstack_utils.delete_instance(self.mock_shade_client,
                                                 'instance_name_id')
        self.assertFalse(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_delete_instance_exception(self, mock_logger):
        self.mock_shade_client.delete_server.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.delete_instance(self.mock_shade_client,
                                                 'instance_name_id')
        mock_logger.error.assert_called_once()
        self.assertFalse(output)


class CreateKeypairTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.name = 'key_name'

    def test_create_keypair(self):
        self.mock_shade_client.create_keypair.return_value = (
            {'name': 'key-name', 'type': 'ssh'})
        output = openstack_utils.create_keypair(
            self.mock_shade_client, self.name)
        self.assertEqual(
            {'name': 'key-name', 'type': 'ssh'},
            output)

    @mock.patch.object(openstack_utils, 'log')
    def test_create_keypair_fail(self, mock_logger):
        self.mock_shade_client.create_keypair.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.create_keypair(
            self.mock_shade_client, self.name)
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)


class DeleteKeypairTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()

    def test_delete_keypair(self):
        self.mock_shade_client.delete_keypair.return_value = True
        output = openstack_utils.delete_keypair(self.mock_shade_client,
                                                'key_name')
        self.assertTrue(output)

    def test_delete_keypair_fail(self):
        self.mock_shade_client.delete_keypair.return_value = False
        output = openstack_utils.delete_keypair(self.mock_shade_client,
                                                'key_name')
        self.assertFalse(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_delete_keypair_exception(self, mock_logger):
        self.mock_shade_client.delete_keypair.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.delete_keypair(self.mock_shade_client,
                                                'key_name')
        mock_logger.error.assert_called_once()
        self.assertFalse(output)


class AttachVolumeToServerTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.server = {'sever_dict'}
        self.volume = {'volume_dict'}

    def test_attach_volume_to_server(self):
        output = openstack_utils.attach_volume_to_server(
            self.mock_shade_client, self.server, self.volume)
        self.assertTrue(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_attach_volume_to_server_fail(self, mock_logger):
        self.mock_shade_client.attach_volume.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.attach_volume_to_server(
            self.mock_shade_client, self.server, self.volume)
        mock_logger.error.assert_called_once()
        self.assertFalse(output)


class GetServerTestCase(unittest.TestCase):

    def test_get_server(self):
        self.mock_shade_client = mock.Mock()
        _uuid = uuidutils.generate_uuid()
        self.mock_shade_client.get_server.return_value = {
            'name': 'server_name', 'id': _uuid}
        output = openstack_utils.get_server(self.mock_shade_client,
                                            'server_name_or_id')
        self.assertEqual({'name': 'server_name', 'id': _uuid}, output)

    @mock.patch.object(openstack_utils, 'log')
    def test_get_server_exception(self, mock_logger):
        self.mock_shade_client = mock.Mock()
        self.mock_shade_client.get_server.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.get_server(self.mock_shade_client,
                                            'server_name_or_id')
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)


class GetFlavorTestCase(unittest.TestCase):

    def test_get_flavor(self):
        self.mock_shade_client = mock.Mock()
        _uuid = uuidutils.generate_uuid()
        self.mock_shade_client.get_flavor.return_value = {
            'name': 'flavor_name', 'id': _uuid}
        output = openstack_utils.get_flavor(self.mock_shade_client,
                                            'flavor_name_or_id')
        self.assertEqual({'name': 'flavor_name', 'id': _uuid}, output)

    @mock.patch.object(openstack_utils, 'log')
    def test_get_flavor_exception(self, mock_logger):
        self.mock_shade_client = mock.Mock()
        self.mock_shade_client.get_flavor.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.get_flavor(self.mock_shade_client,
                                            'flavor_name_or_id')
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)

# *********************************************
#   CINDER
# *********************************************


class GetVolumeIDTestCase(unittest.TestCase):

    def test_get_volume_id(self):
        self.mock_shade_client = mock.Mock()
        _uuid = uuidutils.generate_uuid()
        self.mock_shade_client.get_volume_id.return_value = _uuid
        output = openstack_utils.get_volume_id(self.mock_shade_client,
                                               'volume_name')
        self.assertEqual(_uuid, output)

    def test_get_volume_id_None(self):
        self.mock_shade_client = mock.Mock()
        self.mock_shade_client.get_volume_id.return_value = None
        output = openstack_utils.get_volume_id(self.mock_shade_client,
                                               'volume_name')
        self.assertIsNone(output)


class GetVolumeTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.mock_shade_client.get_volume = mock.Mock()

    def test_get_volume(self):
        self.mock_shade_client.get_volume.return_value = {'volume'}
        output = openstack_utils.get_volume(self.mock_shade_client,
                                            'volume_name_or_id')
        self.assertEqual({'volume'}, output)

    def test_get_volume_None(self):
        self.mock_shade_client.get_volume.return_value = None
        output = openstack_utils.get_volume(self.mock_shade_client,
                                            'volume_name_or_id')
        self.assertIsNone(output)


class CreateVolumeTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.size = 1

    def test_create_volume(self):
        self.mock_shade_client.create_volume.return_value = (
            {'name': 'volume-name', 'size': self.size})
        output = openstack_utils.create_volume(
            self.mock_shade_client, self.size)
        self.assertEqual(
            {'name': 'volume-name', 'size': self.size},
            output)

    @mock.patch.object(openstack_utils, 'log')
    def test_create_volume_fail(self, mock_logger):
        self.mock_shade_client.create_volume.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.create_volume(self.mock_shade_client,
                                               self.size)
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)


class DeleteVolumeTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()

    def test_delete_volume(self):
        self.mock_shade_client.delete_volume.return_value = True
        output = openstack_utils.delete_volume(self.mock_shade_client,
                                               'volume_name_or_id')
        self.assertTrue(output)

    def test_delete_volume_fail(self):
        self.mock_shade_client.delete_volume.return_value = False
        output = openstack_utils.delete_volume(self.mock_shade_client,
                                               'volume_name_or_id')
        self.assertFalse(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_delete_volume_exception(self, mock_logger):
        self.mock_shade_client.delete_volume.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.delete_volume(self.mock_shade_client,
                                               'volume_name_or_id')
        mock_logger.error.assert_called_once()
        self.assertFalse(output)


class DetachVolumeTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self.server = {'server'}
        self.volume = {'volume'}

    def test_detach_volume(self):
        output = openstack_utils.detach_volume(self.mock_shade_client,
                                               self.server, self.volume)
        self.assertTrue(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_detach_volume_exception(self, mock_logger):
        self.mock_shade_client.detach_volume.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.detach_volume(self.mock_shade_client,
                                               self.server, self.volume)
        mock_logger.error.assert_called_once()
        self.assertFalse(output)


# *********************************************
#   GLANCE
# *********************************************

class CreateImageTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_shade_client = mock.Mock()
        self._uuid = uuidutils.generate_uuid()
        self.name = 'image_name'

    @mock.patch.object(openstack_utils, 'log')
    def test_create_image_already_exit(self, mock_logger):
        self.mock_shade_client.get_image_id.return_value = self._uuid
        output = openstack_utils.create_image(self.mock_shade_client, self.name)
        mock_logger.info.assert_called_once()
        self.assertEqual(self._uuid, output)

    def test_create_image(self):
        self.mock_shade_client.get_image_id.return_value = None
        self.mock_shade_client.create_image.return_value = {'id': self._uuid}
        output = openstack_utils.create_image(self.mock_shade_client, self.name)
        self.assertEqual(self._uuid, output)

    @mock.patch.object(openstack_utils, 'log')
    def test_create_image_exception(self, mock_logger):
        self.mock_shade_client.get_image_id.return_value = None
        self.mock_shade_client.create_image.side_effect = (
            exc.OpenStackCloudException('error message'))

        output = openstack_utils.create_image(self.mock_shade_client,
                                              self.name)
        mock_logger.error.assert_called_once()
        self.assertIsNone(output)


class DeleteImageTestCase(unittest.TestCase):

    def test_delete_image(self):
        self.mock_shade_client = mock.Mock()
        self.mock_shade_client.delete_image.return_value = True
        output = openstack_utils.delete_image(self.mock_shade_client,
                                              'image_name_or_id')
        self.assertTrue(output)

    def test_delete_image_fail(self):
        self.mock_shade_client = mock.Mock()
        self.mock_shade_client.delete_image.return_value = False
        output = openstack_utils.delete_image(self.mock_shade_client,
                                              'image_name_or_id')
        self.assertFalse(output)

    @mock.patch.object(openstack_utils, 'log')
    def test_delete_image_exception(self, mock_logger):
        self.mock_shade_client = mock.Mock()
        self.mock_shade_client.delete_image.side_effect = (
            exc.OpenStackCloudException('error message'))
        output = openstack_utils.delete_image(self.mock_shade_client,
                                              'image_name_or_id')
        mock_logger.error.assert_called_once()
        self.assertFalse(output)
