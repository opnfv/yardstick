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
"""This module handle non managed standalone virtualization node."""

from __future__ import absolute_import
import logging
import errno
import collections
import yaml

from yardstick.benchmark.contexts.base import Context
from yardstick.common.constants import YARDSTICK_ROOT_PATH

LOG = logging.getLogger(__name__)


class StandaloneContext(Context):
    """ This class handles standalone nodes - VM running on Non-Managed NFVi
    Configuration: vswitch, ovs, ovs-dpdk, sr-iov, linuxbridge
    """

    __context_type__ = "Standalone"

    def __init__(self):
        self.name = None
        self.file_path = None
        self.nodes = []
        self.networks = {}
        self.nfvi_node = []
        super(StandaloneContext, self).__init__()

    def read_config_file(self):
        """Read from config file"""

        with open(self.file_path) as stream:
            LOG.info("Parsing pod file: %s", self.file_path)
            cfg = yaml.load(stream)
        return cfg

    def init(self, attrs):
        """initializes itself from the supplied arguments"""

        self.name = attrs["name"]
        self.file_path = attrs.get("file", "pod.yaml")
        LOG.info("Parsing pod file: %s", self.file_path)

        try:
            cfg = self.read_config_file()
        except IOError as ioerror:
            if ioerror.errno == errno.ENOENT:
                self.file_path = YARDSTICK_ROOT_PATH + self.file_path
                cfg = self.read_config_file()
            else:
                raise

        self.nodes.extend(cfg["nodes"])
        self.nfvi_node.extend([node for node in cfg["nodes"]
                               if node["role"] == "nfvi_node"])
        # add optional static network definition
        self.networks.update(cfg.get("networks", {}))
        LOG.debug("Nodes: %r", self.nodes)
        LOG.debug("NFVi Node: %r", self.nfvi_node)
        LOG.debug("Networks: %r", self.networks)

    def deploy(self):
        """don't need to deploy"""

        # Todo: NFVi deploy (sriov, vswitch, ovs etc) based on the config.
        pass

    def undeploy(self):
        """don't need to undeploy"""

        # Todo: NFVi undeploy (sriov, vswitch, ovs etc) based on the config.
        super(StandaloneContext, self).undeploy()

    def _get_server(self, attr_name):
        """lookup server info by name from context

        Keyword arguments:
        attr_name -- A name for a server listed in nodes config file
        """

        if isinstance(attr_name, collections.Mapping):
            return None

        if self.name.split("-")[0] != attr_name.split(".")[1]:
            return None

        node_name = attr_name.split(".")[0]
        matching_nodes = (n for n in self.nodes if n["name"] == node_name)

        try:
            # A clone is created in order to avoid affecting the
            # original one.
            node = dict(next(matching_nodes))
        except StopIteration:
            return None

        try:
            duplicate = next(matching_nodes)
        except StopIteration:
            pass
        else:
            raise ValueError("Duplicate nodes!!! Nodes: %s %s",
                             (matching_nodes, duplicate))

        node["name"] = attr_name
        return node

    def _get_network(self, attr_name):
        if isinstance(attr_name, collections.Mapping):
            # Don't generalize too much  Just support vld_id
            vld_id = attr_name.get('vld_id')
            if vld_id is None:
                return None
            try:
                network = next(n for n in self.networks.values() if
                               getattr(n, "vld_id") == vld_id)
            except StopIteration:
                return None

        else:
            network = self.networks[attr_name]

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

