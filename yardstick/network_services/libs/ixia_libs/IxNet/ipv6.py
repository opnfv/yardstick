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


class IxIPv6():

    def _add_ipv6_header(self, ixNet, params):
        tis = ixNet.getList('/traffic', 'trafficItem')
        for ti in tis:
            eps = ixNet.getList(ti, "configElement")
            for ep in eps:
                if eps.index(ep) == 0:
                    value = params["private"]
                    index = [1, '256', '2048']
                else:
                    value = params["public"]
                    index = [2, '2048', '256']
                l3 = value['outer_l3']
                srcip4 = l3['srcip4']
                dstip4 = l3['dstip4']
                for ip in ixNet.getList(ep, "stack"):
                    for ipv6 in ixNet.getList(ip, "field"):
                        if "srcIP" in ipv6:
                            ixNet.setMultiAttribute(
                                ipv6,
                                '-seed', str(index[1]),
                                '-fixedBits', '{0}'.format(srcip4),
                                '-randomMask', '0:0:0:0:0:0:0:ff',
                                '-valueType', 'random',
                                '-countValue', '{0}'.format(l3['count']))
                        if "dstIP" in ipv6:
                            ixNet.setMultiAttribute(
                                ipv6,
                                '-seed', str(index[2]),
                                '-fixedBits', '{0}'.format(dstip4),
                                '-randomMask', '0:0:0:0:0:0:0:ff',
                                '-valueType', 'random',
                                '-countValue', '{0}'.format(l3['count']))
        ixNet.commit()
