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
import uuid

from yardstick.network_services.vnf_generic.vnf import agnostic_vnf

NAME = 'vnf__0'

VNFD = {
    'vnfd:vnfd-catalog': {
        'vnfd': [{
            'id': 'AgnosticVnf',  # NSB python class mapping
            'name': 'AgnosticVnf',
            'short-name': 'AgnosticVnf',
            'description': 'AgnosticVnf',
            'mgmt-interface': {
                'vdu-id': 'vepcvnf-baremetal',
                'user': 'user',  # Value filled by vnfdgen
                'password': 'password',  # Value filled by vnfdgen
                'ip': 'ip'  # Value filled by vnfdgen
            },
            'vdu': [{
                'id': 'vepcvnf-baremetal',
                'name': 'vepc-vnf-baremetal',
                'description': 'vAgnosticVnf workload',
                'external-interface': []}],
            'benchmark': {
                'kpi': []}}]}}


class TestAgnosticVnf(unittest.TestCase):

    def setUp(self):
        self._id = uuid.uuid1().int
        self.vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.agnostic_vnf = agnostic_vnf.AgnosticVnf(NAME, self.vnfd, self._id)

    def test_instantiate(self):
        self.assertIsNone(self.agnostic_vnf.instantiate({}, {}))

    def test_wait_for_instantiate(self):
        self.assertIsNone(self.agnostic_vnf.wait_for_instantiate())

    def test_terminate(self):
        self.assertIsNone(self.agnostic_vnf.terminate())

    def test_scale(self):
        self.assertIsNone(self.agnostic_vnf.scale())

    def test_collect_kpi(self):
        self.assertIsNone(self.agnostic_vnf.collect_kpi())

    def test_start_collect(self):
        self.assertIsNone(self.agnostic_vnf.start_collect())

    def test_stop_collect(self):
        self.assertIsNone(self.agnostic_vnf.stop_collect())
