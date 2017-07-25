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

"""Module with implementation of wrapper around the stress-ng tool
"""

import logging
from tools.load_gen.stress.stress import Stress

class StressNg(Stress):
    """Wrapper around stress-ng tool, which generates load based on
    testcase configuration parameter 'load'
    """
    _process_args = {
        'cmd': ['sudo', 'stress-ng'],
        'timeout': 5,
        'logfile': '/tmp/stress-ng.log',
        'expect': r'stress-ng: info:',
        'name': 'stress-ng'
    }
    _logger = logging.getLogger(__name__)

    def __init__(self, stress_config):
        super(StressNg, self).__init__(stress_config)
