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

from six.moves import range
import unittest

from yardstick.common.yaml_loader import yaml_load
from yardstick.network_services.vnf_generic import vnfdgen


UPLINK = "uplink"
DOWNLINK = "downlink"

TREX_VNFD_TEMPLATE = """
vnfd:vnfd-catalog:
    vnfd:
    -   id: TrexTrafficGen  # ISB class mapping
        name: trexgen
        short-name: trexgen
        description: TRex stateless traffic generator for RFC2544
        mgmt-interface:
            vdu-id: trexgen-baremetal
            user: {{user}}  # Value filled by vnfdgen
            password: {{password}}  # Value filled by vnfdgen
            ip: {{ip}}  # Value filled by vnfdgen
        connection-point:
        -   name: xe0
            type: VPORT
        -   name: xe1
            type: VPORT
        vdu:
        -   id: trexgen-baremetal
            name: trexgen-baremetal
            description: TRex stateless traffic generator for RFC2544
            external-interface:
            -   name: xe0
                virtual-interface:
                    type: PCI-PASSTHROUGH
                    vpci: '{{ interfaces.xe0.vpci}}'
                    local_ip: '{{ interfaces.xe0.local_ip }}'
                    dst_ip: '{{ interfaces.xe0.dst_ip }}'
                    local_mac: '{{ interfaces.xe0.local_mac }}'
                    dst_mac: '{{ interfaces.xe0.dst_mac }}'
                    bandwidth: 10 Gbps
                vnfd-connection-point-ref: xe0
            -   name: xe1
                virtual-interface:
                    type: PCI-PASSTHROUGH
                    vpci: '{{ interfaces.xe1.vpci }}'
                    local_ip: '{{ interfaces.xe1.local_ip }}'
                    dst_ip: '{{ interfaces.xe1.dst_ip }}'
                    local_mac: '{{ interfaces.xe1.local_mac }}'
                    dst_mac: '{{ interfaces.xe1.dst_mac }}'
                    bandwidth: 10 Gbps
                vnfd-connection-point-ref: xe1
            routing_table: {{ routing_table }}
            nd_route_tbl: {{ nd_route_tbl }}

        benchmark:
            kpi:
                - rx_throughput_fps
                - tx_throughput_fps
                - tx_throughput_mbps
                - rx_throughput_mbps
                - tx_throughput_pc_linerate
                - rx_throughput_pc_linerate
                - min_latency
                - max_latency
                - avg_latency
"""

COMPLETE_TREX_VNFD = \
    {'vnfd:vnfd-catalog':
     {'vnfd':
      [{'benchmark':
        {'kpi':
         ['rx_throughput_fps',
          'tx_throughput_fps',
          'tx_throughput_mbps',
          'rx_throughput_mbps',
          'tx_throughput_pc_linerate',
          'rx_throughput_pc_linerate',
          'min_latency',
          'max_latency',
          'avg_latency']},
        'connection-point': [{'name': 'xe0',
                              'type': 'VPORT'},
                             {'name': 'xe1',
                              'type': 'VPORT'}],
        'description': 'TRex stateless traffic generator for RFC2544',
        'id': 'TrexTrafficGen',
        'mgmt-interface': {'ip': '1.1.1.1',
                           'password': 'berta',
                           'user': 'berta',
                           'vdu-id': 'trexgen-baremetal'},
        'name': 'trexgen',
        'short-name': 'trexgen',
        'vdu': [{'description': 'TRex stateless traffic generator for RFC2544',
                 'external-interface':
                 [{'name': 'xe0',
                   'virtual-interface': {'bandwidth': '10 Gbps',
                                         'dst_ip': '1.1.1.1',
                                         'dst_mac': '00:01:02:03:04:05',
                                         'local_ip': '1.1.1.2',
                                         'local_mac': '00:01:02:03:05:05',
                                         'type': 'PCI-PASSTHROUGH',
                                         'vpci': '0000:00:10.2'},
                   'vnfd-connection-point-ref': 'xe0'},
                  {'name': 'xe1',
                   'virtual-interface': {'bandwidth': '10 Gbps',
                                         'dst_ip': '2.1.1.1',
                                         'dst_mac': '00:01:02:03:04:06',
                                         'local_ip': '2.1.1.2',
                                         'local_mac': '00:01:02:03:05:06',
                                         'type': 'PCI-PASSTHROUGH',
                                         'vpci': '0000:00:10.1'},
                   'vnfd-connection-point-ref': 'xe1'}],
                 'id': 'trexgen-baremetal',
                 'nd_route_tbl': [{'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                                   'if': 'xe0',
                                   'netmask': '112',
                                   'network': '0064:ff9b:0:0:0:0:9810:6414'},
                                  {'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                                   'if': 'xe1',
                                   'netmask': '112',
                                   'network': '0064:ff9b:0:0:0:0:9810:2814'}],
                 'routing_table': [{'gateway': '152.16.100.20',
                                    'if': 'xe0',
                                    'netmask': '255.255.255.0',
                                    'network': '152.16.100.20'},
                                   {'gateway': '152.16.40.20',
                                    'if': 'xe1',
                                    'netmask': '255.255.255.0',
                                    'network': '152.16.40.20'}],
                 'name': 'trexgen-baremetal'}]}]}}

