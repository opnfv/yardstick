# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import errno

import mock

from yardstick.benchmark.contexts import base
from yardstick.benchmark.contexts.base import Context
from yardstick.common import yaml_loader
from yardstick.tests.unit import base as ut_base
from yardstick.common.constants import YARDSTICK_ROOT_PATH


class DummyContextClass(Context):

    __context_type__ = "Dummy"

    def __init__(self, host_name_separator='.'):
        super(DummyContextClass, self).__init__\
            (host_name_separator=host_name_separator)
        self.nodes = []
        self.controllers = []
        self.computes = []
        self.baremetals = []

    def _get_network(self, *args):
        pass

    def _get_server(self, *args):
        pass

    def deploy(self):
        pass

    def undeploy(self):
        pass

    def _get_physical_nodes(self):
        pass

    def _get_physical_node_for_server(self, server_name):
        pass


class FlagsTestCase(ut_base.BaseUnitTestCase):

    def setUp(self):
        self.flags = base.Flags()

    def test___init__(self):
        self.assertFalse(self.flags.no_setup)
        self.assertFalse(self.flags.no_teardown)
        self.assertEqual({'verify': False}, self.flags.os_cloud_config)

    def test___init__with_flags(self):
        flags = base.Flags(no_setup=True)
        self.assertTrue(flags.no_setup)
        self.assertFalse(flags.no_teardown)

    def test_parse(self):
        self.flags.parse(no_setup=True, no_teardown='False',
                         os_cloud_config={'verify': True})

        self.assertTrue(self.flags.no_setup)
        self.assertEqual('False', self.flags.no_teardown)
        self.assertEqual({'verify': True}, self.flags.os_cloud_config)

    def test_parse_forbidden_flags(self):
        self.flags.parse(foo=42)
        with self.assertRaises(AttributeError):
            _ = self.flags.foo


class ContextTestCase(ut_base.BaseUnitTestCase):

    @staticmethod
    def _remove_ctx(ctx_obj):
        if ctx_obj in base.Context.list:
            base.Context.list.remove(ctx_obj)

    def test_split_host_name(self):
        ctx_obj = DummyContextClass()
        self.addCleanup(self._remove_ctx, ctx_obj)
        config_name = 'host_name.ctx_name'
        self.assertEqual(('host_name', 'ctx_name'),
                         ctx_obj.split_host_name(config_name))

    def test_split_host_name_wrong_separator(self):
        ctx_obj = DummyContextClass()
        self.addCleanup(self._remove_ctx, ctx_obj)
        config_name = 'host_name-ctx_name'
        self.assertEqual((None, None),
                         ctx_obj.split_host_name(config_name))

    def test_split_host_name_other_separator(self):
        ctx_obj = DummyContextClass(host_name_separator='-')
        self.addCleanup(self._remove_ctx, ctx_obj)
        config_name = 'host_name-ctx_name'
        self.assertEqual(('host_name', 'ctx_name'),
                         ctx_obj.split_host_name(config_name))

    def test_get_physical_nodes(self):
        ctx_obj = DummyContextClass()
        self.addCleanup(self._remove_ctx, ctx_obj)

        result = Context.get_physical_nodes()

        self.assertEqual(result, {None: None})

    @mock.patch.object(Context, 'get_context_from_server')
    def test_get_physical_node_from_server(self, mock_get_ctx):
        ctx_obj = DummyContextClass()
        self.addCleanup(self._remove_ctx, ctx_obj)

        mock_get_ctx.return_value = ctx_obj

        result = Context.get_physical_node_from_server("mock_server")

        mock_get_ctx.assert_called_once()
        self.assertIsNone(result)

    @mock.patch.object(yaml_loader, 'read_yaml_file')
    def test_read_pod_file(self, mock_read_yaml_file):
        attrs = {'name': 'foo',
                 'task_id': '12345678',
                 'file': 'pod.yaml'
                 }

        ctx_obj = DummyContextClass()
        cfg = {"nodes": [
                    {
                        "name": "node1",
                        "role": "Controller",
                        "ip": "10.229.47.137",
                        "user": "root",
                        "key_filename": "/root/.yardstick_key"
                    },
                    {
                        "name": "node2",
                        "role": "Compute",
                        "ip": "10.229.47.139",
                        "user": "root",
                        "key_filename": "/root/.yardstick_key"
                    }
                ]
            }

        mock_read_yaml_file.return_value = cfg
        result = ctx_obj.read_pod_file(attrs)
        self.assertEqual(result, cfg)

        mock_read_yaml_file.side_effect = IOError(errno.EPERM, '')
        with self.assertRaises(IOError):
            ctx_obj.read_pod_file(attrs)

        mock_read_yaml_file.side_effect = IOError(errno.ENOENT, '')
        with self.assertRaises(IOError):
            ctx_obj.read_pod_file(attrs)

        file_path = os.path.join(YARDSTICK_ROOT_PATH, 'pod.yaml')
        self.assertEqual(ctx_obj.file_path, file_path)
