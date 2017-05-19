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

log = logging.getLogger(__name__)

class IxStart():
	  def _start_traffic(self, ixNet):
		tis = ixNet.getList('/traffic', 'trafficItem')
                for ti in tis:
                        ixNet.execute('generate', [ti])
                        ixNet.execute('apply', '/traffic')
                        ixNet.execute('start', '/traffic')
