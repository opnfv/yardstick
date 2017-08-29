#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.contexts.heat

from __future__ import absolute_import

import ipaddress
import logging
import os
import unittest
import uuid
from collections import OrderedDict

import mock

from itertools import count
from yardstick.benchmark.contexts import heat
from yardstick.benchmark.contexts import model

LOG = logging.getLogger(__name__)


class HeatContextTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(HeatContextTestCase, self).__init__(*args, **kwargs)
        self.name_iter = ('vnf{:03}'.format(x) for x in count(0, step=3))

    def setUp(self):
        self.test_context = heat.HeatContext()
        self.mock_context = mock.Mock(spec=heat.HeatContext())

    def test___init__(self):
        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.stack)
        self.assertEqual(self.test_context.networks, OrderedDict())
        self.assertEqual(self.test_context.servers, [])
        self.assertEqual(self.test_context.placement_groups, [])
        self.assertEqual(self.test_context.server_groups, [])
        self.assertIsNone(self.test_context.keypair_name)
        self.assertIsNone(self.test_context.secgroup_name)
        self.assertEqual(self.test_context._server_map, {})
        self.assertIsNone(self.test_context._image)
        self.assertIsNone(self.test_context._flavor)
        self.assertIsNone(self.test_context._user)
        self.assertIsNone(self.test_context.template_file)
        self.assertIsNone(self.test_context.heat_parameters)
        self.assertIsNotNone(self.test_context.key_uuid)
        self.assertIsNotNone(self.test_context.key_filename)

    @mock.patch('yardstick.benchmark.contexts.heat.PlacementGroup')
    @mock.patch('yardstick.benchmark.contexts.heat.ServerGroup')
    @mock.patch('yardstick.benchmark.contexts.heat.Network')
    @mock.patch('yardstick.benchmark.contexts.heat.Server')
    def test_init(self, mock_server, mock_network, mock_sg, mock_pg):

        pgs = {'pgrp1': {'policy': 'availability'}}
        sgs = {'servergroup1': {'policy': 'affinity'}}
        networks = {'bar': {'cidr': '10.0.1.0/24'}}
        servers = {'baz': {'floating_ip': True, 'placement': 'pgrp1'}}
        attrs = {'name': 'foo',
                 'placement_groups': pgs,
                 'server_groups': sgs,
                 'networks': networks,
                 'servers': servers}

        self.test_context.init(attrs)

        self.assertEqual(self.test_context.name, "foo")
        self.assertEqual(self.test_context.keypair_name, "foo-key")
        self.assertEqual(self.test_context.secgroup_name, "foo-secgroup")

        mock_pg.assert_called_with('pgrp1', self.test_context,
                                   pgs['pgrp1']['policy'])
        mock_sg.assert_called_with('servergroup1', self.test_context,
                                   sgs['servergroup1']['policy'])
        self.assertTrue(len(self.test_context.placement_groups) == 1)
        self.assertTrue(len(self.test_context.server_groups) == 1)

        mock_network.assert_called_with(
            'bar', self.test_context, networks['bar'])
        self.assertTrue(len(self.test_context.networks) == 1)

        mock_server.assert_called_with('baz', self.test_context,
                                       servers['baz'])
        self.assertTrue(len(self.test_context.servers) == 1)

        if os.path.exists(self.test_context.key_filename):
            try:
                os.remove(self.test_context.key_filename)
                os.remove(self.test_context.key_filename + ".pub")
            except OSError:
                LOG.exception("key_filename: %s",
                              self.test_context.key_filename)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test__add_resources_to_template_no_servers(self, mock_template):

        self.test_context.keypair_name = "foo-key"
        self.test_context.secgroup_name = "foo-secgroup"
        self.test_context.key_uuid = "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b"
        netattrs = {'cidr': '10.0.0.0/24', 'provider': None, 'external_network': 'ext_net'}
        self.mock_context.name = 'bar'
        self.test_context.networks = OrderedDict(
            {"fool-network": model.Network("fool-network", self.mock_context,
                                           netattrs)})

        self.test_context._add_resources_to_template(mock_template)
        mock_template.add_keypair.assert_called_with(
            "foo-key",
            "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b")
        mock_template.add_security_group.assert_called_with("foo-secgroup")
