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
""" Generic HTTP profile used by different Traffic generators """

from __future__ import absolute_import

from yardstick.network_services.traffic_profile.base import TrafficProfile


class TrafficProfileGenericHTTP(TrafficProfile):
    """ This Class handles setup of generic http traffic profile """

    def __init__(self, TrafficProfile):
        super(TrafficProfileGenericHTTP, self).__init__(TrafficProfile)

    def execute(self, traffic_generator):
        ''' send run traffic for a selected traffic generator'''
        pass

    def _send_http_request(self, server, port, locator, **kwargs):
        ''' send http request for a given server, port '''
        pass
