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

from yardstick.benchmark.contexts import base
from yardstick.tests.unit import base as ut_base


class DummyContextClass(base.Context):

    def _get_network(self, *args):
        pass

    def _get_server(self, *args):
        pass

    def deploy(self):
        pass

    def undeploy(self):
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
