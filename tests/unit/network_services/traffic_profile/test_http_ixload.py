# Copyright (c) 2017 Intel Corporation
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


from __future__ import absolute_import
import unittest

from oslo_serialization import jsonutils

from yardstick.network_services.traffic_profile import http_ixload


class TestIxLoadTrafficGen(unittest.TestCase):

    def test_parse_run_test(self):
        ports = [1, 2, 3]
        testinput = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(testinput)
        ixload = http_ixload.IXLOADHttpTest(j)
        self.assertEqual(testinput, ixload.testinput)
        self.assertEqual(ixload.ports_to_reassign, [
            ["IXIA_CHASSIS", "CARD", 1],
            ["IXIA_CHASSIS", "CARD", 2],
            ["IXIA_CHASSIS", "CARD", 3],
        ])

    def test_get_ports_reassing(self):
        ports = [
            ["IXIA_CHASSIS", "CARD", 1],
            ["IXIA_CHASSIS", "CARD", 2],
            ["IXIA_CHASSIS", "CARD", 3],
        ]
        formatted = http_ixload.IXLOADHttpTest.get_ports_reassign(ports)
        self.assertEqual(formatted, [
            "IXIA_CHASSIS;CARD;1",
            "IXIA_CHASSIS;CARD;2",
            "IXIA_CHASSIS;CARD;3",
        ])
