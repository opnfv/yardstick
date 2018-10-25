# Copyright (c) 2019 Viosoft Corporation
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

from yardstick.network_services.traffic_profile import base


class SipProfile(base.TrafficProfile):
    """ Sipp Traffic profile """

    def __init__(self, yaml_data):
        super(SipProfile, self).__init__(yaml_data)
        self.generator = None

    def execute_traffic(self, traffic_generator=None):
        if traffic_generator is not None and self.generator is None:
            self.generator = traffic_generator

    def is_ended(self):
        if self.generator is not None:
            return self.generator.is_ended()
        return False
