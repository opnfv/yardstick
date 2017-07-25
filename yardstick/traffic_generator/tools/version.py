# Copyright 2017 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generic class to hold sotware version information shown in the report
"""

class Version(object):
    """Container to keep software version details
    """
    def __init__(self, name, version, git_tag='NA'):
        """Create Version object with given data
        """
        self._version = {'name' : name, 'version' : version, 'git_tag' : git_tag}

    def set_value(self, key, value):
        """Upate given `key` by given `value`
        """
        self._version[key] = value

    def get(self):
        """Get content of version object
        """
        return self._version
