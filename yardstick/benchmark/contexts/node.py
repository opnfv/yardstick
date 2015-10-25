##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import sys
import yaml
import logging

from yardstick.benchmark.contexts.base import Context

LOG = logging.getLogger(__name__)


class NodeContext(Context):
    '''Class that handle nodes info'''

    __context_type__ = "Node"

    def __init__(self):
        self.name = None
        self.file_path = None
        self.nodes = []
        self.controllers = []
        self.computes = []
        self.baremetals = []
        super(self.__class__, self).__init__()

    def init(self, attrs):
        '''initializes itself from the supplied arguments'''
        self.name = attrs["name"]
        self.file_path = attrs.get("file", "/etc/yardstick/nodes/pod.yaml")

        LOG.info("Parsing pod file: %s", self.file_path)

        try:
            with open(self.file_path) as stream:
                cfg = yaml.load(stream)
        except IOError as ioerror:
            sys.exit(ioerror)

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
        '''don't need to deploy'''
        pass

    def undeploy(self):
        '''don't need to undeploy'''
        pass

    def _get_server(self, attr_name):
        '''lookup server info by name from context
        attr_name: a name for a server listed in nodes config file
        '''
        if type(attr_name) is dict:
            return None

        if self.name != attr_name.split(".")[1]:
            return None
        node_name = attr_name.split(".")[0]
        nodes = [n for n in self.nodes
                 if n["name"] == node_name]
        if len(nodes) == 0:
            return None
        elif len(nodes) > 1:
            LOG.error("Duplicate nodes!!!")
            LOG.error("Nodes: %r" % nodes)
            sys.exit(-1)

        node = nodes[0]

        server = {
            "name": attr_name,
            "ip": node["ip"],
            "user": node["user"],
            "key_filename": node["key_filename"]
        }

        return server
