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

from yardstick.network_services.libs.ixia_libs.IxNet.load import \
    IxLoad


class TestIxLoad(unittest.TestCase):
    def test__clear_ixia_config(self):
        ixnet_gen = IxLoad()

        ixnet = mock.MagicMock()
        ixnet.execute = mock.Mock()
        result = ixnet_gen._clear_ixia_config(ixnet)
        self.assertIsNone(result)

    def test__load_ixia_profile(self):
        ixnet_gen = IxLoad()

        ixnet = mock.MagicMock()
        ixnet.execute = mock.Mock()
        result = ixnet_gen._load_ixia_profile(ixnet, {})
        self.assertIsNone(result)

    def test_load_ixia_config(self):
        ixnet_gen = IxLoad()

        ixNet = mock.MagicMock()
        ixnet_gen._clear_ixia_config = mock.Mock()
        ixnet_gen._load_ixia_profile = mock.Mock()
        result = ixnet_gen.load_ixia_config(ixNet, {})
        self.assertIsNone(result)
