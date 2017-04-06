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

from __future__ import absolute_import
import logging

log = logging.getLogger(__name__)


class IxPorts():

    def _assign_ports(self, ixNet, _cfg):
        vports = ixNet.getList(ixNet.getRoot(), 'vport')
        ports = \
            [(_cfg['chassis'], _cfg['card1'], _cfg['port1']),
             (_cfg['chassis'], _cfg['card2'], _cfg['port2'])]
        ixNet.execute('assignPorts', ports, [], ixNet.getList("/", "vport"),
                      True)
        ixNet.commit()

        for vport in vports:
            if ixNet.getAttribute(vport, '-state') != 'up':
                log.error("Both thr ports are down...")
