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
""" Base class for the generic traffic profile implementation """

from __future__ import absolute_import
from yardstick.common.utils import import_modules_from_package, itersubclasses


class TrafficProfile(object):
    """
    This class defines the behavior

    """

    @staticmethod
    def get(tp_config):
        """Get the traffic profile instance for the given traffic type

        :param tp_config: loaded YAML file
        :return:
        """
        profile_class = tp_config["traffic_profile"]["traffic_type"]
        import_modules_from_package(
            "yardstick.network_services.traffic_profile")
        try:
            return next(c for c in itersubclasses(TrafficProfile)
                        if c.__name__ == profile_class)(tp_config)
        except StopIteration:
            raise RuntimeError("No implementation for %s", profile_class)

    def __init__(self, tp_config):
        # e.g. RFC2544 start_ip, stop_ip, drop_rate,
        # IMIX = {"10K": 0.1, "100M": 0.5}
        self.params = tp_config

    def execute(self, traffic_generator):
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
