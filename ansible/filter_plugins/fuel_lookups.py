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

def do_find_fuel_nodes(fuel_nodes):
    ips = {}
    for fuel_node in fuel_nodes:
        if 'controller' in fuel_node['roles']:
            ips.setdefault("controller_ids", []).append(fuel_node['id'])
            ips.setdefault("controllers_ips", []).append(fuel_node['ip'])
        if 'compute' in fuel_node['roles']:
            ips.setdefault("compute_ids", []).append(fuel_node['id'])
            ips.setdefault("computes_ips", []).append(fuel_node['ip'])
    return ips

# def do_find_fuel_nodes(fuel_output):
#     ips = {}
#     for l in fuel_output.splitlines():
#         splits = l.splti()
#         if 'controller' in l:
#             ips["controller_ids"] = splits[0]
#             ips["controllers_ips"] = splits[9]
#         if 'compute' in l:
#             ips["compute_ids"] = splits[0]
#             ips["computes_ips"] = splits[9]
#     return ips


class FilterModule(object):
    def filters(self):
        return {
            'find_fuel_nodes': do_find_fuel_nodes,
        }


SAMPLE = """\
id | status | name             | cluster | ip        | mac               | roles                | pending_roles | online | group_id
---+--------+------------------+---------+-----------+-------------------+----------------------+---------------+--------+---------
 4 | ready  | Untitled (9a:b1) |       1 | 10.20.0.6 | 0c:c4:7a:75:9a:b1 | ceph-osd, compute    |               |      1 |        1
 1 | ready  | Untitled (9a:ab) |       1 | 10.20.0.4 | 0c:c4:7a:75:9a:ab | ceph-osd, controller |               |      1 |        1
 5 | ready  | Untitled (9a:1b) |       1 | 10.20.0.7 | 0c:c4:7a:75:9a:1b | ceph-osd, compute    |               |      1 |        1
 2 | ready  | Untitled (9a:67) |       1 | 10.20.0.3 | 0c:c4:7a:75:9a:67 | controller           |               |      1 |        1
 3 | ready  | Untitled (99:d7) |       1 | 10.20.0.5 | 0c:c4:7a:75:99:d7 | controller, mongo    |               |      1 |        1
"""