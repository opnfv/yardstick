# Copyright (c) 2015 Intel Research and Development Ireland Ltd.
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
from experimental_framework.packet_generators import base_packet_generator


class BasePacketGeneratorTest(unittest.TestCase):

    def setUp(self):
        self.mut = base_packet_generator.BasePacketGenerator()
        pass

    def tearDown(self):
        pass

    def test_send_traffic_for_failure(self):
        self.assertRaises(NotImplementedError, self.mut.send_traffic)
