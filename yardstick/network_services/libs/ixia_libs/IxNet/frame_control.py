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


class IxFrame():
    def _setup_frame_properties(self, ixNet, params):
        items = ["configElement"]

        index = 0
        for key, value in params.items():
            weightedPairs = []
            weightedRangePairs = []
            param = value
            tis = ixNet.getList('/traffic', 'trafficItem')
            index += 1
            for index, ti in enumerate(tis):
                index = param['id']

                for idx, stream in enumerate(items):
                    ti = ixNet.remapIds(ti)[0]
                    ixNet.setMultiAttribute(
                        ti + '/{0}:'.format(stream) + str(index) +
                        '/transmissionControl',
                        '-type', '{0}'.format(param['traffic_type']),
                        '-duration', '{0}'.format(param['duration']))

                    ixNet.setMultiAttribute(ti + '/{0}:'.format(stream) +
                                            str(index) + '/frameRate',
                                            '-rate', param['iload'])
                    if param['outer_l2']['framesPerSecond'] is True:
                        ixNet.setMultiAttribute(ti + '/{0}:'.format(stream) +
                                                str(index) + '/frameRate',
                                                '-type', 'framesPerSecond')

                    for key, value in param['outer_l2']['framesize'].items():
                        pairs = []
                        if value != '0':
                            weightedPairs.append(
                                key.replace('B', '').replace('b', ''))
                            weightedPairs.append(value)
                            pairs.append(
                                key.replace('B', '').replace('b', ''))
                            pairs.append(
                                key.replace('B', '').replace('b', ''))
                            pairs.append(value)
                            weightedRangePairs.append(pairs)
                    ixNet.setMultiAttribute(ti + '/{0}:'.format(stream) +
                                            str(index) + '/frameSize',
                                            '-weightedPairs', weightedPairs,
                                            '-incrementFrom', '66',
                                            '-randomMin', '66',
                                            '-quadGaussian', [],
                                            '-weightedRangePairs',
                                            weightedRangePairs,
                                            '-type', 'weightedPairs',
                                            '-presetDistribution', 'cisco',
                                            '-incrementTo', '1518')

                    ixNet.commit()
