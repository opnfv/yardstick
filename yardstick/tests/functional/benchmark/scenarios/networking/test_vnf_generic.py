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
import sys

import mock
import unittest
import yaml

from yardstick import tests as y_tests
from yardstick.common import utils


with mock.patch.dict(sys.modules, y_tests.STL_MOCKS):
    from yardstick.benchmark.scenarios.networking import vnf_generic


TRAFFIC_PROFILE_1 = """
schema: nsb:traffic_profile:0.1
name: rfc2544
description: Traffic profile to run RFC2544 latency
traffic_profile:
  traffic_type : RFC2544Profile
  frame_rate : 100
uplink_0:
  ipv4:
    id: 1
    outer_l2:
      framesize:
        64B: "{{get(imix, 'imix.uplink.64B', '0') }}"
        128B: "{{get(imix, 'imix.uplink.128B', '0') }}"
"""

TRAFFIC_PROFILE_2 = """
{% set vports = get(extra_args, 'vports', 1) %}
traffic_profile:
  traffic_type : RFC2544Profile
{% for vport in range(vports|int) %}
uplink_{{vport}}:
  ipv4: 192.168.0.{{vport}}
{% endfor %}
"""

class VnfGenericTestCase(unittest.TestCase):

    def setUp(self):
        scenario_cfg = {'topology': 'fake_topology',
                        'task_path': 'fake_path',
                        'traffic_profile': 'fake_fprofile_path'}
        context_cfg = {}
        topology_yaml = {'nsd:nsd-catalog': {'nsd': [mock.Mock()]}}
        with mock.patch.object(yaml, 'load', return_value=topology_yaml), \
                mock.patch.object(utils, 'open_relative_file'):
            self.ns_testcase = vnf_generic.NetworkServiceTestCase(scenario_cfg,
                                                                  context_cfg)
        self.ns_testcase._get_traffic_profile = mock.Mock()

    def test__fill_traffic_profile_no_args(self):
        traffic_profile = copy.deepcopy(TRAFFIC_PROFILE_1)
        self.ns_testcase._get_traffic_profile.return_value = traffic_profile

        self.ns_testcase._fill_traffic_profile()
        config = self.ns_testcase.traffic_profile.params
        self.assertEqual('nsb:traffic_profile:0.1', config['schema'])
        self.assertEqual('rfc2544', config['name'])
        self.assertEqual('Traffic profile to run RFC2544 latency',
                         config['description'])
        t_profile = {'traffic_type': 'RFC2544Profile',
                     'frame_rate': 100}
        self.assertEqual(t_profile, config['traffic_profile'])
        uplink_0 = {
            'ipv4': {'id': 1,
                     'outer_l2': {'framesize': {'128B': '0', '64B': '0'}}
                     }
        }
        self.assertEqual(uplink_0, config['uplink_0'])

    def test__fill_traffic_profile_with_args(self):
        traffic_profile = copy.deepcopy(TRAFFIC_PROFILE_2)
        self.ns_testcase._get_traffic_profile.return_value = traffic_profile
        self.ns_testcase.scenario_cfg['extra_args'] = {'vports': 3}

        self.ns_testcase._fill_traffic_profile()
        config = self.ns_testcase.traffic_profile.params
        self.assertEqual({'ipv4': '192.168.0.0'}, config['uplink_0'])
        self.assertEqual({'ipv4': '192.168.0.1'}, config['uplink_1'])
        self.assertEqual({'ipv4': '192.168.0.2'}, config['uplink_2'])
        self.assertNotIn('uplink_3', config)

    def test__fill_traffic_profile_incorrect_args(self):
        traffic_profile = copy.deepcopy(TRAFFIC_PROFILE_2)
        self.ns_testcase._get_traffic_profile.return_value = traffic_profile
        self.ns_testcase.scenario_cfg['extra_args'] = {'incorrect_vports': 3}

        self.ns_testcase._fill_traffic_profile()
        config = self.ns_testcase.traffic_profile.params
        self.assertEqual({'ipv4': '192.168.0.0'}, config['uplink_0'])
        self.assertNotIn('uplink_1', config)