#        mock_template.add_network.assert_called_with("bar-fool-network", 'physnet1', None)
        mock_template.add_router.assert_called_with("bar-fool-network-router", netattrs["external_network"], "bar-fool-network-subnet")
        mock_template.add_router_interface.assert_called_with("bar-fool-network-router-if0", "bar-fool-network-router", "bar-fool-network-subnet")

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_attrs_get(self, mock_template):
        image, flavor, user = expected_tuple = 'foo1', 'foo2', 'foo3'
        self.assertNotEqual(self.test_context.image, image)
        self.assertNotEqual(self.test_context.flavor, flavor)
        self.assertNotEqual(self.test_context.user, user)
        self.test_context._image = image
        self.test_context._flavor = flavor
        self.test_context._user = user
        attr_tuple = self.test_context.image, self.test_context.flavor, self.test_context.user
        self.assertEqual(attr_tuple, expected_tuple)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_attrs_set_negative(self, mock_template):
        with self.assertRaises(AttributeError):
            self.test_context.image = 'foo'

        with self.assertRaises(AttributeError):
            self.test_context.flavor = 'foo'

        with self.assertRaises(AttributeError):
            self.test_context.user = 'foo'

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    @mock.patch('yardstick.benchmark.contexts.heat.get_neutron_client')
    def test_attrs_get(self, mock_neutron, mock_template):
        image, flavor, user = expected_tuple = 'foo1', 'foo2', 'foo3'
        self.assertNotEqual(self.test_context.image, image)
        self.assertNotEqual(self.test_context.flavor, flavor)
        self.assertNotEqual(self.test_context.user, user)
        self.test_context._image = image
        self.test_context._flavor = flavor
        self.test_context._user = user
        attr_tuple = self.test_context.image, self.test_context.flavor, self.test_context.user
        self.assertEqual(attr_tuple, expected_tuple)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_attrs_set_negative(self, mock_template):
        with self.assertRaises(AttributeError):
            self.test_context.image = 'foo'

        with self.assertRaises(AttributeError):
            self.test_context.flavor = 'foo'

        with self.assertRaises(AttributeError):
            self.test_context.user = 'foo'

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_deploy(self, mock_template):
        self.test_context.name = 'foo'
        self.test_context.template_file = '/bar/baz/some-heat-file'
        self.test_context.heat_parameters = {'image': 'cirros'}
        self.test_context.get_neutron_info = mock.MagicMock()
        self.test_context.deploy()

        mock_template.assert_called_with('foo',
                                         '/bar/baz/some-heat-file',
                                         {'image': 'cirros'})
        self.assertIsNotNone(self.test_context.stack)

    def test_add_server_port(self):
        network1 = mock.MagicMock()
        network2 = mock.MagicMock()
        self.test_context.name = 'foo'
        self.test_context.stack = mock.MagicMock()
        self.test_context.networks = {
            'a': network1,
            'c': network2,
        }
        self.test_context.stack.outputs = {
            u'b': u'10.20.30.45',
            u'b-subnet_id': 1,
            u'foo-a-subnet-cidr': u'10.20.0.0/15',
            u'foo-a-subnet-gateway_ip': u'10.20.30.1',
            u'b-mac_address': u'00:01',
            u'b-device_id': u'dev21',
            u'b-network_id': u'net789',
            u'd': u'40.30.20.15',
            u'd-subnet_id': 2,
            u'foo-c-subnet-cidr': u'40.30.0.0/18',
            u'foo-c-subnet-gateway_ip': u'40.30.20.254',
            u'd-mac_address': u'00:10',
            u'd-device_id': u'dev43',
            u'd-network_id': u'net987',
        }
        server = mock.MagicMock()
        server.ports = OrderedDict([
            ('a', {'stack_name': 'b'}),
            ('c', {'stack_name': 'd'}),
        ])

        expected = {
            "private_ip": '10.20.30.45',
            "subnet_id": 1,
            "subnet_cidr": '10.20.0.0/15',
            "network": '10.20.0.0',
            "netmask": '255.254.0.0',
            "gateway_ip": '10.20.30.1',
            "mac_address": '00:01',
            "device_id": 'dev21',
            "network_id": 'net789',
            "network_name": 'a',
            "local_mac": '00:01',
            "local_ip": '10.20.30.45',
        }
        self.test_context.add_server_port(server)
        self.assertEqual(server.private_ip, '10.20.30.45')
        self.assertEqual(len(server.interfaces), 2)
        self.assertDictEqual(server.interfaces['a'], expected)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_undeploy(self, mock_template):
        self.test_context.stack = mock_template
        self.test_context.undeploy()
        self.assertTrue(mock_template.delete.called)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    @mock.patch('yardstick.benchmark.contexts.heat.os')
    def test_undeploy_key_filename(self, mock_template, mock_os):
        self.test_context.stack = mock_template
        mock_os.path.exists.return_value = True
        self.assertIsNone(self.test_context.undeploy())

    def test__get_server_found_dict(self):
        """
        Use HeatContext._get_server to get a server that matches
        based on a dictionary input.
        """
        foo2_server = mock.Mock()
        foo2_server.key_filename = 'key_file'
        foo2_server.private_ip = '10.0.0.2'
        foo2_server.public_ip = '127.0.0.2'
        foo2_server.context.user = 'oof'

        baz3_server = mock.Mock()
        baz3_server.key_filename = 'key_filename'
        baz3_server.private_ip = '10.0.0.3'
        baz3_server.public_ip = '127.0.0.3'
        baz3_server.context.user = 'zab'

        self.test_context.name = 'bar'
        self.test_context._user = 'bot'
        self.test_context.stack = mock.Mock()
        self.test_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.test_context.key_uuid = uuid.uuid4()
        self.test_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
        }

        attr_name = {
            'name': 'foo.bar',
            'private_ip_attr': 'private_ip',
            'public_ip_attr': 'public_ip',
        }
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result['user'], 'bot')
        self.assertIsNotNone(result['key_filename'])
        self.assertEqual(result['ip'], '127.0.0.1')
        self.assertEqual(result['private_ip'], '10.0.0.1')

    def test__get_server_found_dict_no_attrs(self):
        """
        Use HeatContext._get_server to get a server that matches
        based on a dictionary input.
        """
        foo2_server = mock.Mock()
        foo2_server.private_ip = '10.0.0.2'
        foo2_server.public_ip = '127.0.0.2'
        foo2_server.context.user = 'oof'

        baz3_server = mock.Mock()
        baz3_server.private_ip = '10.0.0.3'
        baz3_server.public_ip = '127.0.0.3'
        baz3_server.context.user = 'zab'

        self.test_context.name = 'bar'
        self.test_context._user = 'bot'
        self.test_context.stack = mock.Mock()
        self.test_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.test_context.key_uuid = uuid.uuid4()
        self.test_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
        }

        attr_name = {
            'name': 'foo.bar',
        }
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result['user'], 'bot')
        self.assertIsNotNone(result['key_filename'])
        # no private ip attr mapping in the map results in None value in the result
        self.assertIsNone(result['private_ip'])
        # no public ip attr mapping in the map results in no value in the result
        self.assertNotIn('ip', result)

    def test__get_server_found_not_dict(self):
        """
        Use HeatContext._get_server to get a server that matches
        based on a non-dictionary input
        """
        foo2_server = mock.Mock()
        foo2_server.private_ip = '10.0.0.2'
        foo2_server.public_ip = '127.0.0.2'
        foo2_server.context.user = 'oof'

        baz3_server = mock.Mock()
        baz3_server.private_ip = '10.0.0.3'
        baz3_server.public_ip = None
        baz3_server.context.user = 'zab'

        self.test_context.name = 'bar1'
        self.test_context.stack = mock.Mock()
        self.test_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.test_context.key_uuid = uuid.uuid4()
        self.test_context.generate_routing_table = mock.MagicMock(return_value=[])

        self.test_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
        }

        attr_name = 'baz3'
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result['user'], 'zab')
        self.assertIsNotNone(result['key_filename'])
        self.assertEqual(result['private_ip'], '10.0.0.3')
        # no public_ip on the server results in no value in the result
        self.assertNotIn('public_ip', result)

    def test__get_server_none_found_not_dict(self):
        """
        Use HeatContext._get_server to not get a server due to
        None value associated with the match to a non-dictionary
        input
        """
        foo2_server = mock.Mock()
        foo2_server.private_ip = '10.0.0.2'
        foo2_server.public_ip = '127.0.0.2'
        foo2_server.context.user = 'oof'

        baz3_server = mock.Mock()
        baz3_server.private_ip = '10.0.0.3'
        baz3_server.public_ip = None
        baz3_server.context.user = 'zab'

        self.test_context.name = 'bar1'
        self.test_context.stack = mock.Mock()
        self.test_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.test_context.key_uuid = uuid.uuid4()
        self.test_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
            'wow4': None,
        }

        attr_name = 'wow4'
        result = self.test_context._get_server(attr_name)
        self.assertIsNone(result)

    def test__get_server_not_found_dict(self):
        """
        Use HeatContext._get_server to not get a server for lack
        of a match to a dictionary input
        """
        foo2_server = mock.Mock()
        foo2_server.private_ip = '10.0.0.2'
        foo2_server.public_ip = '127.0.0.2'
        foo2_server.context.user = 'oof'

        baz3_server = mock.Mock()
        baz3_server.private_ip = '10.0.0.3'
        baz3_server.public_ip = None
        baz3_server.context.user = 'zab'

        self.test_context.name = 'bar1'
        self.test_context.stack = mock.Mock()
        self.test_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.test_context.key_uuid = uuid.uuid4()
        self.test_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
        }

        attr_name = {
            'name': 'foo.wow4',
            'private_ip_attr': 'private_ip',
            'public_ip_attr': 'public_ip',
        }
        result = self.test_context._get_server(attr_name)
        self.assertIsNone(result)

    def test__get_server_not_found_not_dict(self):
        """
        Use HeatContext._get_server to not get a server for lack
        of a match to a non-dictionary input
        """
        foo2_server = mock.Mock()
        foo2_server.private_ip = '10.0.0.2'
        foo2_server.public_ip = '127.0.0.2'
        foo2_server.context.user = 'oof'

        baz3_server = mock.Mock()
        baz3_server.private_ip = '10.0.0.3'
        baz3_server.public_ip = None
        baz3_server.context.user = 'zab'

        self.mock_context.name = 'bar1'
        self.test_context.stack = mock.Mock()
        self.mock_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.mock_context.key_uuid = uuid.uuid4()
        self.mock_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
        }

        attr_name = 'foo.wow4'
        result = self.test_context._get_server(attr_name)
        self.assertIsNone(result)

    def test__get_network(self):
        network1 = mock.MagicMock()
        network1.name = 'net_1'
        network1.vld_id = 'vld111'
        network1.segmentation_id = 'seg54'
        network1.network_type = 'type_a'
        network1.physical_network = 'phys'

        network2 = mock.MagicMock()
        network2.name = 'net_2'
        network2.vld_id = 'vld999'
        network2.segmentation_id = 'seg45'
        network2.network_type = 'type_b'
        network2.physical_network = 'virt'

        self.test_context.networks = {
            'a': network1,
            'b': network2,
        }

        attr_name = None
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = {}
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = {'vld_id': 'vld777'}
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = 'vld777'
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = {'vld_id': 'vld999'}
        expected = {
            "name": 'net_2',
            "vld_id": 'vld999',
            "segmentation_id": 'seg45',
            "network_type": 'type_b',
            "physical_network": 'virt',
        }
        result = self.test_context._get_network(attr_name)
        self.assertDictEqual(result, expected)

        attr_name = 'a'
        expected = {
            "name": 'net_1',
            "vld_id": 'vld111',
            "segmentation_id": 'seg54',
            "network_type": 'type_a',
            "physical_network": 'phys',
        }
        result = self.test_context._get_network(attr_name)
        self.assertDictEqual(result, expected)
