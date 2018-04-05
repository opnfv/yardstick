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
"""This module implements stub for publishing results in yardstick format."""
import logging

from yardstick.network_services.nfvi.resource import ResourceProfile
from yardstick.network_services.utils import get_nsb_option

LOG = logging.getLogger(__name__)


class Collector(object):
    """Class that handles dictionary of results in yardstick-plot format."""

    def __init__(self, vnfs):
        super(Collector, self).__init__()
        self.vnfs = vnfs

    def start(self):
        for vnf in self.vnfs:
            vnf.start_collect()

    def stop(self):
        for vnf in self.vnfs:
            vnf.stop_collect()

    def get_kpi(self):
        """Returns dictionary of results in yardstick-plot format

        :return:
        """
        results = {}
        for vnf in self.vnfs:
            # Result example:
            # {"VNF1: { "tput" : [1000, 999] }, "VNF2": { "latency": 100 }}
            LOG.debug("collect KPI for %s", vnf.name)
            results[vnf.name] = vnf.collect_kpi()

        return results
