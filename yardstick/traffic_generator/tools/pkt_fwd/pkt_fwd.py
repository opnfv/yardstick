# Copyright 2016-2017 Intel Corporation.
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
"""Abstract "packet forwarding" model.

This is an abstract class for packet forwarders.
"""

class IPktFwd(object):
    """Interface class that is implemented by specific classes
    of packet forwarders
    """

    def __enter__(self):
        """Start the packet forwarder.

        Provide a context manager interface to the packet forwarders.
        This simply calls the :func:`start` function.
        """
        return self.start()

    def __exit__(self, type_, value, traceback):
        """Stop the packet forwarder.

        Provide a context manager interface to the packet forwarders.
        This simply calls the :func:`stop` function.
        """
        self.stop()

    def start(self):
        """Start the packet forwarder.

        :returns: None
        """
        raise NotImplementedError('Please call an implementation.')

    def start_for_guest(self):
        """Start the packet forward for guest config

        :returns: None
        """

    def stop(self):
        """Stop the packet forwarder.

        :returns: None
        """
        raise NotImplementedError('Please call an implementation.')
