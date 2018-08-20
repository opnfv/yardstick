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

import re

from yardstick.common import exceptions
from yardstick.common import utils


class TrafficProfileConfig(object):
    """Class to contain the TrafficProfile class information

    This object will parse and validate the traffic profile information.
    """
    DEFAULT_SCHEMA = 'nsb:traffic_profile:0.1'
    DEFAULT_FRAME_RATE = '100'
    DEFAULT_DURATION = 30
    RATE_FPS = 'fps'
    RATE_PERCENTAGE = '%'
    RATE_REGEX = re.compile(r'([0-9]*\.[0-9]+|[0-9]+)\s*(fps|%)*(.*)')

    def __init__(self, tp_config):
        self.schema = tp_config.get('schema', self.DEFAULT_SCHEMA)
        self.name = tp_config.get('name')
        self.description = tp_config.get('description')
        tprofile = tp_config['traffic_profile']
        self.traffic_type = tprofile.get('traffic_type')
        self.frame_rate, self.rate_unit = self._parse_rate(
            tprofile.get('frame_rate', self.DEFAULT_FRAME_RATE))
        self.test_precision = tprofile.get('test_precision')
        self.packet_sizes = tprofile.get('packet_sizes')
        self.duration = tprofile.get('duration', self.DEFAULT_DURATION)
        self.lower_bound = tprofile.get('lower_bound')
        self.upper_bound = tprofile.get('upper_bound')
        self.step_interval = tprofile.get('step_interval')
        self.enable_latency = tprofile.get('enable_latency', False)

    def _parse_rate(self, rate):
        """Parse traffic profile rate

        The line rate can be defined in fps or percentage over the maximum line
        rate:
          - frame_rate = 5000 (by default, unit is 'fps')
          - frame_rate = 5000fps
          - frame_rate = 25%

        :param rate: (string, int) line rate in fps or %
        :return: (tuple: int, string) line rate number and unit
        """
        match = self.RATE_REGEX.match(str(rate))
        if not match:
            exceptions.TrafficProfileRate()
        rate = float(match.group(1))
        unit = match.group(2) if match.group(2) else self.RATE_FPS
        if match.group(3):
            raise exceptions.TrafficProfileRate()
        return rate, unit


class TrafficProfile(object):
    """
    This class defines the behavior

    """
    UPLINK = "uplink"
    DOWNLINK = "downlink"

    @staticmethod
    def get(tp_config):
        """Get the traffic profile instance for the given traffic type

        :param tp_config: loaded YAML file
        :return:
        """
        profile_class = tp_config["traffic_profile"]["traffic_type"]
        try:
            return next(c for c in utils.itersubclasses(TrafficProfile)
                        if c.__name__ == profile_class)(tp_config)
        except StopIteration:
            raise exceptions.TrafficProfileNotImplemented(
                profile_class=profile_class)

    def __init__(self, tp_config):
        # e.g. RFC2544 start_ip, stop_ip, drop_rate,
        # IMIX = {"10K": 0.1, "100M": 0.5}
        self.params = tp_config
        self.config = TrafficProfileConfig(tp_config)

    def execute_traffic(self, traffic_generator, **kawrgs):
        """ This methods defines the behavior of the traffic generator.
        It will be called in a loop until the traffic generator exits.

        :param traffic_generator: TrafficGen instance
        :return: None
        """
        raise NotImplementedError()


class DummyProfile(TrafficProfile):
    """
    This is an empty TrafficProfile implementation - if it is used,
    the traffic will be completely handled by the Traffic Generator
    implementation with no regard for the Traffic Profile.
    """
    def execute(self, traffic_generator):
        pass
