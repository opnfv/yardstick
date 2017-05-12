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

from tempfile import NamedTemporaryFile
import unittest
import uuid
import mock

from yardstick.benchmark.contexts import node
from yardstick.orchestrator import heat


class HeatContextTestCase(unittest.TestCase):

    def test_get_short_key_uuid(self):
        u = uuid.uuid4()
        k = heat.get_short_key_uuid(u)
        self.assertEqual(heat.HEAT_KEY_UUID_LENGTH, len(k))
        self.assertIn(k, str(u))

class HeatTemplateTestCase(unittest.TestCase):

    def setUp(self):
        self.template = heat.HeatTemplate('test')

    def test_add_tenant_network(self):
        self.template.add_network('some-network')

        self.assertEqual(self.template.resources['some-network']['type'], 'OS::Neutron::Net')

    def test_add_provider_network(self):
        self.template.add_network('some-network', 'physnet2', 'sriov')

        self.assertEqual(self.template.resources['some-network']['type'], 'OS::Neutron::ProviderNet')
        self.assertEqual(self.template.resources['some-network']['properties']['physical_network'], 'physnet2')

    def test_add_subnet(self):
        netattrs = {'cidr': '10.0.0.0/24', 'provider': None, 'external_network': 'ext_net'}
        self.template.add_subnet('some-subnet', "some-network", netattrs['cidr'])

        self.assertEqual(self.template.resources['some-subnet']['type'], 'OS::Neutron::Subnet')
        self.assertEqual(self.template.resources['some-subnet']['properties']['cidr'], '10.0.0.0/24')

    def test_add_router(self):
        self.template.add_router('some-router', 'ext-net', 'some-subnet')

        self.assertEqual(self.template.resources['some-router']['type'], 'OS::Neutron::Router')
        self.assertIn('some-subnet', self.template.resources['some-router']['depends_on'])

    def test_add_router_interface(self):
        self.template.add_router_interface('some-router-if', 'some-router', 'some-subnet')

        self.assertEqual(self.template.resources['some-router-if']['type'], 'OS::Neutron::RouterInterface')
        self.assertIn('some-subnet', self.template.resources['some-router-if']['depends_on'])

    def test_add_servergroup(self):
        self.template.add_servergroup('some-server-group', 'anti-affinity')

        self.assertEqual(self.template.resources['some-server-group']['type'], 'OS::Nova::ServerGroup')
        self.assertEqual(self.template.resources['some-server-group']['properties']['policies'], ['anti-affinity'])

    def test__add_resources_to_template_raw(self):

        self.test_context = node.NodeContext()
        self.test_context.name = 'foo'
        self.test_context.template_file = '/tmp/some-heat-file'
        self.test_context.heat_parameters = {'image': 'cirros'}
        self.test_context.key_filename = "/tmp/1234"
        self.test_context.keypair_name = "foo-key"
        self.test_context.secgroup_name = "foo-secgroup"
        self.test_context.key_uuid = "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b"
        self._template = {
            'outputs' : {},
            'resources' : {}
        }

        self.heat_object = heat.HeatObject()
        self.heat_tmp_object = heat.HeatObject()

        self.heat_stack = heat.HeatStack("tmpStack")
        self.heat_stack.stacks_exist()

        self.test_context.tmpfile = NamedTemporaryFile(delete=True, mode='w+t')
        self.test_context.tmpfile.write("heat_template_version: 2015-04-30")
        self.test_context.tmpfile.flush()
        self.test_context.tmpfile.seek(0)
        self.heat_tmp_template = heat.HeatTemplate(self.heat_tmp_object, self.test_context.tmpfile.name,
                                                   heat_parameters= {"dict1": 1, "dict2": 2})

        self.heat_template = heat.HeatTemplate(self.heat_object)
        self.heat_template.resources = {}

        self.heat_template.add_network("network1")
        self.heat_template.add_network("network2")
        self.heat_template.add_security_group("sec_group1")
        self.heat_template.add_security_group("sec_group2")
        self.heat_template.add_subnet("subnet1", "network1", "cidr1")
        self.heat_template.add_subnet("subnet2", "network2", "cidr2")
        self.heat_template.add_router("router1", "gw1", "subnet1")
        self.heat_template.add_router_interface("router_if1", "router1", "subnet1")
        self.heat_template.add_port("port1", "network1", "subnet1")
        self.heat_template.add_port("port2", "network2", "subnet2", sec_group_id="sec_group1",provider="not-sriov")
        self.heat_template.add_port("port3", "network2", "subnet2", sec_group_id="sec_group1",provider="sriov")
        self.heat_template.add_floating_ip("floating_ip1", "network1", "port1", "router_if1")
        self.heat_template.add_floating_ip("floating_ip2", "network2", "port2", "router_if2", "foo-secgroup")
        self.heat_template.add_floating_ip_association("floating_ip1_association", "floating_ip1", "port1")
        self.heat_template.add_servergroup("server_grp2", "affinity")
        self.heat_template.add_servergroup("server_grp3", "anti-affinity")
        self.heat_template.add_security_group("security_group")
        self.heat_template.add_server(name="server1", image="image1", flavor="flavor1", flavors=[])
        self.heat_template.add_server_group(name="servergroup", policies=["policy1","policy2"])
        self.heat_template.add_server_group(name="servergroup", policies="policy1")
        self.heat_template.add_server(name="server2", image="image1", flavor="flavor1", flavors=[], ports=["port1", "port2"],
                                 networks=["network1", "network2"], scheduler_hints="hints1", user="user1",
                                 key_name="foo-key", user_data="user", metadata={"cat": 1, "doc": 2},
                                 additional_properties={"prop1": 1, "prop2": 2})
        self.heat_template.add_server(name="server2", image="image1", flavor="flavor1", flavors=["flavor1", "flavor2"],
                                 ports=["port1", "port2"],
                                 networks=["network1", "network2"], scheduler_hints="hints1", user="user1",
                                 key_name="foo-key", user_data="user", metadata={"cat": 1, "doc": 2},
                                 additional_properties={"prop1": 1, "prop2": 2} )
        self.heat_template.add_server(name="server2", image="image1", flavor="flavor1", flavors=["flavor3", "flavor4"],
                                 ports=["port1", "port2"],
                                 networks=["network1", "network2"], scheduler_hints="hints1", user="user1",
                                 key_name="foo-key", user_data="user", metadata={"cat": 1, "doc": 2},
                                 additional_properties={"prop1": 1, "prop2": 2})
        self.heat_template.add_flavor(name="flavor1", vcpus=1, ram=2048, disk=1,extra_specs={"cat": 1, "dog": 2})
        self.heat_template.add_flavor(name=None, vcpus=1, ram=2048)
        self.heat_template.add_server(name="server1",
                                      image="image1",
                                      flavor="flavor1",
                                      flavors=[],
                                      ports=["port1", "port2"],
                                      networks=["network1", "network2"],
                                      scheduler_hints="hints1",
                                      user="user1",
                                      key_name="foo-key",
                                      user_data="user",
                                      metadata={"cat": 1, "doc": 2},
                                      additional_properties= {"prop1": 1, "prop2": 2} )
        self.heat_template.add_network("network1")

        self.heat_template.add_flavor("test")
        self.assertEqual(self.heat_template.resources['test']['type'], 'OS::Nova::Flavor')


class HeatStackTestCase(unittest.TestCase):

    def test_delete_calls__delete_multiple_times(self):
        stack = heat.HeatStack('test')
        stack.uuid = 1
        with mock.patch.object(stack, "_delete") as delete_mock:
            stack.delete()
        # call once and then call again if uuid is not none
        self.assertGreater(delete_mock.call_count, 1)

    def test_delete_all_calls_delete(self):
        stack = heat.HeatStack('test')
        stack.uuid = 1
        with mock.patch.object(stack, "delete") as delete_mock:
            stack.delete_all()
        self.assertGreater(delete_mock.call_count, 0)
