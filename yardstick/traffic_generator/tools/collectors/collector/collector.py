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

"""Abstract "system metrics logger" model.
"""

class ICollector(object):
    """This is an abstract class for system metrics loggers.
    """

    def start(self):
        """Starts data collection. This method must be non-blocking.
        It means, that collector must be executed as a background process.

        Where implemented, this function should raise an exception on
        failure.
        """
        raise NotImplementedError('Please call an implementation.')

    def stop(self):
        """Stops data collection.

        Where implemented, this function should raise an exception on
        failure.
        """
        raise NotImplementedError('Please call an implementation.')

    def get_results(self):
        """Returns collected results.

        Where implemented, this function should raise an exception on
        failure.
        """
        raise NotImplementedError('Please call an implementation.')

    def print_results(self):
        """Logs collected results.

        Where implemented, this function should raise an exception on
        failure.
        """
        raise NotImplementedError('Please call an implementation.')

    def __enter__(self):
        """Starts up collection of statistics
        """
        self.start()

    def __exit__(self, type_, value, traceback):
        """Stops collection of statistics
        """
        self.stop()
