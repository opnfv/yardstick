#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.contexts.model

from __future__ import absolute_import
import unittest
import mock

from yardstick.benchmark.contexts import model


class ObjectTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_context = mock.Mock()

    def test_construct(self):

        test_object = model.Object('foo', self.mock_context)

        self.assertEqual(test_object.name, 'foo')
        self.assertEqual(test_object._context, self.mock_context)
        self.assertIsNone(test_object.stack_name)
        self.assertIsNone(test_object.stack_id)

    def test_dn(self):

        self.mock_context.name = 'bar'
        test_object = model.Object('foo', self.mock_context)

        self.assertEqual('foo.bar', test_object.dn)


class PlacementGroupTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_context = mock.Mock()
        self.mock_context.name = 'bar'

    def tearDown(self):
        model.PlacementGroup.map = {}

    def test_sucessful_construct(self):

        test_pg = model.PlacementGroup('foo', self.mock_context, 'affinity')

        self.assertEqual(test_pg.name, 'foo')
        self.assertEqual(test_pg.members, set())
        self.assertEqual(test_pg.stack_name, 'bar-foo')
        self.assertEqual(test_pg.policy, 'affinity')

        test_map = {'foo': test_pg}
        self.assertEqual(model.PlacementGroup.map, test_map)

    def test_wrong_policy_in_construct(self):

        self.assertRaises(ValueError, model.PlacementGroup, 'foo',
                          self.mock_context, 'baz')

    def test_add_member(self):

        test_pg = model.PlacementGroup('foo', self.mock_context, 'affinity')
        test_pg.add_member('foo')

        self.assertEqual(test_pg.members, set(['foo']))

    def test_get_name_successful(self):

        model.PlacementGroup.map = {'foo': True}
        self.assertTrue(model.PlacementGroup.get('foo'))

    def test_get_name_unsuccessful(self):

        self.assertIsNone(model.PlacementGroup.get('foo'))


class RouterTestCase(unittest.TestCase):

    def test_construct(self):

        mock_context = mock.Mock()
        mock_context.name = 'baz'
        test_router = model.Router('foo', 'bar', mock_context, 'qux')

        self.assertEqual(test_router.stack_name, 'baz-bar-foo')
        self.assertEqual(test_router.stack_if_name, 'baz-bar-foo-if0')
        self.assertEqual(test_router.external_gateway_info, 'qux')


class NetworkTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_context = mock.Mock()
        self.mock_context.name = 'bar'

    def tearDown(self):
        model.Network.list = []

    def test_construct_no_external_network(self):

        attrs = {'cidr': '10.0.0.0/24'}
        test_network = model.Network('foo', self.mock_context, attrs)

        self.assertEqual(test_network.stack_name, 'bar-foo')
        self.assertEqual(test_network.subnet_stack_name, 'bar-foo-subnet')
        self.assertEqual(test_network.subnet_cidr, attrs['cidr'])
        self.assertIsNone(test_network.router)
        self.assertIn(test_network, model.Network.list)

    def test_construct_has_external_network(self):

        attrs = {'external_network': 'ext_net'}
        test_network = model.Network('foo', self.mock_context, attrs)
        exp_router = model.Router('router', 'foo', self.mock_context,
                                  'ext_net')

        self.assertEqual(test_network.router.stack_name, exp_router.stack_name)
        self.assertEqual(test_network.router.stack_if_name,
                         exp_router.stack_if_name)
        self.assertEqual(test_network.router.external_gateway_info,
                         exp_router.external_gateway_info)

    def test_has_route_to(self):

        attrs = {'external_network': 'ext_net'}
        test_network = model.Network('foo', self.mock_context, attrs)

        self.assertTrue(test_network.has_route_to('ext_net'))

    def test_has_no_route_to(self):

        attrs = {}
        test_network = model.Network('foo', self.mock_context, attrs)

        self.assertFalse(test_network.has_route_to('ext_net'))

    @mock.patch('yardstick.benchmark.contexts.model.Network.has_route_to')
    def test_find_by_route_to(self, mock_has_route_to):

        mock_network = mock.Mock()
        model.Network.list = [mock_network]
        mock_has_route_to.return_value = True

        self.assertIs(mock_network, model.Network.find_by_route_to('foo'))

    def test_find_external_network(self):

        mock_network = mock.Mock()
        mock_network.router = mock.Mock()
        mock_network.router.external_gateway_info = 'ext_net'
        model.Network.list = [mock_network]

        self.assertEqual(model.Network.find_external_network(), 'ext_net')

    def test_construct_gateway_ip_is_null(self):

        attrs = {'gateway_ip': 'null'}
        test_network = model.Network('foo', self.mock_context, attrs)
        self.assertEqual(test_network.gateway_ip, 'null')

    def test_construct_gateway_ip_is_none(self):

        attrs = {'gateway_ip': None}
        test_network = model.Network('foo', self.mock_context, attrs)
        self.assertEqual(test_network.gateway_ip, 'null')

    def test_construct_gateway_ip_is_absent(self):

        attrs = {}
        test_network = model.Network('foo', self.mock_context, attrs)
        self.assertIsNone(test_network.gateway_ip)

class ServerTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_context = mock.Mock()
        self.mock_context.name = 'bar'
        self.mock_context.keypair_name = 'some-keys'
        self.mock_context.secgroup_name = 'some-secgroup'
        self.mock_context.user = "some-user"
        netattrs = {'cidr': '10.0.0.0/24', 'provider': None, 'external_network': 'ext_net'}
        self.mock_context.networks = [model.Network("some-network", self.mock_context, netattrs)]


    def test_construct_defaults(self):

        attrs = None
        test_server = model.Server('foo', self.mock_context, attrs)

        self.assertEqual(test_server.stack_name, 'foo.bar')
        self.assertEqual(test_server.keypair_name, 'some-keys')
        self.assertEqual(test_server.secgroup_name, 'some-secgroup')
        self.assertEqual(test_server.placement_groups, [])
        self.assertIsNone(test_server.server_group)
        self.assertEqual(test_server.instances, 1)
        self.assertIsNone(test_server.floating_ip)
        self.assertIsNone(test_server._image)
        self.assertIsNone(test_server._flavor)
        self.assertIn(test_server, model.Server.list)

    @mock.patch('yardstick.benchmark.contexts.model.PlacementGroup')
    def test_construct_get_wrong_placement_group(self, mock_pg):

        attrs = {'placement': 'baz'}
        mock_pg.get.return_value = None

        self.assertRaises(ValueError, model.Server, 'foo',
                          self.mock_context, attrs)

    @mock.patch('yardstick.benchmark.contexts.model.PlacementGroup')
    def test_construct_get_wrong_server_group(self, mock_sg):

        attrs = {'server_group': 'baz'}
        mock_sg.get.return_value = None

        self.assertRaises(ValueError, model.Server, 'foo',
                          self.mock_context, attrs)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test__add_instance(self, mock_template):

        attrs = {'image': 'some-image', 'flavor': 'some-flavor', 'floating_ip': '192.168.1.10', 'floating_ip_assoc': 'some-vm'}
        test_server = model.Server('foo', self.mock_context, attrs)

        self.mock_context.flavors = ['flavor1', 'flavor2', 'some-flavor']

        mock_network = mock.Mock()
        mock_network.name = 'some-network'
        mock_network.stack_name = 'some-network-stack'
        mock_network.allowed_address_pairs = ["1", "2"]
        mock_network.vnic_type = 'normal'
        mock_network.subnet_stack_name = 'some-network-stack-subnet'
        mock_network.provider = 'sriov'
        mock_network.external_network = 'ext_net'
        mock_network.router = model.Router('some-router', 'some-network', self.mock_context, 'ext_net')

        test_server._add_instance(mock_template, 'some-server',
                                  [mock_network], 'hints')

        mock_template.add_port.assert_called_with(
            'some-server-some-network-port',
            mock_network.stack_name,
            mock_network.subnet_stack_name,
            mock_network.vnic_type,
            sec_group_id=self.mock_context.secgroup_name,
            provider=mock_network.provider,
            allowed_address_pairs=mock_network.allowed_address_pairs)

        mock_template.add_floating_ip.assert_called_with(
            'some-server-fip',
            mock_network.external_network,
            'some-server-some-network-port',
            'bar-some-network-some-router-if0',
            'some-secgroup'
        )

        mock_template.add_floating_ip_association.assert_called_with(
            'some-server-fip-assoc',
            'some-server-fip',
            'some-server-some-network-port'
        )

        mock_template.add_server.assert_called_with(
            'some-server', 'some-image',
            flavor='some-flavor',
            flavors=['flavor1', 'flavor2', 'some-flavor'],
            ports=['some-server-some-network-port'],
            user=self.mock_context.user,
            key_name=self.mock_context.keypair_name,
            user_data='',
            scheduler_hints='hints')

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test__add_instance_with_user_data(self, mock_template):
        user_data = "USER_DATA"
        attrs = {
            'image': 'some-image', 'flavor': 'some-flavor',
            'user_data': user_data,
        }
        test_server = model.Server('foo', self.mock_context, attrs)

        test_server._add_instance(mock_template, 'some-server',
                                  [], 'hints')

        mock_template.add_server.assert_called_with(
            'some-server', 'some-image',
            flavor='some-flavor',
            flavors=self.mock_context.flavors,
            ports=[],
            user=self.mock_context.user,
            key_name=self.mock_context.keypair_name,
            user_data=user_data,
            scheduler_hints='hints')

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test__add_instance_plus_flavor(self, mock_template):

        user_data = ''
        attrs = {
            'image': 'some-image', 'flavor': 'flavor1',
            'flavors': ['flavor2'], 'user_data': user_data
        }
        test_server = model.Server('ServerFlavor-2', self.mock_context, attrs)

        self.mock_context.flavors = ['flavor2']
        mock_network = mock.Mock()
        mock_network.allowed_address_pairs = ["1", "2"]
        mock_network.vnic_type = 'normal'
        mock_network.configure_mock(name='some-network', stack_name='some-network-stack',
                                    subnet_stack_name='some-network-stack-subnet',
                                    provider='some-provider')

        test_server._add_instance(mock_template, 'ServerFlavor-2',
                                  [mock_network], 'hints')

        mock_template.add_port.assert_called_with(
            'ServerFlavor-2-some-network-port',
            mock_network.stack_name,
            mock_network.subnet_stack_name,
            mock_network.vnic_type,
            provider=mock_network.provider,
            sec_group_id=self.mock_context.secgroup_name,
            allowed_address_pairs=mock_network.allowed_address_pairs)

        mock_template.add_server.assert_called_with(
            'ServerFlavor-2', 'some-image',
            flavor='flavor1',
            flavors=['flavor2'],
            ports=['ServerFlavor-2-some-network-port'],
            user=self.mock_context.user,
            key_name=self.mock_context.keypair_name,
            user_data=user_data,
            scheduler_hints='hints')

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test__add_instance_misc(self, mock_template):

        user_data = ''
        attrs = {
            'image': 'some-image', 'flavor': 'flavor1',
            'flavors': ['flavor2'], 'user_data': user_data
        }
        test_server = model.Server('ServerFlavor-3', self.mock_context, attrs)

        self.mock_context.flavors =  ['flavor2']
        self.mock_context.flavor = {'vcpus': 4}
        mock_network = mock.Mock()
        mock_network.name = 'some-network'
        mock_network.stack_name = 'some-network-stack'
        mock_network.subnet_stack_name = 'some-network-stack-subnet'

        test_server._add_instance(mock_template, 'ServerFlavor-3',
                                  [mock_network], 'hints')


        mock_template.add_port(
            'ServerFlavor-3-some-network-port',
            mock_network.stack_name,
            mock_network.subnet_stack_name,
            sec_group_id=self.mock_context.secgroup_name)

        mock_template.add_flavor(
            vcpus=4,
            ram=2048,
            disk=1)

        mock_template.add_flavor(
            vcpus=4,
            ram=2048,
            disk=1,
            extra_specs={'cat': 1, 'dog': 2, 'dragon': 1000})

        mock_template.add_server.assert_called_with(
            'ServerFlavor-3', 'some-image',
            flavor='flavor1',
            flavors=['flavor2'],
            ports=['ServerFlavor-3-some-network-port'],
            user=self.mock_context.user,
            key_name=self.mock_context.keypair_name,
            user_data=user_data,
            scheduler_hints='hints')

