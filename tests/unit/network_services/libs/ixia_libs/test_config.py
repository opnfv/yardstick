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

from yardstick.network_services.libs.ixia_libs.IxNet.config import \
    IxConfig


class TestIxConfig(unittest.TestCase):
    def test__get_config(self):
        ixnet_gen = IxConfig()
        tg_cfg = {}
        tg_cfg.update({"vdu": [{"external-interface":
                                [{"virtual-interface":
                                  {"vpci": "0000:07:00.1"}},
                                 {"virtual-interface":
                                  {"vpci": "0000:07:00.1"}}]}]})
        tg_cfg.update({"mgmt-interface": {"ip": "test"}})
        tg_cfg["mgmt-interface"].update({"tg-config": {"dut_result_dir":
                                                       "test"}})
        tg_cfg["mgmt-interface"]["tg-config"].update({"version": "test"})
        tg_cfg["mgmt-interface"]["tg-config"].update({"ixchassis": "test"})
        tg_cfg["mgmt-interface"]["tg-config"].update({"tcl_port": "test"})
        tg_cfg["mgmt-interface"]["tg-config"].update({"py_lib_path": "test"})

        result = ixnet_gen._get_config(tg_cfg)
        self.assertIsNotNone(result)
