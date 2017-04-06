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


class IxEther():
    def _add_ethernet_header(self, ixNet, params):
        tis = ixNet.getList('/traffic', 'trafficItem')
        for index, ti in enumerate(tis):
            eps = ixNet.getList(ti, "configElement")
            for idx, ep in enumerate(eps):
                value = {}
                for k, v in params.items():
                    if str(v['id']) == str(idx + 1):
                        value = v
                        break
                if "outer_l2" not in list(value.keys()):
                    continue
                l2 = value['outer_l2']
                srcmac = l2['srcmac']
                dstmac = l2['dstmac']
                for ip in ixNet.getList(ep, "stack"):
                    for ether in ixNet.getList(ip, "field"):
                        if "ethernet.header.destinationAddress" in ether:
                            ixNet.setMultiAttribute(
                                ether,
                                '-singleValue', '{0}'.format(dstmac),
                                '-fieldValue', '{0}'.format(dstmac),
                                '-valueType', 'singleValue')
                        if "ethernet.header.sourceAddress" in ether:
                            ixNet.setMultiAttribute(
                                ether,
                                '-singleValue', '{0}'.format(srcmac),
                                '-fieldValue', '{0}'.format(srcmac),
                                '-valueType', 'singleValue')
        ixNet.commit()
