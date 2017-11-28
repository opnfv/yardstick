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
import collections
from itertools import islice


def get_server(context, attr_name):
    """lookup server info by name from context

    Keyword arguments:
    attr_name -- A name for a server listed in nodes config file
    """
    node_name, name = context.split_name(attr_name)
    if name is None or context.name != name:
        return None

    matching_nodes = list(islice((n for n in context.nodes if n["name"] == node_name), 2))
    number_of_matching_nodes = len(matching_nodes)
    if number_of_matching_nodes == 0:
        return None
    if number_of_matching_nodes > 1:
        raise ValueError("Duplicate nodes!! Nodes {}".format(matching_nodes))
    # A clone is created in order to avoid affecting the
    # original one.
    node = dict(matching_nodes[0])
    node['name'] = attr_name
    node.setdefault("interfaces", {})
    return node


def get_network(context, attr_name):
    if not isinstance(attr_name, collections.Mapping):
        network = context.networks.get(attr_name)

    else:
        # Don't generalize too much  Just support vld_id
        vld_id = attr_name.get('vld_id', {})
        # for standalone context networks are dicts
        iter1 = (n for n in context.networks.values() if n.get('vld_id') == vld_id)
        network = next(iter1, None)

    if network is None:
        return None

    result = {
        # name is required
        "name": network["name"],
        "vld_id": network.get("vld_id"),
        "segmentation_id": network.get("segmentation_id"),
        "network_type": network.get("network_type"),
        "physical_network": network.get("physical_network"),
    }
    return result
