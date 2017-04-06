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

from yardstick.network_services.libs.ixia_libs.IxNet.IxNet \
    import IxNextgen


class TestIxNextgen(unittest.TestCase):
    def test___init__(self):
        ixnet_gen = IxNextgen()
        self.assertEqual(ixnet_gen._bidir, None)

    def test_is_ipv4orv6(self):
        ixnet_gen = IxNextgen()
        self.assertEqual(1, ixnet_gen.is_ipv4orv6(u"10.12.121.10"))

    def test_is_ipv4orv6_error(self):
        ixnet_gen = IxNextgen()
        self.assertEqual(0, ixnet_gen.is_ipv4orv6(u"1.1.1"))

    def test_is_ipv4orv6_v6(self):
        ixnet_gen = IxNextgen()
        self.assertEqual(
            2, ixnet_gen.is_ipv4orv6(u"0064:ff9b:0:0:0:0:9810:6414"))

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.IxConfig")
    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.sys")
    def test_connect(self, mock_IxConfig, mock_sys):
        ixnet_gen = IxNextgen()
        ixnet_gen.get_ixnet = mock.MagicMock()
        ixnet_gen.get_ixnet.connect = mock.Mock()
        result = ixnet_gen._connect({"py_lib_path": "/tmp"})
        self.assertIsNotNone(result)

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.IxLoad")
    def test_ix_load_config(self, IxLoad):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        self.assertEqual(None, ixnet_gen.ix_load_config({}))

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.IxPorts")
    def test_ix_assign_ports(self, IxLoad):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        self.assertEqual(None, ixnet_gen.ix_assign_ports())

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.IxFrame")
    def test_ix_update_frame(self, IxLoad):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        self.assertEqual(None, ixnet_gen.ix_update_frame({}))

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.IxEther")
    def test_ix_update_ether(self, IxLoad):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        self.assertEqual(None, ixnet_gen.ix_update_ether({}))

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.IxIPv4")
    def test_ix_update_ipv4(self, IxLoad):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        ixnet_gen.is_ipv4orv6 = mock.Mock(return_value=1)
        params = {'public': {'outer_l3': {'srcip4': "1.1.1.1"}}}
        self.assertEqual(None, ixnet_gen.ix_update_ipv4(params))

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.IxIPv6")
    def test_ix_update_ipv6(self, IxLoad):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        ixnet_gen.is_ipv4orv6 = mock.Mock(return_value=2)
        params = {'public': {'outer_l3': {'srcip4':
                                          "0064:ff9b:0:0:0:0:9810:6414"}}}
        self.assertEqual(None, ixnet_gen.ix_update_ipv4(params))

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.Ixudp")
    def test_ix_update_udp(self, Ixudp):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        self.assertEqual(None, ixnet_gen.ix_update_udp({}))

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.Ixtcp")
    def test_ix_update_tcp(self, Ixtcp):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        self.assertEqual(None, ixnet_gen.ix_update_tcp({}))

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.IxStart")
    def test_ix_start_traffic(self, IxStart):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        self.assertEqual(None, ixnet_gen.ix_start_traffic())

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.IxStop")
    def test_ix_stop_traffic(self, IxStop):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        self.assertEqual(None, ixnet_gen.ix_stop_traffic())

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.IxStats")
    def test_ix_get_statistics(self, IxStats):
        ixnet_gen = IxNextgen()
        ixnet_gen.ixNet = mock.Mock()
        self.assertIsNotNone(ixnet_gen.ix_get_statistics())
