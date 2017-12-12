# Copyright (c) 2017 Intel Corporation
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

"""Yardstick custom exceptions"""

from oslo_utils import excutils


class YardstickException(Exception):  # pragma: no cover
    """Base Yardstick Exception.

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    Based on NeutronException class.
    """
    message = "An unknown exception occurred."

    def __init__(self, **kwargs):
        try:
            super(YardstickException, self).__init__(self.message % kwargs)
            self.msg = self.message % kwargs
        except Exception: # pylint: disable=W0703
            with excutils.save_and_reraise_exception() as ctxt:
                ctxt.reraise = False
                # At least get the core message out if something happened
                super(YardstickException, self).__init__(self.message)

    def __str__(self):
        return self.msg


class YardstickBannedModuleImported(YardstickException):
    # pragma: no cover
    message = 'Module "%(module)s" cannnot be imported. Reason: "%(reason)s"'
