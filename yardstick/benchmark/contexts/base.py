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
class Context(object):
    '''Class that represents a context in the logical model'''
    list = []

    def __init__(self):
        Context.list.append(self)

    @abc.abstractmethod
    def init(self, attrs):
        "TODO add comments"

    @staticmethod
    def get_cls(context_type):
        '''Return class of specified type.'''
        for context in utils.itersubclasses(Context):
            if context_type == context.__context_type__:
                return context
        raise RuntimeError("No such context_type %s" % context_type)

    @staticmethod
    def get(context_type):
        """Returns instance of a context for context type.
        """
        return Context.get_cls(context_type)()

    @abc.abstractmethod
    def deploy(self):
        '''TODO add comments'''

    @abc.abstractmethod
    def undeploy(self):
        '''TODO add comments'''

    @abc.abstractmethod
    def get_server(self, attr_name):
        '''lookup server object by name from context
        attr_name: either a name for a server created by yardstick or a dict
        with attribute name mapping when using external heat templates
        '''
