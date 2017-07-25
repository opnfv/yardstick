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

"""Various helper functions
"""

import os
import logging
import glob
import shutil
from yardstick.traffic_generator.conf import settings as S

MAX_L4_FLOWS = 65536

def check_traffic(traffic):
    """Check traffic definition and correct it if possible.
    """
    return traffic
    # check if requested networking layers make sense
    if traffic['l4']['enabled']:
        if not traffic['l3']['enabled']:
            raise RuntimeError('TRAFFIC misconfiguration: l3 must be enabled '
                               'if l4 is enabled.')

    # check if multistream configuration makes sense
    if traffic['multistream']:
        if traffic['stream_type'] == 'L3':
            if not traffic['l3']['enabled']:
                raise RuntimeError('TRAFFIC misconfiguration: l3 must be '
                                   'enabled if l3 streams are requested.')
        if traffic['stream_type'] == 'L4':
            if not traffic['l4']['enabled']:
                raise RuntimeError('TRAFFIC misconfiguration: l4 must be '
                                   'enabled if l4 streams are requested.')

            # in case of UDP ports we have only 65536 (0-65535) unique options
            if traffic['multistream'] > MAX_L4_FLOWS:
                logging.getLogger().warning(
                    'Requested amount of L4 flows %s is bigger than number of '
                    'transport protocol ports. It was set to %s.',
                    traffic['multistream'], MAX_L4_FLOWS)
                traffic['multistream'] = MAX_L4_FLOWS

    return traffic
