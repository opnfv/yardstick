##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import abc
import six

import yardstick.common.utils as utils


@six.add_metaclass(abc.ABCMeta)
class Base(object):

    def __init__(self, conf):
        self.conf = conf

    @staticmethod
    def get_cls(dispatcher_type):
        '''Return class of specified type.'''
        for dispatcher in utils.itersubclasses(Base):
            if dispatcher_type == dispatcher.__dispatcher_type__:
                return dispatcher
        raise RuntimeError("No such dispatcher_type %s" % dispatcher_type)

    @staticmethod
    def get(config):
        """Returns instance of a dispatcher for dispatcher type.
        """
        return Base.get_cls(config["type"])(config)

    @abc.abstractmethod
    def record_result_data(self, data):
        """Recording result data interface."""