NODE_CFG = {'ip': '1.1.1.1',
            'name': 'demeter',
            'password': 'berta',
            'role': 'TrafficGen',
            'user': 'berta',
            'interfaces': {'xe0': {'dpdk_port_num': 1,
                                   'dst_ip': '1.1.1.1',
                                   'dst_mac': '00:01:02:03:04:05',
                                   'local_ip': '1.1.1.2',
                                   'local_mac': '00:01:02:03:05:05',
                                   'vpci': '0000:00:10.2'},
                           'xe1': {'dpdk_port_num': 0,
                                   'dst_ip': '2.1.1.1',
                                   'dst_mac': '00:01:02:03:04:06',
                                   'local_ip': '2.1.1.2',
                                   'local_mac': '00:01:02:03:05:06',
                                   'vpci': '0000:00:10.1'}},
            'nd_route_tbl': [{u'gateway': u'0064:ff9b:0:0:0:0:9810:6414',
                              u'if': u'xe0',
                              u'netmask': u'112',
                              u'network': u'0064:ff9b:0:0:0:0:9810:6414'},
                             {u'gateway': u'0064:ff9b:0:0:0:0:9810:2814',
                              u'if': u'xe1',
                              u'netmask': u'112',
                              u'network': u'0064:ff9b:0:0:0:0:9810:2814'}],
            'routing_table': [{u'gateway': u'152.16.100.20',
                               u'if': u'xe0',
                               u'netmask': u'255.255.255.0',
                               u'network': u'152.16.100.20'},
                              {u'gateway': u'152.16.40.20',
                               u'if': u'xe1',
                               u'netmask': u'255.255.255.0',
                               u'network': u'152.16.40.20'}],
            }


# need to template, but can't use {} so use %s
TRAFFIC_PROFILE_TPL = """
%(0)s:
    - ipv4:
        outer_l2:
            framesize:
                64B: "{{ get(imix, '%(0)s.imix_small', 10) }}"
                128B: "{{ get(imix, '%(0)s.imix_128B', 10) }}"
                256B: "{{ get(imix, '%(0)s.imix_256B', 10) }}"
                373B: "{{ get(imix, '%(0)s.imix_373B', 10) }}"
                570B: "{{get(imix, '%(0)s.imix_570B', 10) }}"
                1400B: "{{get(imix, '%(0)s.imix_1400B', 10) }}"
                1518B: "{{get(imix, '%(0)s.imix_1500B', 40) }}"
""" % {"0": UPLINK}

TRAFFIC_PROFILE = {
    UPLINK: [{"ipv4": {"outer_l2":
                       {"framesize": {"64B": '10', "128B": '10',
                                      "256B": '10', "373B": '10',
                                      "570B": '10', "1400B": '10',
                                      "1518B": '40'}}}}]}


class TestRender(unittest.TestCase):

    def test_render_none(self):

        tmpl = "{{ routing_table }}"
        self.assertEqual(vnfdgen.render(tmpl, routing_table=None), u'~')
        self.assertIsNone(
            yaml_load(vnfdgen.render(tmpl, routing_table=None)))

    def test_render_unicode_dict(self):

        tmpl = "{{ routing_table }}"
        self.assertEqual(yaml_load(vnfdgen.render(
            tmpl, **NODE_CFG)), NODE_CFG["routing_table"])


class TestVnfdGen(unittest.TestCase):
    """ Class to verify VNFS testcases """

    def test_generate_vnfd(self):
        """ Function to verify vnfd generation based on template """
        self.maxDiff = None
        generated_vnfd = vnfdgen.generate_vnfd(TREX_VNFD_TEMPLATE, NODE_CFG)
        self.assertDictEqual(COMPLETE_TREX_VNFD, generated_vnfd)

    def test_generate_tp_no_vars(self):
        """ Function to verify traffic profile generation without imix """

        self.maxDiff = None
        generated_tp = vnfdgen.generate_vnfd(TRAFFIC_PROFILE_TPL, {"imix": {}})
        self.assertDictEqual(TRAFFIC_PROFILE, generated_tp)

    def test_deepgetitem(self):
        d = {'a': 1, 'b': 2}
        self.assertEqual(vnfdgen.deepgetitem(d, "a"), 1)

    def test_dict_flatten_int(self):
        d = {'a': 1, 'b': 2}
        self.assertEqual(vnfdgen.deepgetitem(d, "a"), 1)

    def test_dict_flatten_str_int_key_first(self):
        d = {'0': 1, 0: 24, 'b': 2}
        self.assertEqual(vnfdgen.deepgetitem(d, "0"), 1)

    def test_dict_flatten_int_key_fallback(self):
        d = {0: 1, 'b': 2}
        self.assertEqual(vnfdgen.deepgetitem(d, "0"), 1)

    def test_dict_flatten_list(self):
        d = {'a': 1, 'b': list(range(2))}
        self.assertEqual(vnfdgen.deepgetitem(d, "b.0"), 0)

    def test_dict_flatten_dict(self):
        d = {'a': 1, 'b': {x: x for x in list(range(2))}}
        self.assertEqual(vnfdgen.deepgetitem(d, "b.0"), 0)

    def test_dict_flatten_only_str_key(self):
        d = {'0': 1, 0: 24, 'b': 2}
        self.assertRaises(AttributeError, vnfdgen.deepgetitem, d, 0)

    def test_generate_tp_single_var(self):
        """ Function to verify traffic profile generation with imix """

        generated_tp = \
            vnfdgen.generate_vnfd(TRAFFIC_PROFILE_TPL,
                                  {"imix": {UPLINK: {"imix_small": '20'}}})
        self.maxDiff = None
        tp2 = dict(TRAFFIC_PROFILE)
        tp2[UPLINK][0]["ipv4"]["outer_l2"]["framesize"]["64B"] = '20'
        self.assertDictEqual(tp2, generated_tp)
