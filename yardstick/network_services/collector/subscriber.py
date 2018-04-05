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

    def __init__(self, vnfs, nodes, traffic_profile, timeout=3600):
        super(Collector, self).__init__()
        self.traffic_profile = traffic_profile
        self.vnfs = vnfs
        self.nodes = nodes
        self.timeout = timeout
        self.bin_path = get_nsb_option('bin_path', '')
        self.resource_profiles = {node_name: ResourceProfile.make_from_node(node, self.timeout)
                                  for node_name, node in self.nodes.items()
                                  if node.get("collectd")}

    def start(self):
        """Nothing to do, yet"""
        for resource in self.resource_profiles.values():
            resource.initiate_systemagent(self.bin_path)
            resource.start()
            resource.amqp_process_for_nfvi_kpi()

        for vnf in self.vnfs:
            vnf.start_collect()

    def stop(self):
        """Nothing to do, yet"""
        for resource in self.resource_profiles.values():
            resource.stop()

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

        for node_name, resource in self.resource_profiles.items():
            # Result example:
            # {"VNF1: { "tput" : [1000, 999] }, "VNF2": { "latency": 100 }}
            LOG.debug("collect KPI for %s", node_name)
            if resource.check_if_system_agent_running("collectd")[0] != 0:
                continue

            try:
                results[node_name] = {"core": resource.amqp_collect_nfvi_kpi()}
                LOG.debug("%s collect KPIs %s", node_name, results[node_name]['core'])
            # NOTE(elfoley): catch a more specific error
            except Exception as exc:  # pylint: disable=broad-except
                LOG.exception(exc)
        return results
