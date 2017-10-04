# Copyright (c) 2016-2017 Intel Corporation
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


class SSHError(Exception):
    """Class handles ssh connection error exception"""
    pass


class SSHTimeout(SSHError):
    """Class handles ssh connection timeout exception"""
    pass


class IncorrectConfig(Exception):
    """Class handles incorrect configuration during setup"""
    pass


class IncorrectSetup(Exception):
    """Class handles incorrect setup during setup"""
    pass


class IncorrectNodeSetup(IncorrectSetup):
    """Class handles incorrect setup during setup"""
    pass


class ErrorClass(object):

    def __init__(self, *args, **kwargs):
        if 'test' not in kwargs:
            raise RuntimeError

    def __getattr__(self, item):
        raise AttributeError
