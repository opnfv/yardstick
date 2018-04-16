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

import copy
import logging
import time

import ipaddress
from itertools import chain
import os
import sys

import six
import yaml

from yardstick.benchmark.scenarios import base as scenario_base
from yardstick.error import IncorrectConfig
from yardstick.common.constants import LOG_DIR
from yardstick.common.process import terminate_children
from yardstick.common import utils
from yardstick.network_services.collector.subscriber import Collector
from yardstick.network_services.vnf_generic import vnfdgen
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services import traffic_profile
from yardstick.network_services.traffic_profile import base as tprofile_base
from yardstick.network_services.utils import get_nsb_option
from yardstick import ssh

traffic_profile.register_modules()


LOG = logging.getLogger(__name__)


class NetworkServiceTestCase(scenario_base.Scenario):
    """Class handles Generic framework to do pre-deployment VNF &
       Network service testing  """

    __scenario_type__ = "NSPerf"

    def __init__(self, scenario_cfg, context_cfg):  # Yardstick API
        super(NetworkServiceTestCase, self).__init__()
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg

        self._render_topology()
        self.vnfs = []
        self.collector = None
        self.traffic_profile = None
        self.node_netdevs = {}
        self.bin_path = get_nsb_option('bin_path', '')

    def _get_ip_flow_range(self, ip_start_range):

        # IP range is specified as 'x.x.x.x-y.y.y.y'
        if isinstance(ip_start_range, six.string_types):
            return ip_start_range

        node_name, range_or_interface = next(iter(ip_start_range.items()), (None, '0.0.0.0'))
        if node_name is None:
            # we are manually specifying the range
            ip_addr_range = range_or_interface
        else:
            node = self.context_cfg["nodes"].get(node_name, {})
            try:
                # the ip_range is the interface name
                interface = node.get("interfaces", {})[range_or_interface]
            except KeyError:
                ip = "0.0.0.0"
                mask = "255.255.255.0"
            else:
                ip = interface["local_ip"]
                # we can't default these values, they must both exist to be valid
                mask = interface["netmask"]

            ipaddr = ipaddress.ip_network(six.text_type('{}/{}'.format(ip, mask)), strict=False)
            hosts = list(ipaddr.hosts())
            if len(hosts) > 2:
                # skip the first host in case of gateway
                ip_addr_range = "{}-{}".format(hosts[1], hosts[-1])
            else:
                LOG.warning("Only single IP in range %s", ipaddr)
                # fall back to single IP range
                ip_addr_range = ip
        return ip_addr_range

    def _get_traffic_flow(self):
        flow = {}
        try:
            # TODO: should be .0  or .1 so we can use list
            # but this also roughly matches uplink_0, downlink_0
            fflow = self.scenario_cfg["options"]["flow"]
            for index, src in enumerate(fflow.get("src_ip", [])):
                flow["src_ip_{}".format(index)] = self._get_ip_flow_range(src)

            for index, dst in enumerate(fflow.get("dst_ip", [])):
                flow["dst_ip_{}".format(index)] = self._get_ip_flow_range(dst)

            for index, publicip in enumerate(fflow.get("public_ip", [])):
                flow["public_ip_{}".format(index)] = publicip

            for index, src_port in enumerate(fflow.get("src_port", [])):
                flow["src_port_{}".format(index)] = src_port

            for index, dst_port in enumerate(fflow.get("dst_port", [])):
                flow["dst_port_{}".format(index)] = dst_port

            flow["count"] = fflow["count"]
        except KeyError:
            flow = {}
        return {"flow": flow}

    def _get_traffic_imix(self):
        try:
            imix = {"imix": self.scenario_cfg['options']['framesize']}
        except KeyError:
            imix = {}
        return imix

    def _get_traffic_profile(self):
        profile = self.scenario_cfg["traffic_profile"]
        path = self.scenario_cfg["task_path"]
        with utils.open_relative_file(profile, path) as infile:
            return infile.read()

    def _get_topology(self):
        topology = self.scenario_cfg["topology"]
        path = self.scenario_cfg["task_path"]
        with utils.open_relative_file(topology, path) as infile:
            return infile.read()

    def _fill_traffic_profile(self):
        tprofile = self._get_traffic_profile()
        extra_args = self.scenario_cfg.get('extra_args', {})
        tprofile_data = {
            'flow': self._get_traffic_flow(),
            'imix': self._get_traffic_imix(),
            tprofile_base.TrafficProfile.UPLINK: {},
            tprofile_base.TrafficProfile.DOWNLINK: {},
            'extra_args': extra_args
        }

        traffic_vnfd = vnfdgen.generate_vnfd(tprofile, tprofile_data)
        self.traffic_profile = tprofile_base.TrafficProfile.get(traffic_vnfd)

    def _render_topology(self):
        topology = self._get_topology()
        topology_args = self.scenario_cfg.get('extra_args', {})
        topolgy_data = {
            'extra_args': topology_args
        }
        topology_yaml = vnfdgen.generate_vnfd(topology, topolgy_data)
        self.topology = topology_yaml["nsd:nsd-catalog"]["nsd"][0]

    def _find_vnf_name_from_id(self, vnf_id):
        return next((vnfd["vnfd-id-ref"]
                     for vnfd in self.topology["constituent-vnfd"]
                     if vnf_id == vnfd["member-vnf-index"]), None)

    def _find_vnfd_from_vnf_idx(self, vnf_id):
        return next((vnfd
                     for vnfd in self.topology["constituent-vnfd"]
                     if vnf_id == vnfd["member-vnf-index"]), None)

    @staticmethod
    def find_node_if(nodes, name, if_name, vld_id):
        try:
            # check for xe0, xe1
            intf = nodes[name]["interfaces"][if_name]
        except KeyError:
            # if not xe0, then maybe vld_id,  uplink_0, downlink_0
            # pop it and re-insert with the correct name from topology
            intf = nodes[name]["interfaces"].pop(vld_id)
            nodes[name]["interfaces"][if_name] = intf
        return intf

    def _resolve_topology(self):
        for vld in self.topology["vld"]:
            try:
                node0_data, node1_data = vld["vnfd-connection-point-ref"]
            except (ValueError, TypeError):
                raise IncorrectConfig("Topology file corrupted, "
                                      "wrong endpoint count for connection")

            node0_name = self._find_vnf_name_from_id(node0_data["member-vnf-index-ref"])
            node1_name = self._find_vnf_name_from_id(node1_data["member-vnf-index-ref"])

            node0_if_name = node0_data["vnfd-connection-point-ref"]
            node1_if_name = node1_data["vnfd-connection-point-ref"]

            try:
                nodes = self.context_cfg["nodes"]
                node0_if = self.find_node_if(nodes, node0_name, node0_if_name, vld["id"])
                node1_if = self.find_node_if(nodes, node1_name, node1_if_name, vld["id"])

                # names so we can do reverse lookups
                node0_if["ifname"] = node0_if_name
                node1_if["ifname"] = node1_if_name

                node0_if["node_name"] = node0_name
                node1_if["node_name"] = node1_name

                node0_if["vld_id"] = vld["id"]
                node1_if["vld_id"] = vld["id"]

                # set peer name
                node0_if["peer_name"] = node1_name
                node1_if["peer_name"] = node0_name

                # set peer interface name
                node0_if["peer_ifname"] = node1_if_name
                node1_if["peer_ifname"] = node0_if_name

                # just load the network
                vld_networks = {n.get('vld_id', name): n for name, n in
                                self.context_cfg["networks"].items()}

                node0_if["network"] = vld_networks.get(vld["id"], {})
                node1_if["network"] = vld_networks.get(vld["id"], {})

                node0_if["dst_mac"] = node1_if["local_mac"]
                node0_if["dst_ip"] = node1_if["local_ip"]

                node1_if["dst_mac"] = node0_if["local_mac"]
                node1_if["dst_ip"] = node0_if["local_ip"]

            except KeyError:
                LOG.exception("")
                raise IncorrectConfig("Required interface not found, "
                                      "topology file corrupted")

        for vld in self.topology['vld']:
            try:
                node0_data, node1_data = vld["vnfd-connection-point-ref"]
            except (ValueError, TypeError):
                raise IncorrectConfig("Topology file corrupted, "
                                      "wrong endpoint count for connection")

            node0_name = self._find_vnf_name_from_id(node0_data["member-vnf-index-ref"])
            node1_name = self._find_vnf_name_from_id(node1_data["member-vnf-index-ref"])

            node0_if_name = node0_data["vnfd-connection-point-ref"]
            node1_if_name = node1_data["vnfd-connection-point-ref"]

            nodes = self.context_cfg["nodes"]
            node0_if = self.find_node_if(nodes, node0_name, node0_if_name, vld["id"])
            node1_if = self.find_node_if(nodes, node1_name, node1_if_name, vld["id"])

            # add peer interface dict, but remove circular link
            # TODO: don't waste memory
            node0_copy = node0_if.copy()
            node1_copy = node1_if.copy()
            node0_if["peer_intf"] = node1_copy
            node1_if["peer_intf"] = node0_copy

    def _update_context_with_topology(self):
        for vnfd in self.topology["constituent-vnfd"]:
            vnf_idx = vnfd["member-vnf-index"]
            vnf_name = self._find_vnf_name_from_id(vnf_idx)
            vnfd = self._find_vnfd_from_vnf_idx(vnf_idx)
            self.context_cfg["nodes"][vnf_name].update(vnfd)

    def _generate_pod_yaml(self):
        context_yaml = os.path.join(LOG_DIR, "pod-{}.yaml".format(self.scenario_cfg['task_id']))
        # convert OrderedDict to a list
        # pod.yaml nodes is a list
        nodes = [self._serialize_node(node) for node in self.context_cfg["nodes"].values()]
        pod_dict = {
            "nodes": nodes,
            "networks": self.context_cfg["networks"]
        }
        with open(context_yaml, "w") as context_out:
            yaml.safe_dump(pod_dict, context_out, default_flow_style=False,
                           explicit_start=True)

    @staticmethod
    def _serialize_node(node):
        new_node = copy.deepcopy(node)
        # name field is required
        # remove context suffix
        new_node["name"] = node['name'].split('.')[0]
        try:
            new_node["pkey"] = ssh.convert_key_to_str(node["pkey"])
        except KeyError:
            pass
        return new_node

    def map_topology_to_infrastructure(self):
        """ This method should verify if the available resources defined in pod.yaml
        match the topology.yaml file.

        :return: None. Side effect: context_cfg is updated
        """
        # 3. Use topology file to find connections & resolve dest address
        self._resolve_topology()
        self._update_context_with_topology()

    @classmethod
    def get_vnf_impl(cls, vnf_model_id):
        """ Find the implementing class from vnf_model["vnf"]["name"] field

        :param vnf_model_id: parsed vnfd model ID field
        :return: subclass of GenericVNF
        """
        utils.import_modules_from_package(
            "yardstick.network_services.vnf_generic.vnf")
        expected_name = vnf_model_id
        classes_found = []

        def impl():
            for name, class_ in ((c.__name__, c) for c in
                                 utils.itersubclasses(GenericVNF)):
                if name == expected_name:
                    yield class_
                classes_found.append(name)

        try:
            return next(impl())
        except StopIteration:
            pass

        raise IncorrectConfig("No implementation for %s found in %s" %
                              (expected_name, classes_found))

    @staticmethod
    def create_interfaces_from_node(vnfd, node):
        ext_intfs = vnfd["vdu"][0]["external-interface"] = []
        # have to sort so xe0 goes first
        for intf_name, intf in sorted(node['interfaces'].items()):
            # only interfaces with vld_id are added.
            # Thus there are two layers of filters, only intefaces with vld_id
            # show up in interfaces, and only interfaces with traffic profiles
            # are used by the generators
            if intf.get('vld_id'):
                # force dpkd_port_num to int so we can do reverse lookup
                try:
                    intf['dpdk_port_num'] = int(intf['dpdk_port_num'])
                except KeyError:
                    pass
                ext_intf = {
                    "name": intf_name,
                    "virtual-interface": intf,
                    "vnfd-connection-point-ref": intf_name,
                }
                ext_intfs.append(ext_intf)

    def load_vnf_models(self, scenario_cfg=None, context_cfg=None):
        """ Create VNF objects based on YAML descriptors

        :param scenario_cfg:
        :type scenario_cfg:
        :param context_cfg:
        :return:
        """
        trex_lib_path = get_nsb_option('trex_client_lib')
        sys.path[:] = list(chain([trex_lib_path], (x for x in sys.path if x != trex_lib_path)))

        if scenario_cfg is None:
            scenario_cfg = self.scenario_cfg

        if context_cfg is None:
            context_cfg = self.context_cfg

        vnfs = []
        # we assume OrderedDict for consistency in instantiation
        for node_name, node in context_cfg["nodes"].items():
            LOG.debug(node)
            try:
                file_name = node["VNF model"]
            except KeyError:
                LOG.debug("no model for %s, skipping", node_name)
                continue
            file_path = scenario_cfg['task_path']
            with utils.open_relative_file(file_name, file_path) as stream:
                vnf_model = stream.read()
            vnfd = vnfdgen.generate_vnfd(vnf_model, node)
            # TODO: here add extra context_cfg["nodes"] regardless of template
            vnfd = vnfd["vnfd:vnfd-catalog"]["vnfd"][0]
            # force inject pkey if it exists
            # we want to standardize Heat using pkey as a string so we don't rely
            # on the filesystem
            try:
                vnfd['mgmt-interface']['pkey'] = node['pkey']
            except KeyError:
                pass
            self.create_interfaces_from_node(vnfd, node)
            vnf_impl = self.get_vnf_impl(vnfd['id'])
            vnf_instance = vnf_impl(node_name, vnfd)
            vnfs.append(vnf_instance)

        self.vnfs = vnfs
        return vnfs

    def setup(self):
        """Setup infrastructure, provision VNFs & start traffic

        :return: (list of int) PIDs of the processes controlling the traffic
                 generators
        """
        # 1. Verify if infrastructure mapping can meet topology
        self.map_topology_to_infrastructure()
        # 1a. Load VNF models
        self.load_vnf_models()
        # 1b. Fill traffic profile with information from topology
        self._fill_traffic_profile()

        # 2. Provision VNFs

        # link events will cause VNF application to exit
        # so we should start traffic runners before VNFs
        traffic_runners = [vnf for vnf in self.vnfs if vnf.runs_traffic]
        non_traffic_runners = [vnf for vnf in self.vnfs if not vnf.runs_traffic]
        try:
            for vnf in chain(traffic_runners, non_traffic_runners):
                LOG.info("Instantiating %s", vnf.name)
                vnf.instantiate(self.scenario_cfg, self.context_cfg)
                LOG.info("Waiting for %s to instantiate", vnf.name)
                vnf.wait_for_instantiate()
        except:
            LOG.exception("")
            for vnf in self.vnfs:
                vnf.terminate()
            raise

        # we have to generate pod.yaml here after VNF has probed so we know vpci and driver
        self._generate_pod_yaml()

        # 3. Run experiment
        # Start listeners first to avoid losing packets
        for traffic_gen in traffic_runners:
            traffic_gen.listen_traffic(self.traffic_profile)

        # register collector with yardstick for KPI collection.
        self.collector = Collector(self.vnfs, self.context_cfg["nodes"], self.traffic_profile)
        self.collector.start()

        # Start the actual traffic
        tg_pids = []
        for traffic_gen in traffic_runners:
            LOG.info("Starting traffic on %s", traffic_gen.name)
            tg_pids.append(traffic_gen.run_traffic(self.traffic_profile))

        return tg_pids

    def run(self, result):  # yardstick API
        """ Yardstick calls run() at intervals defined in the yaml and
            produces timestamped samples

        :param result: dictionary with results to update
        :return: None
        """

        # this is the only method that is check from the runner
        # so if we have any fatal error it must be raised via these methods
        # otherwise we will not terminate

        result.update(self.collector.get_kpi())

    def teardown(self):
        """ Stop the collector and terminate VNF & TG instance

        :return
        """

        try:
            try:
                self.collector.stop()
                for vnf in self.vnfs:
                    LOG.info("Stopping %s", vnf.name)
                    vnf.terminate()
                LOG.debug("all VNFs terminated: %s", ", ".join(vnf.name for vnf in self.vnfs))
            finally:
                terminate_children()
        except Exception:
            # catch any exception in teardown and convert to simple exception
            # never pass exceptions back to multiprocessing, because some exceptions can
            # be unpicklable
            # https://bugs.python.org/issue9400
            LOG.exception("")
            raise RuntimeError("Error in teardown")

    def pre_run_wait_time(self, time_seconds):
        """Time waited before executing the run method"""
        time.sleep(time_seconds)

    def post_run_wait_time(self, time_seconds):
        """Time waited after executing the run method"""
        pass
