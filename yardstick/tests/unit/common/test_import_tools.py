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

import unittest

from yardstick.common import exceptions as y_exc
from yardstick.common import import_tools


@import_tools.decorator_banned_modules
class DummyClass(object):
    pass


class DecoratorBannedModule(unittest.TestCase):

    MODULE = 'yardstick.tests.unit.common.banned_modules.banned_module'

    def test_passt(self):
        self.assertIsNotNone(DummyClass())

    def test_banned_module(self):
        import_tools.BANNED_MODULES[self.MODULE] = 'Banned module!!'
        from yardstick.tests.unit.common.banned_modules import importing_module
        self.addCleanup(self._remove_module)

        with self.assertRaises(y_exc.YardstickBannedModuleImported) as exc:
            importing_module.ImportingClass()

        msg = ('Module "%s" cannnot be imported. Reason: "Banned module!!"'
               % self.MODULE)
        self.assertEqual(msg, str(exc.exception))

    def _remove_module(self):
        del import_tools.BANNED_MODULES[self.MODULE]
