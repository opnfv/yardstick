##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import logging

from yardstick.benchmark.contexts.base import Context


LOG = logging.getLogger(__name__)


class DummyContext(Context):
    '''Class that handle dummy info'''

    __context_type__ = "Dummy"

    def __init__(self):
        super(self.__class__, self).__init__()

    def init(self, attrs):
        pass

    def deploy(self):
        '''don't need to deploy'''
        pass

    def undeploy(self):
        '''don't need to undeploy'''
        pass

    def _get_server(self, attr_name):
        return None
