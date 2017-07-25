# Copyright 2015 Intel Corporation.
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
"""IResult interface definition.
"""

class IResults(object):
    """Abstract class defining an interface for gathering results
    """
    def print_results(self):
        """Prints gathered results to screen.
        """
        raise NotImplementedError("This class does not implement the" \
                                  " \"print_results\" function.")

    def get_results(self):
        """Returns gathered results as a list of dictionaries.

        Each list element represents one record of data.

        :return: Results dictionary
            - key: Column name
            - value: Column value.
        """
        raise NotImplementedError("This class does not implement the" \
                                  " \"get_results\" function.")
