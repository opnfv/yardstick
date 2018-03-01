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


class Flags(object):
    """Class to represent the status of the flags in a context"""

    _FLAGS = {'no_setup': False,
              'no_teardown': False}

    def __init__(self, **kwargs):
        for name, value in self._FLAGS.items():
            setattr(self, name, value)

        for name, value in ((name, value) for (name, value) in kwargs.items()
                            if name in self._FLAGS):
            setattr(self, name, value)

    def parse(self, **kwargs):
        """Read in values matching the flags stored in this object"""
        if not kwargs:
            return

        for name, value in ((name, value) for (name, value) in kwargs.items()
                            if name in self._FLAGS):
            setattr(self, name, value)


@six.add_metaclass(abc.ABCMeta)
class Context(object):
    """Class that represents a context in the logical model"""
    list = []
    SHORT_TASK_ID_LEN = 8

    @staticmethod
    def split_name(name, sep='.'):
        try:
            name_iter = iter(name.split(sep))
        except AttributeError:
            # name is not a string
            return None, None
        return next(name_iter), next(name_iter, None)

    def __init__(self):
        Context.list.append(self)
        self._flags = Flags()
        self._name = None
        self._task_id = None

    def init(self, attrs):
        """Initiate context"""
        self._name = attrs['name']
        self._task_id = attrs['task_id']
        self._flags.parse(**attrs.get('flags', {}))
        self._name_task_id = '{}-{}'.format(
            self._name, self._task_id[:self.SHORT_TASK_ID_LEN])

    @property
    def name(self):
        if self._flags.no_setup or self._flags.no_teardown:
            return self._name
        else:
            return self._name_task_id

    @property
    def assigned_name(self):
        return self._name

    @staticmethod
    def get_cls(context_type):
        """Return class of specified type."""
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
        """Deploy context."""

    @abc.abstractmethod
    def undeploy(self):
        """Undeploy context."""
        self._delete_context()

    def _delete_context(self):
        Context.list.remove(self)

    @abc.abstractmethod
    def _get_server(self, attr_name):
        """get server info by name from context
        """

    @abc.abstractmethod
    def _get_network(self, attr_name):
        """get network info by name from context
        """

    @staticmethod
    def get_server(attr_name):
        """lookup server info by name from context
        attr_name: either a name for a server created by yardstick or a dict
        with attribute name mapping when using external heat templates
        """
        servers = (context._get_server(attr_name) for context in Context.list)
        try:
            return next(s for s in servers if s)
        except StopIteration:
            raise ValueError("context not found for server %r" %
                             attr_name)

    @staticmethod
    def get_context_from_server(attr_name):
        """lookup context info by name from node config
        attr_name: either a name of the node created by yardstick or a dict
        with attribute name mapping when using external templates

        :returns Context instance
        """
        servers = ((context._get_server(attr_name), context)
                   for context in Context.list)
        try:
            return next(con for s, con in servers if s)
        except StopIteration:
            raise ValueError("context not found for name %r" %
                             attr_name)

    @staticmethod
    def get_network(attr_name):
        """lookup server info by name from context
        attr_name: either a name for a server created by yardstick or a dict
        with attribute name mapping when using external heat templates
        """

        networks = (context._get_network(attr_name) for context in Context.list)
        try:
            return next(n for n in networks if n)
        except StopIteration:
            raise ValueError("context not found for server %r" %
                             attr_name)
