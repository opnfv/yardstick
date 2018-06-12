# Copyright 2018 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from yardstick.common import exceptions
from yardstick.tests.unit import base as ut_base


class ErrorClassTestCase(ut_base.BaseUnitTestCase):

    def test_init(self):
        with self.assertRaises(RuntimeError):
            exceptions.ErrorClass()

    def test_getattr(self):
        error_instance = exceptions.ErrorClass(test='')
        with self.assertRaises(AttributeError):
            error_instance.get_name()
