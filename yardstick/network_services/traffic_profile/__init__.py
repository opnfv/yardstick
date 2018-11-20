# Copyright (c) 2018 Intel Corporation
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

import importlib


def register_modules():
    modules = [
        'yardstick.network_services.traffic_profile.trex_traffic_profile',
        'yardstick.network_services.traffic_profile.fixed',
        'yardstick.network_services.traffic_profile.http',
        'yardstick.network_services.traffic_profile.http_ixload',
        'yardstick.network_services.traffic_profile.ixia_rfc2544',
        'yardstick.network_services.traffic_profile.prox_ACL',
        'yardstick.network_services.traffic_profile.prox_irq',
        'yardstick.network_services.traffic_profile.prox_binsearch',
        'yardstick.network_services.traffic_profile.prox_profile',
        'yardstick.network_services.traffic_profile.prox_ramp',
        'yardstick.network_services.traffic_profile.rfc2544',
        'yardstick.network_services.traffic_profile.pktgen',
        'yardstick.network_services.traffic_profile.landslide_profile',
        'yardstick.network_services.traffic_profile.vpp_rfc2544',
    ]

    for module in modules:
        importlib.import_module(module)
