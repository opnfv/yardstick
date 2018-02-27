##############################################################################
# Copyright (c) 2017 Intel Corporation
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import tempfile

import mock
from oslo_serialization import jsonutils
from oslo_utils import uuidutils
import shade
import unittest

from yardstick.benchmark.contexts import node
from yardstick.common import exceptions
from yardstick.orchestrator import heat


class FakeStack(object):

    def __init__(self, outputs=None, status=None, id=None):
        self.outputs = outputs
        self.status = status
        self.id = id


class HeatStackTestCase(unittest.TestCase):

    def setUp(self):
        self.stack_name = 'STACK NAME'
        with mock.patch.object(shade, 'openstack_cloud'):
            self.heatstack = heat.HeatStack(self.stack_name)
        self._mock_stack_create = mock.patch.object(self.heatstack._cloud,
                                                    'create_stack')
        self.mock_stack_create = self._mock_stack_create.start()
        self._mock_stack_delete = mock.patch.object(self.heatstack._cloud,
                                                    'delete_stack')
        self.mock_stack_delete = self._mock_stack_delete.start()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self._mock_stack_create.stop()
        self._mock_stack_delete.stop()
        heat._DEPLOYED_STACKS = {}

    def test_create(self):
        template = {'tkey': 'tval'}
        heat_parameters = {'pkey': 'pval'}
        outputs = [{'output_key': 'okey', 'output_value': 'oval'}]
        id = uuidutils.generate_uuid()
        self.mock_stack_create.return_value = FakeStack(
            outputs=outputs, status=mock.Mock(), id=id)
        mock_tfile = mock.Mock()
        with mock.patch.object(tempfile._TemporaryFileWrapper, '__enter__',
                               return_value=mock_tfile):
            self.heatstack.create(template, heat_parameters, True, 100)
            mock_tfile.write.assert_called_once_with(jsonutils.dump_as_bytes(template))
            mock_tfile.close.assert_called_once()

        self.mock_stack_create.assert_called_once_with(
            self.stack_name, template_file=mock_tfile.name, wait=True,
            timeout=100, pkey='pval')
        self.assertEqual({'okey': 'oval'}, self.heatstack.outputs)
        self.assertEqual(heat._DEPLOYED_STACKS[id], self.heatstack._stack)

    def test_stacks_exist(self):
        self.assertEqual(0, self.heatstack.stacks_exist())
        heat._DEPLOYED_STACKS['id'] = 'stack'
        self.assertEqual(1, self.heatstack.stacks_exist())

    def test_delete_not_uuid(self):
        self.assertIsNone(self.heatstack.delete())

    def test_delete_existing_uuid(self):
        id = uuidutils.generate_uuid()
        self.heatstack._stack = FakeStack(
            outputs=mock.Mock(), status=mock.Mock(), id=id)
        heat._DEPLOYED_STACKS[id] = self.heatstack._stack
        delete_return = mock.Mock()
        self.mock_stack_delete.return_value = delete_return

        ret = self.heatstack.delete(wait=True)
        self.assertEqual(delete_return, ret)
        self.assertFalse(heat._DEPLOYED_STACKS)
        self.mock_stack_delete.assert_called_once_with(id, wait=True)

    def test_delete_bug_in_shade(self):
        id = uuidutils.generate_uuid()
        self.heatstack._stack = FakeStack(
            outputs=mock.Mock(), status=mock.Mock(), id=id)
        heat._DEPLOYED_STACKS[id] = self.heatstack._stack
        self.mock_stack_delete.side_effect = TypeError()

        ret = self.heatstack.delete(wait=True)
        self.assertTrue(ret)
        self.assertFalse(heat._DEPLOYED_STACKS)
        self.mock_stack_delete.assert_called_once_with(id, wait=True)


