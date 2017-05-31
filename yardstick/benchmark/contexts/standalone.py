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
        self.nfvi_node = []
        self.attrs = {}
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
        self.attrs = attrs
        LOG.debug("Nodes: %r", self.nodes)
        LOG.debug("NFVi Node: %r", self.nfvi_node)

    def deploy(self):
        """don't need to deploy"""

        # Todo: NFVi deploy (sriov, vswitch, ovs etc) based on the config.
        pass

    def undeploy(self):
        """don't need to undeploy"""

        # Todo: NFVi undeploy (sriov, vswitch, ovs etc) based on the config.
        super(StandaloneContext, self).undeploy()

    def _get_context_from_server(self, name):
        """lookup server info for a given nodename
        name: a name for a server listed in nodes and get its attributes
        """
        _, name = self.split_name(name)
        if name is not None and self.name == name:
            return self.attrs
        return None

    def _get_server(self, attr_name):
        """lookup server info by name from context

        Keyword arguments:
        attr_name -- A name for a server listed in nodes config file
        """
        node_name, name = self.split_name(attr_name)
        if name is None or self.name != name:
            return None

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
