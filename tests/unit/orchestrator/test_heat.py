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
from itertools import count
from tempfile import NamedTemporaryFile
import unittest
import uuid
import time
import mock

from yardstick.benchmark.contexts import node
from yardstick.orchestrator import heat


TARGET_MODULE = 'yardstick.orchestrator.heat'


def mock_patch_target_module(inner_import):
    return mock.patch('.'.join([TARGET_MODULE, inner_import]))


@contextmanager
def timer():
    start = time.time()
    data = {'start': start}
    try:
        yield data
    finally:
        data['end'] = end = time.time()
        data['delta'] = end - start


def index_value_iter(index, index_value, base_value=None):
    for current_index in count():
        if current_index == index:
            yield index_value
        else:
            yield base_value


def get_error_message(error):
    try:
        # py2
        return error.message
    except AttributeError:
        # py3
        return next((arg for arg in error.args if isinstance(arg, str)), None)


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
        heat_template.add_port("port1", "network1", "subnet1", "normal")
        heat_template.add_port("port2", "network2", "subnet2", "normal", sec_group_id="sec_group1",provider="not-sriov")
        heat_template.add_port("port3", "network2", "subnet2", "normal", sec_group_id="sec_group1",provider="sriov")
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

    @mock_patch_target_module('op_utils')
    @mock_patch_target_module('heatclient')
    def test_create_negative(self, mock_heat_client_class, mock_op_utils):
        self.template.HEAT_WAIT_LOOP_INTERVAL = 0
        mock_heat_client = mock_heat_client_class()  # get the constructed mock

        # populate attributes of the constructed mock
        mock_heat_client.stacks.get().stack_status_reason = 'the reason'

        expected_status_calls = 0
        expected_constructor_calls = 1  # above, to get the instance
        expected_create_calls = 0
        expected_op_utils_usage = 0

        with mock.patch.object(self.template, 'status', return_value=None) as mock_status:
            # block with timeout hit
            timeout = 0
            with self.assertRaises(RuntimeError) as raised, timer() as time_data:
                self.template.create(block=True, timeout=timeout)

            # ensure op_utils was used
            expected_op_utils_usage += 1
            self.assertEqual(mock_op_utils.get_session.call_count, expected_op_utils_usage)
            self.assertEqual(mock_op_utils.get_endpoint.call_count, expected_op_utils_usage)
            self.assertEqual(mock_op_utils.get_heat_api_version.call_count, expected_op_utils_usage)

            # ensure the constructor and instance were used
            self.assertEqual(mock_heat_client_class.call_count, expected_constructor_calls)
            self.assertEqual(mock_heat_client.stacks.create.call_count, expected_create_calls)

            # ensure that the status was used
            self.assertGreater(mock_status.call_count, expected_status_calls)
            expected_status_calls = mock_status.call_count  # synchronize the value

            # ensure the expected exception was raised
            error_message = get_error_message(raised.exception)
            self.assertIn('timeout', error_message)
            self.assertNotIn('the reason', error_message)

            # block with create failed
            timeout = 10
            mock_status.side_effect = iter([None, None, u'CREATE_FAILED'])
            with self.assertRaises(RuntimeError) as raised, timer() as time_data:
                self.template.create(block=True, timeout=timeout)

            # ensure the existing heat_client was used and op_utils was used again
            self.assertEqual(mock_op_utils.get_session.call_count, expected_op_utils_usage)
            self.assertEqual(mock_op_utils.get_endpoint.call_count, expected_op_utils_usage)
            self.assertEqual(mock_op_utils.get_heat_api_version.call_count, expected_op_utils_usage)

            # ensure the constructor was not used but the instance was used
            self.assertEqual(mock_heat_client_class.call_count, expected_constructor_calls)
            self.assertEqual(mock_heat_client.stacks.create.call_count, expected_create_calls)

            # ensure that the status was used three times
            expected_status_calls += 3
            self.assertEqual(mock_status.call_count, expected_status_calls)

    @mock_patch_target_module('op_utils')
    @mock_patch_target_module('heatclient')
    def test_create(self, mock_heat_client_class, mock_op_utils):
        self.template.HEAT_WAIT_LOOP_INTERVAL = 0.2
        mock_heat_client = mock_heat_client_class()

        # populate attributes of the constructed mock
        mock_heat_client.stacks.get().outputs = [
            {'output_key': 'key1', 'output_value': 'value1'},
            {'output_key': 'key2', 'output_value': 'value2'},
            {'output_key': 'key3', 'output_value': 'value3'},
        ]
        expected_outputs = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3',
        }

        expected_status_calls = 0
        expected_constructor_calls = 1  # above, to get the instance
        expected_create_calls = 0
        expected_op_utils_usage = 0

        with mock.patch.object(self.template, 'status') as mock_status:
            self.template.name = 'no block test'
            mock_status.return_value = None

            # no block
            self.assertIsInstance(self.template.create(block=False, timeout=2), heat.HeatStack)

            # ensure op_utils was used
            expected_op_utils_usage += 1
            self.assertEqual(mock_op_utils.get_session.call_count, expected_op_utils_usage)
            self.assertEqual(mock_op_utils.get_endpoint.call_count, expected_op_utils_usage)
            self.assertEqual(mock_op_utils.get_heat_api_version.call_count, expected_op_utils_usage)

            # ensure the constructor and instance were used
            self.assertEqual(mock_heat_client_class.call_count, expected_constructor_calls)
            self.assertEqual(mock_heat_client.stacks.create.call_count, expected_create_calls)

            # ensure that the status was not used
            self.assertEqual(mock_status.call_count, expected_status_calls)

            # ensure no outputs because this requires blocking
            self.assertEqual(self.template.outputs, {})

            # block with immediate complete
            self.template.name = 'block, immediate complete test'

            mock_status.return_value = self.template.HEAT_CREATE_COMPLETE_STATUS
            self.assertIsInstance(self.template.create(block=True, timeout=2), heat.HeatStack)

            # ensure existing instance was re-used and op_utils was not used
            self.assertEqual(mock_heat_client_class.call_count, expected_constructor_calls)
            self.assertEqual(mock_heat_client.stacks.create.call_count, expected_create_calls)

            # ensure status was checked once
            expected_status_calls += 1
            self.assertEqual(mock_status.call_count, expected_status_calls)

            # reset template outputs
            self.template.outputs = None

            # block with delayed complete
            self.template.name = 'block, delayed complete test'

            success_index = 2
            mock_status.side_effect = index_value_iter(success_index,
                                                       self.template.HEAT_CREATE_COMPLETE_STATUS)
            self.assertIsInstance(self.template.create(block=True, timeout=2), heat.HeatStack)

            # ensure existing instance was re-used and op_utils was not used
            self.assertEqual(mock_heat_client_class.call_count, expected_constructor_calls)
            self.assertEqual(mock_heat_client.stacks.create.call_count, expected_create_calls)

            # ensure status was checked three more times
            expected_status_calls += 1 + success_index
            self.assertEqual(mock_status.call_count, expected_status_calls)


class HeatStackTestCase(unittest.TestCase):

    def test_delete_calls__delete_multiple_times(self):
        stack = heat.HeatStack('test')
        stack.uuid = 1
        with mock.patch.object(stack, "_delete") as delete_mock:
            stack.delete()
        # call once and then call again if uuid is not none
        self.assertGreater(delete_mock.call_count, 1)

    @mock.patch('yardstick.orchestrator.heat.op_utils')
    def test_delete_all_calls_delete(self, mock_op):
        # we must patch the object before we create an instance
        # so we can override delete() in all the instances
        with mock.patch.object(heat.HeatStack, "delete") as delete_mock:
            stack = heat.HeatStack('test')
            stack.uuid = 1
            stack.delete_all()
            self.assertGreater(delete_mock.call_count, 0)
