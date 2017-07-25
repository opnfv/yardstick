# Copyright 2016 Intel Corporation.
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

"""Packet forwarder controller for Physical to Physical deployment
"""

import logging
from conf import settings

class PktFwdController(object):
    """Packet forwarder controller for P2P deployment scenario.

    Attributes:
        _pktfwd_class: The packet forwarder class to be used.
        _pktfwd: The packet forwarder object controlled by this controller
    """
    def __init__(self, deployment, pktfwd_class):
        """Initializes up the prerequisites for the P2P deployment scenario.

        :vswitch_class: the vSwitch class to be used.
        """
        self._deployment = deployment
        self._logger = logging.getLogger(__name__)
        self._pktfwd_class = pktfwd_class
        self._pktfwd = pktfwd_class(guest=True if deployment == "pvp" and
                                    settings.getValue('VNF') != "QemuPciPassthrough" else False)
        self._logger.debug('Creation using ' + str(self._pktfwd_class))

    def setup(self):
        """Sets up the packet forwarder for p2p.
        """
        self._logger.debug('Setup using ' + str(self._pktfwd_class))

        try:
            self._pktfwd.start()
        except:
            self._pktfwd.stop()
            raise

    def get_vswitch(self):
        """See IVswitchController for description
        """
        return self._pktfwd

    def setup_for_guest(self):
        """Sets up the packet forwarder for pvp.
        """
        self._logger.debug('Setup using ' + str(self._pktfwd_class))

        try:
            self._pktfwd.start_for_guest()
        except:
            self._pktfwd.stop()
            raise

    def stop(self):
        """Tears down the packet forwarder created in setup().
        """
        self._logger.debug('Stop using ' + str(self._pktfwd_class))
        self._pktfwd.stop()

    def __enter__(self):
        if self._deployment.find("p2p") == 0:
            self.setup()
        elif self._deployment == "pvp" and settings.getValue('VNF') != "QemuPciPassthrough":
            self.setup_for_guest()

    def __exit__(self, type_, value, traceback):
        if self._deployment.find("p2p") == 0:
            self.stop()
        elif self._deployment == "pvp" and settings.getValue('VNF') != "QemuPciPassthrough":
            self.stop()

    def get_pktfwd(self):
        """Get the controlled packet forwarder

        :return: The controlled IPktFwd
        """
        return self._pktfwd

    def dump_vswitch_flows(self):
        """ Dumps flows from vswitch
        """
        raise NotImplementedError(
            "The PktFwdController does not implement the "
            "\"dump_vswitch_flows\" function.")
