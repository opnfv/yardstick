# Copyright 2013 IBM Corp
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# yardstick comment: this is a modified copy of
# ceilometer/ceilometer/dispatcher/__init__.py

from __future__ import absolute_import
import abc
import six

import yardstick.common.utils as utils


@six.add_metaclass(abc.ABCMeta)
class Base(object):

    def __init__(self, conf):
        self.conf = conf

    @staticmethod
    def get_cls(dispatcher_type):
        """Return class of specified type."""
        for dispatcher in utils.itersubclasses(Base):
            if dispatcher_type == dispatcher.__dispatcher_type__:
                return dispatcher
        raise RuntimeError("No such dispatcher_type %s" % dispatcher_type)

    @staticmethod
    def get(config):
        """Returns instance of a dispatcher for dispatcher type.
        """
        out_type = config['DEFAULT']['dispatcher']

        return Base.get_cls(out_type.capitalize())(config)

    @abc.abstractmethod
    def flush_result_data(self, data):
        """Flush result data into permanent storage media interface."""
