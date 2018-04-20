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

from yardstick.common import exceptions
from yardstick.common.messaging import payloads
from yardstick.tests.unit import base as ut_base


class _DummyPayload(payloads.Payload):
    REQUIRED_FIELDS = {'version', 'key1', 'key2'}


class PayloadTestCase(ut_base.BaseUnitTestCase):

    def test__init(self):
        payload = _DummyPayload(version=1, key1='value1', key2='value2')
        self.assertEqual(1, payload.version)
        self.assertEqual('value1', payload.key1)
        self.assertEqual('value2', payload.key2)
        self.assertEqual(3, len(payload._fields))

    def test__init_missing_required_fields(self):
        with self.assertRaises(exceptions.PayloadMissingAttributes):
            _DummyPayload(key1='value1', key2='value2')

    def test_obj_to_dict(self):
        payload = _DummyPayload(version=1, key1='value1', key2='value2')
        payload_dict = payload.obj_to_dict()
        self.assertEqual({'version': 1, 'key1': 'value1', 'key2': 'value2'},
                         payload_dict)

    def test_dict_to_obj(self):
        _dict = {'version': 2, 'key1': 'value100', 'key2': 'value200'}
        payload = _DummyPayload.dict_to_obj(_dict)
        self.assertEqual(set(_dict.keys()), payload._fields)


class TrafficGeneratorPayloadTestCase(ut_base.BaseUnitTestCase):

    def test_init(self):
        tg_payload = payloads.TrafficGeneratorPayload(
            version=1, iteration=10, kpid={'key1': 'value1'})
        self.assertEqual(1, tg_payload.version)
        self.assertEqual(10, tg_payload.iteration)
        self.assertEqual({'key1': 'value1'}, tg_payload.kpi)
        self.assertEqual(3, len(tg_payload._fields))

    def test__init_missing_required_fields(self):
        with self.assertRaises(exceptions.PayloadMissingAttributes):
            payloads.TrafficGeneratorPayload(version=1, iteration=10)
        with self.assertRaises(exceptions.PayloadMissingAttributes):
            payloads.TrafficGeneratorPayload(iteration=10, kpi={})
        with self.assertRaises(exceptions.PayloadMissingAttributes):
            payloads.TrafficGeneratorPayload(iteration=10)
