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
import logging
import ipaddress
import six

from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)


class YangModel(object):

    RULE_TEMPLATE = "p acl add 1 {0} {1} {2} {3} {4} {5} {6} {7} 0 0 {8}"

    def __init__(self, config_file):
        super(YangModel, self).__init__()
        self._config_file = config_file
        self._options = {}
        self._rules = ''

    @property
    def config_file(self):
        return self._config_file

    @config_file.setter
    def config_file(self, value):
        self._config_file = value
        self._options = {}
        self._rules = ''

    def _read_config(self):
        # TODO: add some error handling in case of empty or non-existing file
        try:
            with open(self._config_file) as f:
                self._options = yaml_load(f)
        except Exception as e:
            LOG.exception("Failed to load the yaml %s", e)
            raise

    def _get_entries(self):
        if not self._options:
            return ''

        rule_list = []
        for ace in self._options['access-list1']['acl']['access-list-entries']:
            # TODO: resolve ports using topology file and nodes'
            # ids: public or private.
            matches = ace['ace']['matches']
            dst_ipv4_net = matches['destination-ipv4-network']
            dst_ipv4_net_ip = ipaddress.ip_interface(six.text_type(dst_ipv4_net))
            port0_local_network = dst_ipv4_net_ip.network.network_address.exploded
            port0_prefix = dst_ipv4_net_ip.network.prefixlen

            src_ipv4_net = matches['source-ipv4-network']
            src_ipv4_net_ip = ipaddress.ip_interface(six.text_type(src_ipv4_net))
            port1_local_network = src_ipv4_net_ip.network.network_address.exploded
            port1_prefix = src_ipv4_net_ip.network.prefixlen

            lower_dport = matches['destination-port-range']['lower-port']
            upper_dport = matches['destination-port-range']['upper-port']

            lower_sport = matches['source-port-range']['lower-port']
            upper_sport = matches['source-port-range']['upper-port']

            # TODO: proto should be read from file also.
            # Now all rules in sample ACL file are TCP.
            rule_list.append('')  # get an extra new line
            rule_list.append(self.RULE_TEMPLATE.format(port0_local_network,
                                                       port0_prefix,
                                                       port1_local_network,
                                                       port1_prefix,
                                                       lower_dport,
                                                       upper_dport,
                                                       lower_sport,
                                                       upper_sport,
                                                       0))
            rule_list.append(self.RULE_TEMPLATE.format(port1_local_network,
                                                       port1_prefix,
                                                       port0_local_network,
                                                       port0_prefix,
                                                       lower_sport,
                                                       upper_sport,
                                                       lower_dport,
                                                       upper_dport,
                                                       1))

        self._rules = '\n'.join(rule_list)

    def get_rules(self):
        if not self._rules:
            self._read_config()
            self._get_entries()
        return self._rules
