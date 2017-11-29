#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# yardstick: this file is copied from python-heatclient and slightly modified

from __future__ import absolute_import
import unittest

from yardstick.common import yaml_loader


class TemplateFormatTestCase(unittest.TestCase):

    def test_parse_to_value_exception(self):

        self.assertEquals(yaml_loader.yaml_load("string"), u"string")


def main():
    unittest.main()

if __name__ == '__main__':
    main()
