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


class IxLoad():
    def _clear_ixia_config(self, ixNet):
        ixNet.execute('newConfig')

    def _load_ixia_profile(self, ixNet, profile):
        ixNet.execute('loadConfig', ixNet.readFrom(profile))

    def load_ixia_config(self, ixNet, profile):
        self._clear_ixia_config(ixNet)
        self._load_ixia_profile(ixNet, profile)
