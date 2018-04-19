##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from collections import OrderedDict
from itertools import count
import logging
import os

import mock
import unittest

from yardstick.benchmark.contexts import base
from yardstick.benchmark.contexts import heat
from yardstick.benchmark.contexts import model
from yardstick.common import constants as consts
from yardstick.common import exceptions as y_exc
from yardstick import ssh


LOG = logging.getLogger(__name__)


class HeatContextTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(HeatContextTestCase, self).__init__(*args, **kwargs)
        self.name_iter = ('vnf{:03}'.format(x) for x in count(0, step=3))

    def setUp(self):
        self.test_context = heat.HeatContext()
        self.addCleanup(self._remove_contexts)
        self.mock_context = mock.Mock(spec=heat.HeatContext())

    def _remove_contexts(self):
        if self.test_context in self.test_context.list:
            self.test_context._delete_context()

    def test___init__(self):
        self.assertIsNone(self.test_context._name)
        self.assertIsNone(self.test_context._task_id)
        self.assertFalse(self.test_context._flags.no_setup)
        self.assertFalse(self.test_context._flags.no_teardown)
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
        self.assertIsNone(self.test_context.key_filename)

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
                 'task_id': '1234567890',
                 'placement_groups': pgs,
                 'server_groups': sgs,
                 'networks': networks,
                 'servers': servers}

        self.test_context.init(attrs)

        self.assertFalse(self.test_context._flags.no_setup)
        self.assertFalse(self.test_context._flags.no_teardown)
        self.assertEqual(self.test_context._name, "foo")
        self.assertEqual(self.test_context._task_id, '1234567890')
        self.assertEqual(self.test_context.name, "foo-12345678")
        self.assertEqual(self.test_context.keypair_name, "foo-12345678-key")
        self.assertEqual(self.test_context.secgroup_name, "foo-12345678-secgroup")

        mock_pg.assert_called_with('pgrp1', self.test_context,
                                   pgs['pgrp1']['policy'])
        mock_sg.assert_called_with('servergroup1', self.test_context,
                                   sgs['servergroup1']['policy'])
        self.assertEqual(len(self.test_context.placement_groups), 1)
        self.assertEqual(len(self.test_context.server_groups), 1)

        mock_network.assert_called_with(
            'bar', self.test_context, networks['bar'])
        self.assertEqual(len(self.test_context.networks), 1)

        mock_server.assert_called_with('baz', self.test_context,
                                       servers['baz'])
        self.assertEqual(len(self.test_context.servers), 1)

    def test_init_no_name_or_task_id(self):
        attrs = {}
        self.assertRaises(KeyError, self.test_context.init, attrs)

    def test_name(self):
        self.test_context._name = 'foo'
        self.test_context._task_id = '1234567890'
        self.test_context._name_task_id = '{}-{}'.format(
            self.test_context._name, self.test_context._task_id[:8])
        self.assertEqual(self.test_context.name, 'foo-12345678')
        self.assertEqual(self.test_context.assigned_name, 'foo')

    def test_name_flags(self):
        self.test_context._flags = base.Flags(
            **{"no_setup": True, "no_teardown": True})
        self.test_context._name = 'foo'
        self.test_context._task_id = '1234567890'

        self.assertEqual(self.test_context.name, 'foo')
        self.assertEqual(self.test_context.assigned_name, 'foo')

    def test_init_no_setup_no_teardown(self):

        attrs = {'name': 'foo',
                 'task_id': '1234567890',
                 'placement_groups': {},
                 'server_groups': {},
                 'networks': {},
                 'servers': {},
                 'flags': {
                     'no_setup': True,
                     'no_teardown': True,
                     },
                }

        self.test_context.init(attrs)
        self.assertTrue(self.test_context._flags.no_setup)
        self.assertTrue(self.test_context._flags.no_teardown)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test__add_resources_to_template_no_servers(self, mock_template):
        self.test_context._name = 'ctx'
        self.test_context._task_id = '1234567890'
        self.test_context._name_task_id = '{}-{}'.format(
            self.test_context._name, self.test_context._task_id[:8])
        self.test_context.keypair_name = "ctx-key"
        self.test_context.secgroup_name = "ctx-secgroup"
        self.test_context.key_uuid = "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b"
        netattrs = {'cidr': '10.0.0.0/24', 'provider': None,
                    'external_network': 'ext_net'}

        self.test_context.networks = OrderedDict(
            {"mynet": model.Network("mynet", self.test_context,
                                           netattrs)})

        self.test_context._add_resources_to_template(mock_template)
        mock_template.add_keypair.assert_called_with(
            "ctx-key",
            "ctx-12345678")
        mock_template.add_security_group.assert_called_with("ctx-secgroup")
        mock_template.add_network.assert_called_with(
            "ctx-12345678-mynet", 'physnet1', None, None, None, None)
        mock_template.add_router.assert_called_with(
            "ctx-12345678-mynet-router",
            netattrs["external_network"],
            "ctx-12345678-mynet-subnet")
        mock_template.add_router_interface.assert_called_with(
            "ctx-12345678-mynet-router-if0",
            "ctx-12345678-mynet-router",
            "ctx-12345678-mynet-subnet")

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_attrs_get(self, *args):
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
    def test_attrs_set_negative(self, *args):
        with self.assertRaises(AttributeError):
            self.test_context.image = 'foo'

        with self.assertRaises(AttributeError):
            self.test_context.flavor = 'foo'

        with self.assertRaises(AttributeError):
            self.test_context.user = 'foo'

    def test__create_new_stack(self):
        template = mock.Mock()
        self.test_context._create_new_stack(template)
        template.create.assert_called_once()

    def test__create_new_stack_stack_create_failed(self):
        template = mock.Mock()
        template.create.side_effect = y_exc.HeatTemplateError

        self.assertRaises(y_exc.HeatTemplateError,
                          self.test_context._create_new_stack,
                          template)

    def test__create_new_stack_keyboard_interrupt(self):
        template = mock.Mock()
        template.create.side_effect = KeyboardInterrupt
        self.assertRaises(y_exc.StackCreationInterrupt,
                          self.test_context._create_new_stack,
                          template)

    @mock.patch.object(os.path, 'exists', return_value=True)
    @mock.patch.object(heat.HeatContext, '_add_resources_to_template')
    @mock.patch.object(heat.HeatContext, '_create_new_stack')
    def test_deploy_stack_creation_failed(self, mock_create,
            mock_resources_template, mock_path_exists):
        self.test_context._name = 'foo'
        self.test_context._task_id = '1234567890'
        self.test_context._name_task_id = 'foo-12345678'
        mock_create.side_effect = y_exc.HeatTemplateError
        self.assertRaises(y_exc.HeatTemplateError,
                          self.test_context.deploy)

        # RAH: test
        if len(mock_path_exists.call_args_list) > 1:
            print(mock_path_exists.call_args_list)
            raise Exception(mock_path_exists.call_args_list)
        mock_path_exists.assert_called_once()
        mock_resources_template.assert_called_once()

    @mock.patch.object(os.path, 'exists', return_value=False)
    @mock.patch.object(ssh.SSH, 'gen_keys')
    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_deploy(self, mock_template, mock_genkeys, mock_path_exists):
        self.test_context._name = 'foo'
        self.test_context._task_id = '1234567890'
        self.test_context._name_task_id = '{}-{}'.format(
            self.test_context._name, self.test_context._task_id[:8])
        self.test_context.template_file = '/bar/baz/some-heat-file'
        self.test_context.heat_parameters = {'image': 'cirros'}
        self.test_context.get_neutron_info = mock.MagicMock()
        self.test_context.deploy()

        mock_template.assert_called_with('foo-12345678',
                                         '/bar/baz/some-heat-file',
                                         {'image': 'cirros'})
        self.assertIsNotNone(self.test_context.stack)
        key_filename = ''.join(
            [consts.YARDSTICK_ROOT_PATH,
             'yardstick/resources/files/yardstick_key-',
             self.test_context._name_task_id])
        mock_genkeys.assert_called_once_with(key_filename)
        # RAH: test
        if len(mock_path_exists.call_args_list) > 1:
            print(mock_path_exists.call_args_list)
            raise Exception(mock_path_exists.call_args_list)
        mock_path_exists.assert_called_once_with(key_filename)

    @mock.patch.object(heat, 'HeatTemplate')
    @mock.patch.object(os.path, 'exists', return_value=False)
    @mock.patch.object(ssh.SSH, 'gen_keys')
    @mock.patch.object(heat.HeatContext, '_retrieve_existing_stack')
    @mock.patch.object(heat.HeatContext, '_create_new_stack')
    def test_deploy_no_setup(self, mock_create_new_stack,
            mock_retrieve_existing_stack, mock_genkeys, mock_path_exists,
            *args):
        self.test_context._name = 'foo'
        self.test_context._task_id = '1234567890'
        self.test_context.template_file = '/bar/baz/some-heat-file'
        self.test_context.heat_parameters = {'image': 'cirros'}
        self.test_context.get_neutron_info = mock.MagicMock()
        self.test_context._flags.no_setup = True
        self.test_context.deploy()

        mock_create_new_stack.assert_not_called()
        mock_retrieve_existing_stack.assert_called_with(self.test_context.name)
        self.assertIsNotNone(self.test_context.stack)
        key_filename = ''.join(
            [consts.YARDSTICK_ROOT_PATH,
             'yardstick/resources/files/yardstick_key-',
             self.test_context._name])
        mock_genkeys.assert_called_once_with(key_filename)
        # RAH: test
        if len(mock_path_exists.call_args_list) > 1:
            print(mock_path_exists.call_args_list)
            raise Exception(mock_path_exists.call_args_list)
        mock_path_exists.assert_called_once_with(key_filename)

    @mock.patch.object(heat, 'HeatTemplate')
    @mock.patch.object(os.path, 'exists', return_value=False)
    @mock.patch.object(ssh.SSH, 'gen_keys')
    @mock.patch.object(heat.HeatContext, '_create_new_stack')
    @mock.patch.object(heat.HeatContext, '_retrieve_existing_stack',
                       return_value=None)
    def test_deploy_try_retrieve_context_does_not_exist(self,
            mock_retrieve_stack, mock_create_new_stack, mock_genkeys,
            mock_path_exists, *args):
        self.test_context._name = 'demo'
        self.test_context._task_id = '1234567890'
        self.test_context._flags.no_setup = True
        self.test_context.template_file = '/bar/baz/some-heat-file'
        self.test_context.get_neutron_info = mock.MagicMock()

        self.test_context.deploy()

        mock_retrieve_stack.assert_called_once_with(self.test_context._name)
        mock_create_new_stack.assert_called()
        key_filename = ''.join(
            [consts.YARDSTICK_ROOT_PATH,
             'yardstick/resources/files/yardstick_key-',
             self.test_context._name])
        mock_genkeys.assert_called_once_with(key_filename)
        # RAH: test
        if len(mock_path_exists.call_args_list) > 1:
            print(mock_path_exists.call_args_list)
            raise Exception(mock_path_exists.call_args_list)
        mock_path_exists.assert_any_call(key_filename)

    @mock.patch.object(heat, 'HeatTemplate', return_value='heat_template')
    @mock.patch.object(heat.HeatContext, '_add_resources_to_template')
    @mock.patch.object(os.path, 'exists', return_value=False)
    @mock.patch.object(ssh.SSH, 'gen_keys')
    def test_deploy_ssh_key_before_adding_resources(self, mock_genkeys,
            mock_path_exists, mock_add_resources, *args):
        mock_manager = mock.Mock()
        mock_manager.attach_mock(mock_add_resources,
                                 '_add_resources_to_template')
        mock_manager.attach_mock(mock_genkeys, 'gen_keys')
        mock_manager.reset_mock()
        self.test_context._name_task_id = 'demo-12345678'
        self.test_context.get_neutron_info = mock.Mock()
        with mock.patch.object(self.test_context, '_create_new_stack') as \
                mock_create_stack, \
                mock.patch.object(self.test_context, 'get_neutron_info') as \
                mock_neutron_info:
            self.test_context.deploy()

        mock_neutron_info.assert_called_once()
        mock_create_stack.assert_called_once()
        key_filename = ''.join(
            [consts.YARDSTICK_ROOT_PATH,
             'yardstick/resources/files/yardstick_key-',
             self.test_context._name_task_id])
        mock_genkeys.assert_called_once_with(key_filename)
        # RAH: test
        if len(mock_path_exists.call_args_list) > 1:
            print(mock_path_exists.call_args_list)
            raise Exception(mock_path_exists.call_args_list)
        mock_path_exists.assert_called_with(key_filename)

        mock_call_gen_keys = mock.call.gen_keys(key_filename)
        mock_call_add_resources = (
            mock.call._add_resources_to_template('heat_template'))
        self.assertTrue(mock_manager.mock_calls.index(mock_call_gen_keys) <
                        mock_manager.mock_calls.index(mock_call_add_resources))

    def test_check_for_context(self):
        pass
        # check that the context exists

    def test_add_server_port(self):
        network1 = mock.MagicMock()
        network2 = mock.MagicMock()
        self.test_context._name = 'foo'
        self.test_context._task_id = '1234567890'
        self.test_context._name_task_id = '{}-{}'.format(
            self.test_context._name, self.test_context._task_id[:8])
        self.test_context.stack = mock.MagicMock()
        self.test_context.networks = {
            'a': network1,
            'c': network2,
        }
        self.test_context.stack.outputs = {
            u'b': u'10.20.30.45',
            u'b-subnet_id': 1,
            u'foo-12345678-a-subnet-cidr': u'10.20.0.0/15',
            u'foo-12345678-a-subnet-gateway_ip': u'10.20.30.1',
            u'b-mac_address': u'00:01',
            u'b-device_id': u'dev21',
            u'b-network_id': u'net789',
            u'd': u'40.30.20.15',
            u'd-subnet_id': 2,
            u'foo-12345678-c-subnet-cidr': u'40.30.0.0/18',
            u'foo-12345678-c-subnet-gateway_ip': u'40.30.20.254',
            u'd-mac_address': u'00:10',
            u'd-device_id': u'dev43',
            u'd-network_id': u'net987',
            u'e': u'40.30.20.15',
            u'e-subnet_id': 2,
            u'e-mac_address': u'00:10',
            u'e-device_id': u'dev43',
            u'e-network_id': u'net987',
        }
        server = mock.MagicMock()
        server.private_ip = None
        server.ports = OrderedDict([
            ('a', [{'stack_name': 'b', 'port': 'port_a'}]),
            ('c', [{'stack_name': 'd', 'port': 'port_c'},
                   {'stack_name': 'e', 'port': 'port_f'}]),
        ])

        expected = {
            "private_ip": '10.20.30.45',
            "subnet_id": 1,
            "subnet_cidr": '10.20.0.0/15',
            "network": '10.20.0.0',
            "netmask": '255.254.0.0',
            "name": "port_a",
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
        self.assertEqual(len(server.interfaces), 3)
        self.assertDictEqual(server.interfaces['port_a'], expected)

    @mock.patch('yardstick.benchmark.contexts.heat.os')
    @mock.patch.object(heat.HeatContext, '_delete_key_file')
    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_undeploy(self, mock_template, mock_delete_key, *args):
        self.test_context.stack = mock_template
        self.test_context._name = 'foo'
        self.test_context._task_id = '1234567890'
        self.test_context._name_task_id = '{}-{}'.format(
            self.test_context._name, self.test_context._task_id[:8])
        # mock_os.path.exists.return_value = True
        self.test_context.key_filename = 'foo/bar/foobar'
        self.test_context.undeploy()
        mock_delete_key.assert_called()
        mock_template.delete.assert_called_once()

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_undeploy_no_teardown(self, mock_template):
        self.test_context.stack = mock_template
        self.test_context._name = 'foo'
        self.test_context._task_id = '1234567890'
        self.test_context._flags.no_teardown = True
        self.test_context.undeploy()

        mock_template.delete.assert_not_called()

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    @mock.patch('yardstick.benchmark.contexts.heat.os')
    def test_undeploy_key_filename(self, mock_os, mock_template):
        self.test_context.stack = mock_template
        self.test_context._name = 'foo'
        self.test_context._task_id = '1234567890'
        self.test_context._name_task_id = '{}-{}'.format(
            self.test_context._name, self.test_context._task_id)
        mock_os.path.exists.return_value = True
        self.test_context.key_filename = 'foo/bar/foobar'
        self.assertIsNone(self.test_context.undeploy())

    @mock.patch("yardstick.benchmark.contexts.heat.pkg_resources")
    def test__get_server_found_dict(self, *args):
        """
        Use HeatContext._get_server to get a server that matches
        based on a dictionary input.
        """
        foo2_server = mock.Mock()
        foo2_server.key_filename = None
        foo2_server.private_ip = '10.0.0.2'
        foo2_server.public_ip = '127.0.0.2'
        foo2_server.context.user = 'oof'

        baz3_server = mock.Mock()
        baz3_server.key_filename = None
        baz3_server.private_ip = '10.0.0.3'
        baz3_server.public_ip = '127.0.0.3'
        baz3_server.context.user = 'zab'

        self.test_context._name = 'bar'
        self.test_context._task_id = '1234567890'
        self.test_context._name_task_id = '{}-{}'.format(
            self.test_context._name, self.test_context._task_id[:8])
        self.test_context._user = 'bot'
        self.test_context.stack = mock.Mock()
        self.test_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.test_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
        }

        attr_name = {
            'name': 'foo.bar-12345678',
            'private_ip_attr': 'private_ip',
            'public_ip_attr': 'public_ip',
        }
        self.test_context.key_uuid = 'foo-42'
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result['user'], 'bot')
        self.assertEqual(result['ip'], '127.0.0.1')
        self.assertEqual(result['private_ip'], '10.0.0.1')

    @mock.patch("yardstick.benchmark.contexts.heat.pkg_resources")
    def test__get_server_found_dict_no_attrs(self, *args):
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

        self.test_context._name = 'bar'
        self.test_context._task_id = '1234567890'
        self.test_context._name_task_id = '{}-{}'.format(
            self.test_context._name, self.test_context._task_id[:8])
        self.test_context._user = 'bot'
        self.test_context.stack = mock.Mock()
        self.test_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.test_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
        }

        attr_name = {
            'name': 'foo.bar-12345678',
        }

        self.test_context.key_uuid = 'foo-42'
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result['user'], 'bot')
        # no private ip attr mapping in the map results in None value in the result
        self.assertIsNone(result['private_ip'])
        # no public ip attr mapping in the map results in no value in the result
        self.assertNotIn('ip', result)

    @mock.patch("yardstick.benchmark.contexts.heat.pkg_resources")
    def test__get_server_found_not_dict(self, *args):
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

        self.test_context._name = 'bar1'
        self.test_context._task_id = '1234567890'
        self.test_context._name_task_id = 'bar1-12345678'
        self.test_context.stack = mock.Mock()
        self.test_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.test_context.generate_routing_table = mock.MagicMock(return_value=[])

        self.test_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
        }

        attr_name = 'baz3'
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result['user'], 'zab')
        self.assertEqual(result['private_ip'], '10.0.0.3')
        # no public_ip on the server results in no value in the result
        self.assertNotIn('public_ip', result)

    @mock.patch("yardstick.benchmark.contexts.heat.pkg_resources")
    def test__get_server_none_found_not_dict(self, *args):
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

        self.test_context._name = 'bar1'
        self.test_context.stack = mock.Mock()
        self.test_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.test_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
            'wow4': None,
        }

        self.test_context.key_uuid = 'foo-42'
        attr_name = 'wow4'
        result = self.test_context._get_server(attr_name)
        self.assertIsNone(result)

    @mock.patch("yardstick.benchmark.contexts.heat.pkg_resources")
    def test__get_server_not_found_dict(self, *args):
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

        self.test_context._name = 'bar1'
        self.test_context._task_id = '1235467890'
        self.test_context._name_task_id = '{}-{}'.format(
            self.test_context._name, self.test_context._task_id[:8])
        self.test_context.stack = mock.Mock()
        self.test_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.test_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
        }

        self.test_context.key_uuid = 'foo-42'
        attr_name = {
            'name': 'foo.wow4',
            'private_ip_attr': 'private_ip',
            'public_ip_attr': 'public_ip',
        }
        result = self.test_context._get_server(attr_name)
        self.assertIsNone(result)

    @mock.patch("yardstick.benchmark.contexts.heat.pkg_resources")
    def test__get_server_not_found_not_dict(self, *args):
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

        self.mock_context._name = 'bar1'
        self.test_context.stack = mock.Mock()
        self.mock_context.stack.outputs = {
            'private_ip': '10.0.0.1',
            'public_ip': '127.0.0.1',
        }
        self.mock_context._server_map = {
            'baz3': baz3_server,
            'foo2': foo2_server,
        }

        self.test_context.key_uuid = 'foo-42'
        attr_name = 'foo.wow4'
        result = self.test_context._get_server(attr_name)
        self.assertIsNone(result)

    # TODO: Split this into more granular tests
    def test__get_network(self):
        network1 = mock.MagicMock()
        network1.name = 'net_1'
        network1.vld_id = 'vld111'
        network1.segmentation_id = 'seg54'
        network1.network_type = 'type_a'
        network1.physical_network = 'phys'

        network2 = mock.MagicMock()
        network2.name = 'net_2'
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

        attr_name = {'network_type': 'nosuch'}
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = 'vld777'
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = {'segmentation_id': 'seg45'}
        expected = {
            "name": 'net_2',
            "segmentation_id": 'seg45',
            "network_type": 'type_b',
            "physical_network": 'virt',
        }
        result = self.test_context._get_network(attr_name)
        self.assertDictEqual(result, expected)

        attr_name = 'a'
        expected = {
            "name": 'net_1',
            "segmentation_id": 'seg54',
            "network_type": 'type_a',
            "physical_network": 'phys',
        }
        result = self.test_context._get_network(attr_name)
        self.assertDictEqual(result, expected)
