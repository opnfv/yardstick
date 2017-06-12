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
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
import unittest
import uuid
import time
import mock

from yardstick.benchmark.contexts import node
from yardstick.orchestrator import heat


@contextmanager
def timer():
    data = {'start': time.time()}
    yield data
    data['end'] = time.time()
    data['delta'] = data['end'] - data['start']


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
        test_context = node.NodeContext()
        test_context.name = 'foo'
        test_context.template_file = '/tmp/some-heat-file'
        test_context.heat_parameters = {'image': 'cirros'}
        test_context.key_filename = "/tmp/1234"
        test_context.keypair_name = "foo-key"
        test_context.secgroup_name = "foo-secgroup"
        test_context.key_uuid = "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b"
        heat_object = heat.HeatObject()

        heat_stack = heat.HeatStack("tmpStack")
        self.assertTrue(heat_stack.stacks_exist())

        test_context.tmpfile = NamedTemporaryFile(delete=True, mode='w+t')
        test_context.tmpfile.write("heat_template_version: 2015-04-30")
        test_context.tmpfile.flush()
        test_context.tmpfile.seek(0)
        heat_template = heat.HeatTemplate(heat_object)
        heat_template.resources = {}

        heat_template.add_network("network1")
        heat_template.add_network("network2")
        heat_template.add_security_group("sec_group1")
        heat_template.add_security_group("sec_group2")
        heat_template.add_subnet("subnet1", "network1", "cidr1")
        heat_template.add_subnet("subnet2", "network2", "cidr2")
        heat_template.add_router("router1", "gw1", "subnet1")
        heat_template.add_router_interface("router_if1", "router1", "subnet1")
        heat_template.add_port("port1", "network1", "subnet1")
        heat_template.add_port("port2", "network2", "subnet2", sec_group_id="sec_group1",provider="not-sriov")
        heat_template.add_port("port3", "network2", "subnet2", sec_group_id="sec_group1",provider="sriov")
        heat_template.add_floating_ip("floating_ip1", "network1", "port1", "router_if1")
        heat_template.add_floating_ip("floating_ip2", "network2", "port2", "router_if2", "foo-secgroup")
        heat_template.add_floating_ip_association("floating_ip1_association", "floating_ip1", "port1")
        heat_template.add_servergroup("server_grp2", "affinity")
        heat_template.add_servergroup("server_grp3", "anti-affinity")
        heat_template.add_security_group("security_group")
        heat_template.add_server(name="server1", image="image1", flavor="flavor1", flavors=[])
        heat_template.add_server_group(name="servergroup", policies=["policy1","policy2"])
        heat_template.add_server_group(name="servergroup", policies="policy1")
        heat_template.add_server(name="server2", image="image1", flavor="flavor1", flavors=[], ports=["port1", "port2"],
                                 networks=["network1", "network2"], scheduler_hints="hints1", user="user1",
                                 key_name="foo-key", user_data="user", metadata={"cat": 1, "doc": 2},
                                 additional_properties={"prop1": 1, "prop2": 2})
        heat_template.add_server(name="server2", image="image1", flavor="flavor1", flavors=["flavor1", "flavor2"],
                                 ports=["port1", "port2"],
                                 networks=["network1", "network2"], scheduler_hints="hints1", user="user1",
                                 key_name="foo-key", user_data="user", metadata={"cat": 1, "doc": 2},
                                 additional_properties={"prop1": 1, "prop2": 2} )
        heat_template.add_server(name="server2", image="image1", flavor="flavor1", flavors=["flavor3", "flavor4"],
                                 ports=["port1", "port2"],
                                 networks=["network1", "network2"], scheduler_hints="hints1", user="user1",
                                 key_name="foo-key", user_data="user", metadata={"cat": 1, "doc": 2},
                                 additional_properties={"prop1": 1, "prop2": 2})
        heat_template.add_flavor(name="flavor1", vcpus=1, ram=2048, disk=1,extra_specs={"cat": 1, "dog": 2})
        heat_template.add_flavor(name=None, vcpus=1, ram=2048)
        heat_template.add_server(name="server1",
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
        heat_template.add_network("network1")

        heat_template.add_flavor("test")
        self.assertEqual(heat_template.resources['test']['type'], 'OS::Nova::Flavor')

    @mock.patch('heatclient.client.Client')
    @mock.patch('yardstick.common.openstack_utils.get_session')
    def test_create_negative(self, mock_heat_client, mock_get_session):
        self.template.HEAT_WAIT_LOOP_INTERVAL = interval = 0.2
        mock_heat_client.stacks.get.stack_status_reason = 'the reason'
        with mock.patch.object(self.template, 'status', return_value=None) as mock_status:
            # block with timeout hit
            timeout = 2
            with self.assertRaises(RuntimeError) as raised, timer() as time_data:
                self.template.create(block=True, timeout=timeout)

            self.assertEqual(mock_get_session.call_count, 1)
            self.assertEqual(mock_heat_client.call_count, 1)
            self.assertGreaterEqual(time_data['delta'], interval)
            self.assertLess(time_data['delta'], timeout + interval)
            self.assertIn('timeout', raised.msg)
            self.assertNotIn('the reason', raised.msg)
            self.assertEqual(mock_heat_client.stacks.create.call_count, 1)

            # block with create failed
            timeout = 10
            mock_status.side_effect = iter([None, None, u'CREATE_FAILED'])
            with self.assertRaises(RuntimeError) as raised, timer() as time_data:
                self.template.create(block=True, timeout=timeout)

            self.assertEqual(mock_heat_client.call_count, 1)
            self.assertGreater(time_data['delta'], interval * 1.8)
            self.assertLess(time_data['delta'], interval * 3.2)
            self.assertNotIn('timeout', raised.msg)
            self.assertIn('the reason', raised.msg)
            self.assertEqual(mock_heat_client.stacks.create.call_count, 1)

    @mock.patch('heatclient.client.Client')
    @mock.patch('yardstick.common.openstack_utils.get_session')
    def test_create(self, mock_heat_client, mock_get_session):
        self.template.HEAT_WAIT_LOOP_INTERVAL = interval = 0.2
        mock_heat_client.stacks.get.stack_status_reason = 'the reason'
        with mock.patch.object(self.template, 'status') as mock_status:
            mock_heat_client.stacks.get.outputs = [
                {'output_key': 'key1', 'output_value': 'value1'},
                {'output_key': 'key2', 'output_value': 'value2'},
                {'output_key': 'key3', 'output_value': 'value3'},
            ]
            expected_outputs = {
                'key1': 'value1',
                'key2': 'value2',
                'key3': 'value3',
            }

            # no block
            with timer() as time_data:
                self.assertIsInstance(self.template.create(block=False, timeout=2), heat.HeatStack)

            self.assertEqual(mock_get_session.call_count, 1)
            self.assertEqual(mock_heat_client.call_count, 1)
            self.assertLess(time_data['delta'], interval)
            self.assertEqual(mock_status.call_count, 0)

            # no outputs because this requires blocking
            self.assertEqual(self.template.outputs, {})

            # block with immediate complete
            mock_status.return_value = u'CREATE_COMPLETE'
            with timer() as time_data:
                self.assertIsInstance(self.template.create(block=True, timeout=2), heat.HeatStack)

            self.assertEqual(mock_heat_client.call_count, 1)
            self.assertLess(time_data['delta'], interval)
            self.assertEqual(mock_heat_client.stacks.create.call_count, 1)
            self.assertEqual(mock_status.call_count, 1)
            self.assertEqual(self.template.outputs, expected_outputs)

            # block with delayed complete
            mock_status.side_effect = iter([None, None, u'CREATE_COMPLETE'])
            with timer() as time_data:
                self.assertIsInstance(self.template.create(block=True, timeout=2), heat.HeatStack)

            self.assertEqual(mock_heat_client.call_count, 1)
            self.assertGreaterEqual(time_data['delta'], interval * 1.8)
            self.assertLess(time_data['delta'], interval * 3.2)
            self.assertEqual(mock_heat_client.stacks.create.call_count, 1)
            self.assertEqual(mock_status.call_count, 3)


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
