#!/usr/bin/env python

# Copyright (c) 2016-2017 Intel Corporation
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
#

# Unittest for yardstick.network_services.libs.ixia_libs.IxNet

from __future__ import absolute_import
import unittest
import mock

from yardstick.network_services.libs.ixia_libs.IxNet.stop import \
    IxStop


class TestIxStop(unittest.TestCase):
    def test__stop_traffic(self):
        ixnet_gen = IxStop()

        ixnet = mock.MagicMock()
        ixnet.execute = mock.Mock()
        ixnet.commit = mock.Mock()
        ixnet.getList = mock.Mock(return_value=[0])
        result = ixnet_gen._stop_traffic(ixnet)
        self.assertIsNone(result)
