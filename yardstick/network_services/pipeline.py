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
from __future__ import print_function
import itertools

from six.moves import zip

FIREWALL_ADD_DEFAULT = "p {0} firewall add default 1"
FIREWALL_ADD_PRIO = """\
p {0} firewall add priority 1 ipv4  {1} 24 0.0.0.0 0 0 65535 0 65535 6 0xFF port 0"""

FLOW_ADD_QINQ_RULES = """\
p {0} flow add qinq 128 512 port 0 id 1
p {0} flow add default 1"""

ACTION_FLOW_BULK = "p {0} action flow bulk /tmp/action_bulk_512.txt"
ACTION_DSCP_CLASS_COLOR = "p {0} action dscp {1} class {2} color {3}"
ROUTE_ADD_DEFAULT = "p {0} route add default 1"
ROUTE_ADD_ETHER_QINQ = 'p {0} route add {1} {2} port 0 ether {3} qinq 0 {4}'
ROUTE_ADD_ETHER_MPLS = "p {0} route add {1} 21 port 0 ether {2} mpls 0:{3}"


class PipelineRules(object):

    def __init__(self, pipeline_id=0):
        super(PipelineRules, self).__init__()
        self.rule_list = []
        self.pipeline_id = pipeline_id

    def __str__(self):
        return '\n'.join(self.rule_list)

    def get_string(self):
        return str(self)

    def next_pipeline(self, num=1):
        self.pipeline_id += num

    def add_newline(self):
        self.rule_list.append('')

    def add_rule(self, base, *args):
        self.rule_list.append(base.format(self.pipeline_id, *args))

    def add_firewall_prio(self, ip):
        self.add_rule(FIREWALL_ADD_PRIO, ip)

    def add_firewall_script(self, ip):
        ip_addr = ip.split('.')
        assert len(ip_addr) == 4
        ip_addr[-1] = '0'
        for i in range(256):
            ip_addr[-2] = str(i)
            ip = '.'.join(ip_addr)
            self.add_firewall_prio(ip)
        self.add_rule(FIREWALL_ADD_DEFAULT)
        self.add_newline()

    def add_flow_classification_script(self):
        self.add_rule(FLOW_ADD_QINQ_RULES)

    def add_flow_action(self):
        self.add_rule(ACTION_FLOW_BULK)

    def add_dscp_class_color(self, dscp, color):
        self.add_rule(ACTION_DSCP_CLASS_COLOR, dscp, dscp % 4, color)

    def add_flow_action2(self):
        self.add_rule(ACTION_FLOW_BULK)
        for dscp, color in zip(range(64), itertools.cycle('GYR')):
            self.add_dscp_class_color(dscp, color)

    def add_route_ether_mpls(self, ip, mac_addr, index):
        self.add_rule(ROUTE_ADD_ETHER_MPLS, ip, mac_addr, index)

    def add_route_script(self, ip, mac_addr):
        ip_addr = ip.split('.')
        assert len(ip_addr) == 4
        ip_addr[-1] = '0'
        for index in range(0, 256, 8):
            ip_addr[-2] = str(index)
            ip = '.'.join(ip_addr)
            self.add_route_ether_mpls(ip, mac_addr, index)
        self.add_rule(ROUTE_ADD_DEFAULT)
        self.add_newline()

    def add_ether_qinq(self, ip, mask, mac_addr, index):
        self.add_rule(ROUTE_ADD_ETHER_QINQ, ip, mask, mac_addr, index)

    def add_route_script2(self, ip, mac_addr):
        ip_addr = ip.split('.')
        assert len(ip_addr) == 4
        ip_addr[-1] = '0'
        mask = 24
        for i in range(0, 256):
            ip_addr[-2] = str(i)
            ip = '.'.join(ip_addr)
            self.add_ether_qinq(ip, mask, mac_addr, i)
        self.add_rule(ROUTE_ADD_DEFAULT)
        self.add_newline()
