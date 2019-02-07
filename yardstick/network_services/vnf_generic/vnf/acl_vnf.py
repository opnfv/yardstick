# Copyright (c) 2016-2019 Intel Corporation
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

import logging
import ipaddress
import six
from yardstick.common import utils
from yardstick.common import exceptions

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF, DpdkVnfSetupEnvHelper
from yardstick.network_services.helpers.samplevnf_helper import PortPairs
from itertools import chain

LOG = logging.getLogger(__name__)

# ACL should work the same on all systems, we can provide the binary
ACL_PIPELINE_COMMAND = \
    'sudo {tool_path} -p {port_mask_hex} -f {cfg_file} -s {script} {hwlb}'

ACL_COLLECT_KPI = r"""\
ACL TOTAL:[^p]+pkts_processed"?:\s(\d+),[^p]+pkts_drop"?:\s(\d+),[^p]+pkts_received"?:\s(\d+),"""


class AclApproxSetupEnvSetupEnvHelper(DpdkVnfSetupEnvHelper):

    APP_NAME = "vACL"
    CFG_CONFIG = "/tmp/acl_config"
    CFG_SCRIPT = "/tmp/acl_script"
    PIPELINE_COMMAND = ACL_PIPELINE_COMMAND
    HW_DEFAULT_CORE = 2
    SW_DEFAULT_CORE = 5
    DEFAULT_CONFIG_TPL_CFG = "acl.cfg"
    VNF_TYPE = "ACL"
    RULE_CMD = "acl"

    DEFAULT_PRIORITY = 1
    DEFAULT_PROTOCOL = 0
    DEFAULT_PROTOCOL_MASK = 0
    # Default actions to be applied to SampleVNF. Please note,
    # that this list is extended with `fwd` action when default
    # actions are generated.
    DEFAULT_FWD_ACTIONS = ["accept", "count"]

    def __init__(self, vnfd_helper, ssh_helper, scenario_helper):
        super(AclApproxSetupEnvSetupEnvHelper, self).__init__(vnfd_helper,
                                                              ssh_helper,
                                                              scenario_helper)
        self._action_id = 0

    def get_ip_from_port(self, port):
        # we can't use gateway because in OpenStack gateways interfere with floating ip routing
        # return self.make_ip_addr(self.get_ports_gateway(port), self.get_netmask_gateway(port))
        vintf = self.vnfd_helper.find_interface(name=port)["virtual-interface"]
        return utils.make_ip_addr(vintf["local_ip"], vintf["netmask"])

    def get_network_and_prefixlen_from_ip_of_port(self, port):
        ip_addr = self.get_ip_from_port(port)
        # handle cases with no gateway
        if ip_addr:
            return ip_addr.network.network_address.exploded, ip_addr.network.prefixlen
        else:
            return None, None

    @property
    def new_action_id(self):
        """Get new action id"""
        self._action_id += 1
        return self._action_id

    def get_default_flows(self):
        """Get default actions/rules
        Returns: (<actions>, <rules>)
            <actions>:
                 { <action_id>: [ <list of actions> ]}
            Example:
                 { 0 : [ "accept", "count", {"fwd" : "port": 0} ], ... }
            <rules>:
                 [ {"src_ip": "x.x.x.x", "src_ip_mask", 24, ...}, ... ]
            Note:
                See `generate_rule_cmds()` to get list of possible map keys.
        """
        actions, rules = {}, []
        _port_pairs = PortPairs(self.vnfd_helper.interfaces)
        port_pair_list = _port_pairs.port_pair_list
        for src_intf, dst_intf in port_pair_list:
            # get port numbers of the interfaces
            src_port = self.vnfd_helper.port_num(src_intf)
            dst_port = self.vnfd_helper.port_num(dst_intf)
            # get interface addresses and prefixes
            src_net, src_prefix_len = self.get_network_and_prefixlen_from_ip_of_port(src_intf)
            dst_net, dst_prefix_len = self.get_network_and_prefixlen_from_ip_of_port(dst_intf)
            # ignore entries with empty values
            if all((src_net, src_prefix_len, dst_net, dst_prefix_len)):
                # flow: src_net:dst_net -> dst_port
                action_id = self.new_action_id
                actions[action_id] = self.DEFAULT_FWD_ACTIONS[:]
                actions[action_id].append({"fwd": {"port": dst_port}})
                rules.append({"priority": 1, 'cmd': self.RULE_CMD,
                    "src_ip": src_net, "src_ip_mask": src_prefix_len,
                    "dst_ip": dst_net, "dst_ip_mask": dst_prefix_len,
                    "src_port_from": 0, "src_port_to": 65535,
                    "dst_port_from": 0, "dst_port_to": 65535,
                    "protocol": 0, "protocol_mask": 0,
                    "action_id": action_id})
                # flow: dst_net:src_net -> src_port
                action_id = self.new_action_id
                actions[action_id] = self.DEFAULT_FWD_ACTIONS[:]
                actions[action_id].append({"fwd": {"port": src_port}})
                rules.append({"cmd":self.RULE_CMD, "priority": 1,
                    "src_ip": dst_net, "src_ip_mask": dst_prefix_len,
                    "dst_ip": src_net, "dst_ip_mask": src_prefix_len,
                    "src_port_from": 0, "src_port_to": 65535,
                    "dst_port_from": 0, "dst_port_to": 65535,
                    "protocol": 0, "protocol_mask": 0,
                    "action_id": action_id})
        return actions, rules

    def get_flows(self, options):
        """Get actions/rules based on provided options.
        The `options` is a dict representing the ACL rules configuration
        file. Result is the same as described in `get_default_flows()`.
        """
        actions, rules = {}, []
        for ace in options['access-list-entries']:
            # Generate list of actions
            action_id = self.new_action_id
            actions[action_id] = ace['actions']
            # Destination nestwork
            matches = ace['matches']
            dst_ipv4_net = matches['destination-ipv4-network']
            dst_ipv4_net_ip = ipaddress.ip_interface(six.text_type(dst_ipv4_net))
            # Source network
            src_ipv4_net = matches['source-ipv4-network']
            src_ipv4_net_ip = ipaddress.ip_interface(six.text_type(src_ipv4_net))
            # Append the rule
            rules.append({'action_id': action_id, 'cmd': self.RULE_CMD,
                'dst_ip': dst_ipv4_net_ip.network.network_address.exploded,
                'dst_ip_mask': dst_ipv4_net_ip.network.prefixlen,
                'src_ip': src_ipv4_net_ip.network.network_address.exploded,
                'src_ip_mask': src_ipv4_net_ip.network.prefixlen,
                'dst_port_from': matches['destination-port-range']['lower-port'],
                'dst_port_to': matches['destination-port-range']['upper-port'],
                'src_port_from': matches['source-port-range']['lower-port'],
                'src_port_to': matches['source-port-range']['upper-port'],
                'priority': matches.get('priority', self.DEFAULT_PRIORITY),
                'protocol': matches.get('protocol', self.DEFAULT_PROTOCOL),
                'protocol_mask': matches.get('protocol_mask',
                                              self.DEFAULT_PROTOCOL_MASK)
            })
        return actions, rules

    def generate_rule_cmds(self, rules, apply_rules=False):
        """Convert rules into list of SampleVNF CLI commands"""
        rule_template = ("p {cmd} add {priority} {src_ip} {src_ip_mask} "
                         "{dst_ip} {dst_ip_mask} {src_port_from} {src_port_to} "
                         "{dst_port_from} {dst_port_to} {protocol} "
                         "{protocol_mask} {action_id}")
        rule_cmd_list = []
        for rule in rules:
            rule_cmd_list.append(rule_template.format(**rule))
        if apply_rules:
            # add command to apply all rules at the end
            rule_cmd_list.append("p {cmd} applyruleset".format(cmd=self.RULE_CMD))
        return rule_cmd_list

    def generate_action_cmds(self, actions):
        """Convert actions into list of SampleVNF CLI commands.
        These method doesn't validate the provided list of actions. Supported
        list of actions are limited by SampleVNF. Thus, the user should be
        responsible to specify correct action name(s). Yardstick should take
        the provided action by user and apply it to SampleVNF.
        Anyway, some of the actions require addition parameters to be
        specified. In case of `fwd` & `nat` action used have to specify
        the port attribute.
        """
        _action_template_map = {
            "fwd": "p action add {action_id} fwd {port}",
            "nat": "p action add {action_id} nat {port}"
        }
        action_cmd_list = []
        for action_id, actions in actions.items():
            for action in actions:
                if isinstance(action, dict):
                    for action_name in action.keys():
                        # user provided an action name with addition options
                        # e.g.: {"fwd": {"port": 0}}
                        # format action CLI command and add it to the list
                        if action_name not in _action_template_map.keys():
                            raise exceptions.AclUnknownActionTemplate(
                                action_name=action_name)
                        template = _action_template_map[action_name]
                        try:
                            action_cmd_list.append(template.format(
                                action_id=action_id, **action[action_name]))
                        except KeyError as exp:
                            raise exceptions.AclMissingActionArguments(
                                action_name=action_name,
                                action_param=exp.args[0])
                else:
                    # user provided an action name w/o addition options
                    # e.g.: "accept", "count"
                    action_cmd_list.append(
                        "p action add {action_id} {action}".format(
                        action_id=action_id, action=action))
        return action_cmd_list

    def get_flows_config(self, options=None):
        """Get action/rules configuration commands (string) to be
        applied to SampleVNF to configure ACL rules (flows).
        """
        action_cmd_list, rule_cmd_list = [], []
        if options:
            # if file name is set, read actions/rules from the file
            actions, rules = self.get_flows(options)
            action_cmd_list = self.generate_action_cmds(actions)
            rule_cmd_list = self.generate_rule_cmds(rules)
        # default actions/rules
        dft_actions, dft_rules = self.get_default_flows()
        dft_action_cmd_list = self.generate_action_cmds(dft_actions)
        dft_rule_cmd_list = self.generate_rule_cmds(dft_rules, apply_rules=True)
        # generate multi-line commands to add actions/rules
        return '\n'.join(chain(action_cmd_list, dft_action_cmd_list,
                               rule_cmd_list, dft_rule_cmd_list))


class AclApproxVnf(SampleVNF):

    APP_NAME = "vACL"
    APP_WORD = 'acl'
    COLLECT_KPI = ACL_COLLECT_KPI

    COLLECT_MAP = {
        'packets_in': 3,
        'packets_fwd': 1,
        'packets_dropped': 2,
    }

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = AclApproxSetupEnvSetupEnvHelper

        super(AclApproxVnf, self).__init__(name, vnfd, setup_env_helper_type, resource_helper_type)

    def wait_for_instantiate(self):
        """Wait for VNF to initialize"""
        self.wait_for_initialize()
