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

"""VSPERF TestPMD implementation
"""

import logging
import pexpect
from conf import settings
from src.dpdk import dpdk
from src.dpdk import TestPMDProcess
from tools.pkt_fwd.pkt_fwd import IPktFwd

_LOGGER = logging.getLogger(__name__)
_VSWITCHD_CONST_ARGS = ['--', '-i']
_TESTPMD_PVP_CONST_ARGS = ['--vdev', 'net_vhost0,iface=/tmp/dpdkvhostuser0',
                           '--vdev', 'net_vhost1,iface=/tmp/dpdkvhostuser1',]

class TestPMD(IPktFwd):
    """TestPMD implementation (only phy2phy deployment is supported)

    This is wrapper for functionality implemented in ${DPDK}/app/test-pmd.

    The method docstrings document only considerations specific to this
    implementation. For generic information of the nature of the methods,
    see the interface definition.
    """

    _logger = logging.getLogger()

    def __init__(self, guest=False):
        vswitchd_args = settings.getValue('VSWITCHD_DPDK_ARGS')

        # override socket-mem settings
        for tmp_arg in vswitchd_args:
            if tmp_arg.startswith('--socket-mem'):
                vswitchd_args.remove(tmp_arg)
        vswitchd_args += ['--socket-mem ' +
                          ','.join(settings.getValue('DPDK_SOCKET_MEM'))]

        if guest:
            vswitchd_args += _TESTPMD_PVP_CONST_ARGS
        vswitchd_args += _VSWITCHD_CONST_ARGS
        vswitchd_args += settings.getValue('TESTPMD_ARGS')

        # need to give mbufs a larger size for jumbo frames based on the setting
        if settings.getValue('VSWITCH_JUMBO_FRAMES_ENABLED'):
            vswitchd_args += ['--mbuf-size={}'.format(int(
                settings.getValue('VSWITCH_JUMBO_FRAMES_SIZE')) + 500)]

        self._nports = len(settings.getValue('NICS'))
        self._fwdmode = settings.getValue('TESTPMD_FWD_MODE')
        self._csum_layer = settings.getValue('TESTPMD_CSUM_LAYER')
        self._csum_calc = settings.getValue('TESTPMD_CSUM_CALC')
        self._csum_tunnel = settings.getValue('TESTPMD_CSUM_PARSE_TUNNEL')

        self._testpmd = TestPMDProcess(testpmd_args=vswitchd_args)

    def start(self):
        """See IPktFwd for general description

        Activates testpmd.
        """
        self._logger.info("Starting TestPMD...")
        dpdk.init()
        self._testpmd.start()
        self._logger.info("TestPMD...Started.")

        self._testpmd.send('set fwd {}'.format(self._fwdmode), 1)

        if settings.getValue('VSWITCH_JUMBO_FRAMES_ENABLED'):
            self._testpmd.send('port stop all', 1)  # ports must be stopped to set mtu
            self._testpmd.send('port config all max-pkt-len {}'.format(
                settings.getValue('VSWITCH_JUMBO_FRAMES_SIZE')), 1)
            self._testpmd.send('port start all', 1)

        for port in range(self._nports):
            self._testpmd.send('csum set {} {} {}'.format(
                self._csum_layer, self._csum_calc, port), 1)
            self._testpmd.send('csum parse_tunnel {} {}'.format(
                self._csum_tunnel, port), 1)

        self._testpmd.send('start', 1)

    def start_for_guest(self):
        """See IPktFwd for general description

        Activates testpmd for guest config
        """
        self._logger.info("Starting TestPMD for one guest...")
        dpdk.init()
        self._testpmd.start()
        self._logger.info("TestPMD...Started.")

        if settings.getValue('VSWITCH_JUMBO_FRAMES_ENABLED'):
            self._testpmd.send('port stop all', 1)  # ports must be stopped to set mtu
            self._testpmd.send('port config all max-pkt-len {}'.format(
                settings.getValue('VSWITCH_JUMBO_FRAMES_SIZE')), 1)
            # conflicting info if scatter needs to be enabled or not
            self._testpmd.send('port config all scatter on', 1)
            self._testpmd.send('port start all', 1)
            self._testpmd.wait(timeout=60)  # port startup can take a few seconds

        self._testpmd.send('set portlist 0,2,1,3', 1)
        self._testpmd.send('set fwd {}'.format(self._fwdmode), 1)

        self._testpmd.send('start', 1)

    def stop(self):
        """See IPktFwd for general description

        Kills testpmd.
        """
        try:
            self._testpmd.send('stop')
            self._testpmd.wait('Done.', 5)
            self._testpmd.send('quit', 2)
            self._testpmd.kill()
        except pexpect.EOF:
            pass
        dpdk.cleanup()

    # Method could be a function
    # pylint: disable=no-self-use
    def get_version(self):
        """
        Get product version
        :return: None
        """
        # No way to read TestPMD version
        return []
