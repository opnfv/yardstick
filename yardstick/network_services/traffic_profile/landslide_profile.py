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
""" Spirent Landslide traffic profile definitions """

from __future__ import absolute_import

from yardstick.network_services.traffic_profile.base import TrafficProfile


class LandslideProfile(TrafficProfile):
    """
    This traffic profile handles attributes of Landslide data stream
    """

    def __init__(self, tp_config):
        super(LandslideProfile, self).__init__(tp_config)

        # for backward compatibility support dict and list of dicts
        if isinstance(tp_config["dmf_config"], dict):
            self.dmf_config = [tp_config["dmf_config"]]
        else:
            self.dmf_config = tp_config["dmf_config"]

    def execute(self, traffic_generator):
        pass

    def update_dmf(self, options):
        if 'dmf' in options:
            if isinstance(options['dmf'], dict):
                _dmfs = [options['dmf']]
            else:
                _dmfs = options['dmf']

            for index, _dmf in enumerate(_dmfs):
                try:
                    self.dmf_config[index].update(_dmf)
                except IndexError:
                    pass
