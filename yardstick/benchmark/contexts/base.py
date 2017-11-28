##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import abc
import operator

import six

import yardstick.common.utils as utils
from yardstick.common.yaml_loader import yaml_load


@six.add_metaclass(abc.ABCMeta)
class Context(object):
    """Class that represents a context in the logical model"""
    list = []

    @staticmethod
    def split_name(name, sep=None):
        if sep is None:
            sep = '.'
        try:
            name_iter = iter(name.split(sep))
        except AttributeError:
            # name is not a string
            return None, None
        return next(name_iter), next(name_iter, None)

    @staticmethod
    def load_pod_yaml(logger, attrs, key='file', default='pod.yaml', alt_path=None):
        wrapper = utils.FilePathWrapper(attrs.get(key, default), alt_path)

        with wrapper:
            logger.info("Parsing pod file: %s", wrapper.base_path)
            cfg = yaml_load(wrapper.handle)

        return wrapper.base_path, cfg

    @staticmethod
    def iter_nodes_of_role(nodes, node_role_set, invert=False):
        def not_contains(a, b):
            return b not in a

        if invert:
            operator1 = not_contains
        else:
            operator1 = operator.contains

        return (node for node in nodes if operator1(node_role_set, str(node.get('role', ''))))

    def __init__(self):
        Context.list.append(self)

    @abc.abstractmethod
    def init(self, attrs):
        """Initiate context."""

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
