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

import copy
import unittest
import uuid

from yardstick.network_services.vnf_generic.vnf import epc_vnf

NAME = 'vnf__0'

VNFD = {
    'vnfd:vnfd-catalog': {
        'vnfd': [{
            'id': 'EPCVnf',  # NSB python class mapping
            'name': 'EPCVnf',
            'short-name': 'EPCVnf',
            'description': 'EPCVnf',
            'mgmt-interface': {
                'vdu-id': 'vepcvnf-baremetal',
                'user': 'user',  # Value filled by vnfdgen
                'password': 'password',  # Value filled by vnfdgen
                'ip': 'ip'  # Value filled by vnfdgen
            },
            'vdu': [{
                'id': 'vepcvnf-baremetal',
                'name': 'vepc-vnf-baremetal',
                'description': 'vEPCVnf workload',
                'external-interface': []}],
            'benchmark': {
                'kpi': []}}]}}


class TestEPCVnf(unittest.TestCase):

    def setUp(self):
        self._id = uuid.uuid1().int
        self.vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.epc_vnf = epc_vnf.EPCVnf(NAME, self.vnfd, self._id)

    def test___init__(self, *args):
        _epc_vnf = epc_vnf.EPCVnf(NAME, self.vnfd, self._id)
        for x in {'user', 'password', 'ip'}:
            self.assertEqual(self.vnfd['mgmt-interface'][x],
                             _epc_vnf.vnfd_helper.mgmt_interface[x])
        self.assertEqual(NAME, _epc_vnf.name)
        self.assertEqual([], _epc_vnf.kpi)
        self.assertEqual({}, _epc_vnf.config)
        self.assertFalse(_epc_vnf.runs_traffic)

    def test___init__missing_ip(self, *args):
        _vnfd = copy.deepcopy(self.vnfd)
        _vnfd['mgmt-interface'].pop('ip')
        _epc_vnf = epc_vnf.EPCVnf(NAME, _vnfd, self._id)
        for x in {'user', 'password'}:
            self.assertEqual(_vnfd['mgmt-interface'][x],
                             _epc_vnf.vnfd_helper.mgmt_interface[x])
        self.assertNotIn('ip', _epc_vnf.vnfd_helper.mgmt_interface)
        self.assertEqual(NAME, _epc_vnf.name)
        self.assertEqual([], _epc_vnf.kpi)
        self.assertEqual({}, _epc_vnf.config)
        self.assertFalse(_epc_vnf.runs_traffic)

    def test_instantiate(self):
        self.assertIsNone(self.epc_vnf.instantiate({}, {}))

    def test_wait_for_instantiate(self):
        self.assertIsNone(self.epc_vnf.wait_for_instantiate())

    def test_terminate(self):
        self.assertIsNone(self.epc_vnf.terminate())

    def test_scale(self):
        self.assertIsNone(self.epc_vnf.scale())

    def test_collect_kpi(self):
        self.assertIsNone(self.epc_vnf.collect_kpi())

    def test_start_collect(self):
        self.assertIsNone(self.epc_vnf.start_collect())

    def test_stop_collect(self):
        self.assertIsNone(self.epc_vnf.stop_collect())
