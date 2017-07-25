# Copyright 2015-2017 Intel Corporation.
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

"""Functions for creating controller objects based on deployment or traffic
"""

from yardstick.traffic_generator.core.traffic_controller_rfc2544 import TrafficControllerRFC2544
from yardstick.traffic_generator.core.traffic_controller_rfc2889 import TrafficControllerRFC2889
from yardstick.traffic_generator.core.traffic_controller_rfc3511 import TrafficControllerRFC3511


def __init__():
    """Finds and loads all the modules required.

    Very similar code to load_trafficgens().
    """
    pass

def create_traffic(traffic_type, trafficgen_class):
    """Return a new IVTrafficController for the traffic type.

    The returned traffic controller has the given traffic type and traffic
    generator class.

    traffic_types: 'rfc2544_throughput'

    :param traffic_type: Name of traffic type
    :param trafficgen_class: Reference to traffic generator class to be used.
    :return: A new TrafficController
    """
    if traffic_type.lower().startswith('rfc2889'):
        return TrafficControllerRFC2889(trafficgen_class)
    elif traffic_type.lower().startswith('rfc2544'):
        return TrafficControllerRFC2544(trafficgen_class)
    else:
        return TrafficControllerRFC3511(trafficgen_class)
