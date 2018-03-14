# Copyright (c) 2018 Intel Corporation
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

import abc

import six

from yardstick.common import exceptions


@six.add_metaclass(abc.ABCMeta)
class Payload(object):
    """Base Payload class to transfer data through the MQ service"""

    REQUIRED_FIELDS = {'version'}

    def __init__(self, **kwargs):
        """Init method

        :param kwargs: (dictionary) attributes and values of the object
        :returns: Payload object
        """

        if not all(req_field in kwargs for req_field in self.REQUIRED_FIELDS):
            _attrs = set(kwargs) - self.REQUIRED_FIELDS
            missing_attributes = ', '.join(str(_attr) for _attr in _attrs)
            raise exceptions.PayloadMissingAttributes(
                missing_attributes=missing_attributes)

        for name, value in kwargs.items():
            setattr(self, name, value)

        self._fields = set(kwargs.keys())

    def obj_to_dict(self):
        """Returns a dictionary with the attributes of the object"""
        return {field: getattr(self, field) for field in self._fields}

    @classmethod
    def dict_to_obj(cls, _dict):
        """Returns a Payload object built from the dictionary elements"""
        return cls(**_dict)
