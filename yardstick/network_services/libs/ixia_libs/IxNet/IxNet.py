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

import os
import base64
import time
import sys 
import logging
import ipaddress
from config import IxConfig
from ether import IxEther
from frame_control import IxFrame
from ipv4 import IxIPv4
from ipv6 import IxIPv6
from load import IxLoad
from ports import IxPorts
from start import IxStart
from statistics import IxStats
from stop import IxStop
from tcp import Ixtcp
from udp import Ixudp

log = logging.getLogger(__name__)

class IxNextgen():
	def __init__(self):
                self.ixNet = None
                self._objRefs = dict()
                _cfg = None
                _logger = logging.getLogger(__name__)
                _params = None
                _bidir = None

        def is_ipv4orv6(self, ip):
            ret = 0 # invalid
            try:
                ipaddress.IPv4Address(ip)
                ret = 1 # ipv4
            except:
                try:
                        ipaddress.IPv6Address(ip)
                        ret = 2 # ipv4
                except:
                        print(ip, " is not valid")
            return ret


	# This routine will connect to a running automation server on a specified port
        def _connect(self, tg_cfg):
            ret = ""
            self._cfg = IxConfig()._get_config(tg_cfg)

	    sys.path.append(self._cfg["py_lib_path"])
	    import IxNetwork
            self.ixNet = IxNetwork.IxNet()
		
            ret = self.ixNet.connect(self._cfg['machine'],
                                    '-port',  str(self._cfg['port']),
                                    '-version', str(self._cfg['version']))
            return ret

	def ix_load_config(self, profile):
		IxLoad().load_ixia_config(self.ixNet, profile)

	def ix_assign_ports(self):
		IxPorts()._assign_ports(self.ixNet, self._cfg)

	def ix_update_frame(self, params):
		IxFrame()._setup_frame_properties(self.ixNet, params)

	def ix_update_ether(self, params):
		IxEther()._add_ethernet_header(self.ixNet, params)

	def ix_update_ipv4(self, params):
		if (self.is_ipv4orv6(params['public']['outer_l3']['srcip4']) == 2):
			IxIPv6()._add_ipv6_header(self.ixNet, params)
		else:
			IxIPv4()._add_ipv4_header(self.ixNet, params)

	def ix_update_udp(self, params):
		Ixudp()._add_udp_header(self.ixNet, params)

	def ix_update_tcp(self, params):
		Ixtcp()._add_tcp_header(self.ixNet, params)

	def ix_start_traffic(self):
		IxStart()._start_traffic(self.ixNet)

	def ix_stop_traffic(self):
		IxStop()._stop_traffic(self.ixNet)

	def ix_get_statistics(self):
		return IxStats()._get_statistics(self.ixNet)
