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

import logging
import os
import unittest
import uuid

import mock

from yardstick.benchmark.contexts import heat


LOG = logging.getLogger(__name__)


class HeatContextTestCase(unittest.TestCase):

    def setUp(self):
        self.test_context = heat.HeatContext()
        self.mock_context = mock.Mock(spec=heat.HeatContext())

    def test_construct(self):

        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.stack)
        self.assertEqual(self.test_context.networks, [])
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

        self.test_context._add_resources_to_template(mock_template)
        mock_template.add_keypair.assert_called_with(
            "foo-key",
            "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b")
        mock_template.add_security_group.assert_called_with("foo-secgroup")
        mock_template.add_flavor("test")
        mock_template.add_flavor(vcpus=4, ram=2048)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test__add_resources_to_template_misc(self, mock_template):

        self.test_context.keypair_name = "foo-key"
        self.test_context.secgroup_name = "foo-secgroup"
        self.test_context.key_uuid = "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b"

        self.test_context._add_resources_to_template(mock_template)
        mock_template.add_keypair.assert_called_with(
            "foo-key",
            "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b")
        mock_template.add_security_group.assert_called_with("foo-secgroup")
        mock_template.add_flavor("test")
        mock_template.add_flavor(vcpus=4, ram=2048)
        mock_template.add_flavor(vcpus=4, ram=2048, extra_specs={"cat": 1, "dog": 2})
        mock_template.add_network("network1")
        mock_template.add_network("network2")
        mock_template.add_security_group("sec_group1", "nopolicy")
        mock_template.add_security_group("sec_group2", ["policy1", "policy2"])
        mock_template.add_subnet("subnet1", "network1", "cidr1")
        mock_template.add_subnet("subnet2", "network2", "cidr2")
        mock_template.add_router("router1", "gw1", "subnet1")
        mock_template.add_router_interface("router_if1", "router1" ,"subnet1")
        mock_template.add_port("port1", "network1", "subnet1")
        mock_template.add_port("port2", "network2", "subnet2", sec_group_id="sec_group1")
        mock_template.add_floating_ip("floating_ip1", "network1", "port1", "router_if1")
        mock_template.add_floating_ip("floating_ip2", "network2", "port2", "router_if2","foo-secgroup")
        mock_template.add_floating_ip_association("floating_ip1_association", "floating_ip1", "port1")
        mock_template.add_servergroup("server_grp1","nopolicy")
        mock_template.add_servergroup("server_grp2", "affinity")
        mock_template.add_servergroup("server_grp3", "anti-affinity")
        mock_template.add_security_group("security_group")
        mock_template.add_server(name="server1", image="image1", flavor="flavor1")
        mock_template.add_server(name="server2", image="image1", flavor="flavor1", ports=["port1","port2"],
                                    networks=["network1","network2"], scheduler_hints="hints1", user="user1",
                                    key_name="foo-key", user_data="user", metadata={"cat":1, "doc": 2},
                                    additional_properties={"prop1": 1, "prop2": 2})
        mock_template.add_server(image="image1", flavor="flavor1", ports=["port1", "port2"],
                                networks=["network1", "network2"], scheduler_hints="hints1", user="user1",
                                key_name="foo-key", user_data="user", metadata={"cat": 1, "doc": 2},
                                additional_properties={"prop1": 1, "prop2": 2})

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_deploy(self, mock_template):

        self.test_context.name = 'foo'
        self.test_context.template_file = '/bar/baz/some-heat-file'
        self.test_context.heat_parameters = {'image': 'cirros'}
        self.test_context.deploy()

        mock_template.assert_called_with(self.test_context.name,
                                         self.test_context.template_file,
                                         self.test_context.heat_parameters)
        self.assertIsNotNone(self.test_context.stack)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_undeploy(self, mock_template):

        self.test_context.stack = mock_template
        self.test_context.undeploy()

        self.assertTrue(mock_template.delete.called)

    def test__get_server(self):

        self.mock_context.name = 'bar'
        self.mock_context.stack.outputs = {'public_ip': '127.0.0.1',
                                           'private_ip': '10.0.0.1'}
        self.mock_context.key_uuid = uuid.uuid4()

        attr_name = {'name': 'foo.bar',
                     'public_ip_attr': 'public_ip',
                     'private_ip_attr': 'private_ip'}
        result = heat.HeatContext._get_server(self.mock_context, attr_name)

        self.assertEqual(result['ip'], '127.0.0.1')
        self.assertEqual(result['private_ip'], '10.0.0.1')