class HeatTemplateTestCase(unittest.TestCase):

    def setUp(self):
        self.template = heat.HeatTemplate('test')

    def test_add_tenant_network(self):
        self.template.add_network('some-network')

        self.assertEqual('OS::Neutron::Net',
                         self.template.resources['some-network']['type'])

    def test_add_provider_network(self):
        self.template.add_network('some-network', 'physnet2', 'sriov')

        self.assertEqual(self.template.resources['some-network']['type'],
                         'OS::Neutron::ProviderNet')
        self.assertEqual(self.template.resources['some-network'][
                             'properties']['physical_network'], 'physnet2')

    def test_add_subnet(self):
        netattrs = {'cidr': '10.0.0.0/24',
                    'provider': None,
                    'external_network': 'ext_net'}
        self.template.add_subnet('some-subnet', "some-network",
                                 netattrs['cidr'])

        self.assertEqual(self.template.resources['some-subnet']['type'],
                         'OS::Neutron::Subnet')
        self.assertEqual(self.template.resources['some-subnet']['properties'][
                             'cidr'], '10.0.0.0/24')

    def test_add_router(self):
        self.template.add_router('some-router', 'ext-net', 'some-subnet')

        self.assertEqual(self.template.resources['some-router']['type'],
                         'OS::Neutron::Router')
        self.assertIn('some-subnet',
                      self.template.resources['some-router']['depends_on'])

    def test_add_router_interface(self):
        self.template.add_router_interface('some-router-if', 'some-router',
                                           'some-subnet')

        self.assertEqual(self.template.resources['some-router-if']['type'],
                         'OS::Neutron::RouterInterface')
        self.assertIn('some-subnet',
                      self.template.resources['some-router-if']['depends_on'])

    def test_add_servergroup(self):
        self.template.add_servergroup('some-server-group', 'anti-affinity')

        self.assertEqual(self.template.resources['some-server-group']['type'],
                         'OS::Nova::ServerGroup')
        self.assertEqual(self.template.resources['some-server-group'][
                             'properties']['policies'], ['anti-affinity'])

    def test__add_resources_to_template_raw(self):
        test_context = node.NodeContext()
        test_context.name = 'foo'
        test_context.template_file = '/tmp/some-heat-file'
        test_context.heat_parameters = {'image': 'cirros'}
        test_context.key_filename = "/tmp/1234"
        test_context.keypair_name = "foo-key"
        test_context.secgroup_name = "foo-secgroup"
        test_context.key_uuid = "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b"

        test_context.tmpfile = tempfile.NamedTemporaryFile(
            delete=True, mode='w+t')
        test_context.tmpfile.write("heat_template_version: 2015-04-30")
        test_context.tmpfile.flush()
        test_context.tmpfile.seek(0)
        heat_template = heat.HeatTemplate('template name')
        heat_template.resources = {}

        heat_template.add_network("network1")
        heat_template.add_network("network2")
        heat_template.add_security_group("sec_group1")
        heat_template.add_security_group("sec_group2")
        heat_template.add_subnet("subnet1", "network1", "cidr1")
        heat_template.add_subnet("subnet2", "network2", "cidr2")
        heat_template.add_router("router1", "gw1", "subnet1")
        heat_template.add_router_interface("router_if1", "router1", "subnet1")
        network1 = mock.MagicMock()
        network1.stack_name = "network1"
        network1.subnet_stack_name = "subnet1"
        network1.vnic_type = "normal"
        network2 = mock.MagicMock()
        network2.stack_name = "network2"
        network2.subnet_stack_name = "subnet2"
        network2.vnic_type = "normal"
        heat_template.add_port("port1", network1)
        heat_template.add_port("port2", network2,
                               sec_group_id="sec_group1", provider="not-sriov")
        heat_template.add_port("port3", network2,
                               sec_group_id="sec_group1", provider="sriov")
        heat_template.add_floating_ip("floating_ip1", "network1", "port1",
                                      "router_if1")
        heat_template.add_floating_ip("floating_ip2", "network2", "port2",
                                      "router_if2", "foo-secgroup")
        heat_template.add_floating_ip_association("floating_ip1_association",
                                                  "floating_ip1", "port1")
        heat_template.add_servergroup("server_grp2", "affinity")
        heat_template.add_servergroup("server_grp3", "anti-affinity")
        heat_template.add_security_group("security_group")
        heat_template.add_server(name="server1", image="image1",
                                 flavor="flavor1", flavors=[])
        heat_template.add_server_group(name="servergroup",
                                       policies=["policy1", "policy2"])
        heat_template.add_server_group(name="servergroup",
                                       policies="policy1")
        heat_template.add_server(
            name="server2", image="image1", flavor="flavor1", flavors=[],
            ports=["port1", "port2"], networks=["network1", "network2"],
            scheduler_hints="hints1", user="user1", key_name="foo-key",
            user_data="user", metadata={"cat": 1, "doc": 2},
            additional_properties={"prop1": 1, "prop2": 2})
        heat_template.add_server(
            name="server2", image="image1", flavor="flavor1",
            flavors=["flavor1", "flavor2"], ports=["port1", "port2"],
            networks=["network1", "network2"], scheduler_hints="hints1",
            user="user1", key_name="foo-key", user_data="user",
            metadata={"cat": 1, "doc": 2},
            additional_properties={"prop1": 1, "prop2": 2})
        heat_template.add_server(
            name="server2", image="image1", flavor="flavor1",
            flavors=["flavor3", "flavor4"], ports=["port1", "port2"],
            networks=["network1", "network2"], scheduler_hints="hints1",
            user="user1", key_name="foo-key", user_data="user",
            metadata={"cat": 1, "doc": 2},
            additional_properties={"prop1": 1, "prop2": 2})
        heat_template.add_flavor(name="flavor1", vcpus=1, ram=2048, disk=1,
                                 extra_specs={"cat": 1, "dog": 2})
        heat_template.add_flavor(name=None, vcpus=1, ram=2048)
        heat_template.add_server(
            name="server1", image="image1", flavor="flavor1", flavors=[],
            ports=["port1", "port2"], networks=["network1", "network2"],
            scheduler_hints="hints1", user="user1", key_name="foo-key",
            user_data="user", metadata={"cat": 1, "doc": 2},
            additional_properties={"prop1": 1, "prop2": 2})
        heat_template.add_network("network1")

        heat_template.add_flavor("test")
        self.assertEqual(heat_template.resources['test']['type'],
                         'OS::Nova::Flavor')

    def test_create_not_block(self):
        heat_stack = mock.Mock()
        with mock.patch.object(heat, 'HeatStack', return_value=heat_stack):
            ret = self.template.create(block=False)
        heat_stack.create.assert_called_once_with(
            self.template._template, self.template.heat_parameters, False,
            3600)
        self.assertEqual(heat_stack, ret)

    def test_create_block(self):
        heat_stack = mock.Mock()
        heat_stack.status = self.template.HEAT_STATUS_COMPLETE
        with mock.patch.object(heat, 'HeatStack', return_value=heat_stack):
            ret = self.template.create(block=False)
        heat_stack.create.assert_called_once_with(
            self.template._template, self.template.heat_parameters, False,
            3600)
        self.assertEqual(heat_stack, ret)


    def test_create_block_status_no_complete(self):
        heat_stack = mock.Mock()
        heat_stack.status = 'other status'
        with mock.patch.object(heat, 'HeatStack', return_value=heat_stack):
            self.assertRaises(exceptions.HeatTemplateError,
                              self.template.create, block=True)
        heat_stack.create.assert_called_once_with(
            self.template._template, self.template.heat_parameters, True,
            3600)
