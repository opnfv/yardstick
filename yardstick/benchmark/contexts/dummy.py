##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from yardstick.benchmark import contexts
from yardstick.benchmark.contexts import base


class DummyContext(base.Context):
    """Class that handle dummy info.

    This class is also used to test the abstract class Context because it
    provides a minimal concrete implementation of a subclass.
    """

    __context_type__ = contexts.CONTEXT_DUMMY

    def deploy(self):
        """Don't need to deploy"""
        pass

    def undeploy(self):
        """Don't need to undeploy"""
        pass

    def _get_server(self, attr_name):
        return None

    def _get_network(self, attr_name):
        return None

    def _get_physical_nodes(self):
        return None

    def _get_physical_node_for_server(self, server_name):
        return None
