##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
import logging
import errno
import os
import collections
import yaml

from yardstick.benchmark.contexts.base import Context
from yardstick.definitions import YARDSTICK_ROOT_PATH

LOG = logging.getLogger(__name__)


class NodeContext(Context):
    """Class that handle nodes info"""

    __context_type__ = "Node"

    def __init__(self):
        self.name = None
        self.file_path = None
        self.nodes = []
        self.controllers = []
        self.computes = []
        self.baremetals = []
        super(self.__class__, self).__init__()

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

        try:
            cfg = self.read_config_file()
        except IOError as ioerror:
            if ioerror.errno == errno.ENOENT:
                self.file_path = \
                    os.path.join(YARDSTICK_ROOT_PATH, self.file_path)
                cfg = self.read_config_file()
            else:
                raise

        self.nodes.extend(cfg["nodes"])
        self.controllers.extend([node for node in cfg["nodes"]
                                 if node["role"] == "Controller"])
        self.computes.extend([node for node in cfg["nodes"]
                              if node["role"] == "Compute"])
        self.baremetals.extend([node for node in cfg["nodes"]
                                if node["role"] == "Baremetal"])
        LOG.debug("Nodes: %r", self.nodes)
        LOG.debug("Controllers: %r", self.controllers)
        LOG.debug("Computes: %r", self.computes)
        LOG.debug("BareMetals: %r", self.baremetals)

    def deploy(self):
        """don't need to deploy"""
        pass

    def undeploy(self):
        """don't need to undeploy"""
        pass

    def _get_server(self, attr_name):
        """lookup server info by name from context
        attr_name: a name for a server listed in nodes config file
        """
        if isinstance(attr_name, collections.Mapping):
            return None

        if self.name != attr_name.split(".")[1]:
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
