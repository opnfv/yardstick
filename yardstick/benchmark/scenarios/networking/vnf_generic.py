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
""" NSPerf specific scenario definition """

from __future__ import absolute_import
import logging
import yaml

from yardstick.benchmark.scenarios import base
from yardstick.common.utils import import_modules_from_package, itersubclasses
from yardstick.network_services.collector.subscriber import Collector
from yardstick.network_services.vnf_generic import vnfdgen
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.traffic_profile.base import TrafficProfile

LOG = logging.getLogger(__name__)


class SSHError(Exception):
    """Class handles ssh connection error exception"""
    pass


class SSHTimeout(SSHError):
    """Class handles ssh connection timeout exception"""
    pass


class IncorrectConfig(Exception):
    """Class handles incorrect configuration during setup"""
    pass


class IncorrectSetup(Exception):
    """Class handles incorrect setup during setup"""
    pass


class NetworkServiceTestCase(base.Scenario):
    """Class handles Generic framework to do pre-deployment VNF &
       Network service testing  """

    __scenario_type__ = "NSPerf"

    def __init__(self, scenario_cfg, context_cfg):  # Yardstick API
        super(NetworkServiceTestCase, self).__init__()
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg

        # fixme: create schema to validate all fields have been provided
        with open(scenario_cfg["topology"]) as stream:
            self.topology = yaml.load(stream)["nsd:nsd-catalog"]["nsd"][0]
        self.vnfs = []
        self.collector = None
        self.traffic_profile = None

    @classmethod
    def _get_traffic_flow(cls, scenario_cfg):
        try:
            with open(scenario_cfg["traffic_options"]["flow"]) as fflow:
                flow = yaml.load(fflow)
        except (KeyError, IOError, OSError):
            flow = {}
        return flow

    @classmethod
    def _get_traffic_imix(cls, scenario_cfg):
        try:
            with open(scenario_cfg["traffic_options"]["imix"]) as fimix:
                imix = yaml.load(fimix)
        except (KeyError, IOError, OSError):
            imix = {}
        return imix

    @classmethod
    def _get_traffic_profile(cls, scenario_cfg, context_cfg):
        traffic_profile_tpl = ""
        private = {}
        public = {}
        try:
            with open(scenario_cfg["traffic_profile"]) as infile:
                traffic_profile_tpl = infile.read()

        except (KeyError, IOError, OSError):
            raise

        return [traffic_profile_tpl, private, public]

    def _fill_traffic_profile(self, scenario_cfg, context_cfg):
        traffic_profile = {}

        flow = self._get_traffic_flow(scenario_cfg)

        imix = self._get_traffic_imix(scenario_cfg)

        traffic_mapping, private, public = \
            self._get_traffic_profile(scenario_cfg, context_cfg)

        traffic_profile = vnfdgen.generate_vnfd(traffic_mapping,
                                                {"imix": imix, "flow": flow,
                                                 "private": private,
                                                 "public": public})

        return TrafficProfile.get(traffic_profile)

    @classmethod
    def _find_vnf_name_from_id(cls, topology, vnf_id):
        return next((vnfd["vnfd-id-ref"]
                     for vnfd in topology["constituent-vnfd"]
                     if vnf_id == vnfd["member-vnf-index"]), None)

    def _resolve_topology(self, context_cfg, topology):
        for vld in topology["vld"]:
            if len(vld["vnfd-connection-point-ref"]) > 2:
                raise IncorrectConfig("Topology file corrupted, "
                                      "too many endpoint for connection")

            node_0, node_1 = vld["vnfd-connection-point-ref"]

            node0 = self._find_vnf_name_from_id(topology,
                                                node_0["member-vnf-index-ref"])
            node1 = self._find_vnf_name_from_id(topology,
                                                node_1["member-vnf-index-ref"])

            if0 = node_0["vnfd-connection-point-ref"]
            if1 = node_1["vnfd-connection-point-ref"]

            try:
                nodes = context_cfg["nodes"]
                nodes[node0]["interfaces"][if0]["vld_id"] = vld["id"]
                nodes[node1]["interfaces"][if1]["vld_id"] = vld["id"]

                nodes[node0]["interfaces"][if0]["dst_mac"] = \
                    nodes[node1]["interfaces"][if1]["local_mac"]
                nodes[node0]["interfaces"][if0]["dst_ip"] = \
                    nodes[node1]["interfaces"][if1]["local_ip"]

                nodes[node1]["interfaces"][if1]["dst_mac"] = \
                    nodes[node0]["interfaces"][if0]["local_mac"]
                nodes[node1]["interfaces"][if1]["dst_ip"] = \
                    nodes[node0]["interfaces"][if0]["local_ip"]
            except KeyError:
                raise IncorrectConfig("Required interface not found,"
                                      "topology file corrupted")

    @classmethod
    def _find_list_index_from_vnf_idx(cls, topology, vnf_idx):
        return next((topology["constituent-vnfd"].index(vnfd)
                     for vnfd in topology["constituent-vnfd"]
                     if vnf_idx == vnfd["member-vnf-index"]), None)

    def _update_context_with_topology(self, context_cfg, topology):
        for idx in topology["constituent-vnfd"]:
            vnf_idx = idx["member-vnf-index"]
            nodes = context_cfg["nodes"]
            node = self._find_vnf_name_from_id(topology, vnf_idx)
            list_idx = self._find_list_index_from_vnf_idx(topology, vnf_idx)
            nodes[node].update(topology["constituent-vnfd"][list_idx])

    def map_topology_to_infrastructure(self, context_cfg, topology):
        """ This method should verify if the available resources defined in pod.yaml
        match the topology.yaml file.

        :param topology:
        :return: None. Side effect: context_cfg is updated
        """

        for node, node_dict in context_cfg["nodes"].items():
            for interface in node_dict["interfaces"]:
                network = node_dict["interfaces"][interface]
                keys = ["vpci", "local_ip", "netmask",
                        "local_mac", "driver", "dpdk_port_num"]
                missing = set(keys).difference(network)
                if missing:
                    raise IncorrectConfig("Require interface fields '%s' "
                                          "not found, topology file "
                                          "corrupted" % ', '.join(missing))

        # 3. Use topology file to find connections & resolve dest address
        self._resolve_topology(context_cfg, topology)
        self._update_context_with_topology(context_cfg, topology)

    @classmethod
    def get_vnf_impl(cls, vnf_model):
        """ Find the implementing class from vnf_model["vnf"]["name"] field

        :param vnf_model: dictionary containing a parsed vnfd
        :return: subclass of GenericVNF
        """
        import_modules_from_package(
            "yardstick.network_services.vnf_generic.vnf")
        expected_name = vnf_model['id']
        impl = (c for c in itersubclasses(GenericVNF)
                if c.__name__ == expected_name)
        try:
            return next(impl)
        except StopIteration:
            raise IncorrectConfig("No implementation for %s", expected_name)

    def load_vnf_models(self, context_cfg):
        """ Create VNF objects based on YAML descriptors

        :param context_cfg:
        :return:
        """
        vnfs = []
        for node in context_cfg["nodes"]:
            LOG.debug(context_cfg["nodes"][node])
            with open(context_cfg["nodes"][node]["VNF model"]) as stream:
                vnf_model = stream.read()
            vnfd = vnfdgen.generate_vnfd(vnf_model, context_cfg["nodes"][node])
            vnf_impl = self.get_vnf_impl(vnfd["vnfd:vnfd-catalog"]["vnfd"][0])
            vnf_instance = vnf_impl(vnfd["vnfd:vnfd-catalog"]["vnfd"][0])
            vnf_instance.name = node
            vnfs.append(vnf_instance)

        return vnfs

    def setup(self):
        """ Setup infrastructure, provission VNFs & start traffic

        :return:
        """

        # 1. Verify if infrastructure mapping can meet topology
        self.map_topology_to_infrastructure(self.context_cfg, self.topology)
        # 1a. Load VNF models
        self.vnfs = self.load_vnf_models(self.context_cfg)
        # 1b. Fill traffic profile with information from topology
        self.traffic_profile = self._fill_traffic_profile(self.scenario_cfg,
                                                          self.context_cfg)

        # 2. Provision VNFs
        try:
            for vnf in self.vnfs:
                LOG.info("Instantiating %s", vnf.name)
                vnf.instantiate(self.scenario_cfg, self.context_cfg)
        except RuntimeError:
            for vnf in self.vnfs:
                vnf.terminate()
            raise

        # 3. Run experiment
        # Start listeners first to avoid losing packets
        traffic_runners = [vnf for vnf in self.vnfs if vnf.runs_traffic]
        for traffic_gen in traffic_runners:
            traffic_gen.listen_traffic(self.traffic_profile)

        # register collector with yardstick for KPI collection.
        self.collector = Collector(self.vnfs, self.traffic_profile)
        self.collector.start()

        # Start the actual traffic
        for traffic_gen in traffic_runners:
            LOG.info("Starting traffic on %s", traffic_gen.name)
            traffic_gen.run_traffic(self.traffic_profile)

    def run(self, result):  # yardstick API
        """ Yardstick calls run() at intervals defined in the yaml and
            produces timestamped samples

        :param result: dictionary with results to update
        :return: None
        """

        for vnf in self.vnfs:
            # Result example:
            # {"VNF1: { "tput" : [1000, 999] }, "VNF2": { "latency": 100 }}
            LOG.debug("vnf")
            result.update(self.collector.get_kpi(vnf))

    def teardown(self):
        """ Stop the collector and terminate VNF & TG instance

        :return
        """

        self.collector.stop()
        for vnf in self.vnfs:
            LOG.info("Stopping %s", vnf.name)
            vnf.terminate()
