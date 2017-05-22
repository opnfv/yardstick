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

import errno
import os

import re
from operator import itemgetter
from collections import defaultdict

import yaml

from yardstick.benchmark.scenarios import base
from yardstick.common.utils import import_modules_from_package, itersubclasses
from yardstick.network_services.collector.subscriber import Collector
from yardstick.network_services.vnf_generic import vnfdgen
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.traffic_profile.base import TrafficProfile
from yardstick import ssh

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


class SshManager(object):
    def __init__(self, node):
        super(SshManager, self).__init__()
        self.node = node
        self.conn = None

    def __enter__(self):
        """
        args -> network device mappings
        returns -> ssh connection ready to be used
        """
        try:
            self.conn = ssh.SSH.from_node(self.node)
            self.conn.wait()
        except SSHError as error:
            LOG.info("connect failed to %s, due to %s", self.node["ip"], error)
        # self.conn defaults to None
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()


def open_relative_file(path, task_path):
    try:
        return open(path)
    except IOError as e:
        if e.errno == errno.ENOENT:
            return open(os.path.join(task_path, path))
        raise


class NetworkServiceTestCase(base.Scenario):
    """Class handles Generic framework to do pre-deployment VNF &
       Network service testing  """

    __scenario_type__ = "NSPerf"

    def __init__(self, scenario_cfg, context_cfg):  # Yardstick API
        super(NetworkServiceTestCase, self).__init__()
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg

        # fixme: create schema to validate all fields have been provided
        with open_relative_file(scenario_cfg["topology"],
                                scenario_cfg['task_path']) as stream:
            topology_yaml = yaml.load(stream)

        self.topology = topology_yaml["nsd:nsd-catalog"]["nsd"][0]
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
            with open_relative_file(scenario_cfg["traffic_profile"],
                                    scenario_cfg["task_path"]) as infile:
                traffic_profile_tpl = infile.read()

        except (KeyError, IOError, OSError):
            raise

        return [traffic_profile_tpl, private, public]

    def _fill_traffic_profile(self, scenario_cfg, context_cfg):
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

    @staticmethod
    def get_vld_networks(networks):
        return {n['vld_id']: n for n in networks.values()}

    def _resolve_topology(self, context_cfg, topology):
        for vld in topology["vld"]:
            try:
                node_0, node_1 = vld["vnfd-connection-point-ref"]
            except (TypeError, ValueError):
                raise IncorrectConfig("Topology file corrupted, "
                                      "wrong number of endpoints for connection")

            node_0_name = self._find_vnf_name_from_id(topology,
                                                      node_0["member-vnf-index-ref"])
            node_1_name = self._find_vnf_name_from_id(topology,
                                                      node_1["member-vnf-index-ref"])

            node_0_ifname = node_0["vnfd-connection-point-ref"]
            node_1_ifname = node_1["vnfd-connection-point-ref"]

            node_0_if = context_cfg["nodes"][node_0_name]["interfaces"][node_0_ifname]
            node_1_if = context_cfg["nodes"][node_1_name]["interfaces"][node_1_ifname]
            try:
                vld_networks = self.get_vld_networks(context_cfg["networks"])

                node_0_if["vld_id"] = vld["id"]
                node_1_if["vld_id"] = vld["id"]

                # set peer name
                node_0_if["peer_name"] = node_1_name
                node_1_if["peer_name"] = node_0_name

                # set peer interface name
                node_0_if["peer_ifname"] = node_1_ifname
                node_1_if["peer_ifname"] = node_0_ifname

                # just load the whole network dict
                node_0_if["network"] = vld_networks.get(vld["id"], {})
                node_1_if["network"] = vld_networks.get(vld["id"], {})

                node_0_if["dst_mac"] = node_1_if["local_mac"]
                node_0_if["dst_ip"] = node_1_if["local_ip"]

                node_1_if["dst_mac"] = node_0_if["local_mac"]
                node_1_if["dst_ip"] = node_0_if["local_ip"]

                # add peer interface dict, but remove circular link
                # TODO: don't waste memory
                node_0_copy = node_0_if.copy()
                node_1_copy = node_1_if.copy()
                node_0_if["peer_intf"] = node_1_copy
                node_1_if["peer_intf"] = node_0_copy
            except KeyError:
                raise IncorrectConfig("Required interface not found, "
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

    @staticmethod
    def _sort_dpdk_port_num(netdevs):
        # dpdk_port_num is PCI BUS ID ordering, lowest first
        s = sorted(netdevs.values(), key=itemgetter('pci_bus_id'))
        for dpdk_port_num, netdev in enumerate(s, 1):
            netdev['dpdk_port_num'] = dpdk_port_num

    @classmethod
    def _probe_missing_values(cls, netdevs, network, missing):
        mac = network['local_mac']
        for netdev in netdevs.values():
            if netdev['address'].lower() == mac.lower():
                network['driver'] = netdev['driver']
                network['vpci'] = netdev['pci_bus_id']
                network['dpdk_port_num'] = netdev['dpdk_port_num']
                network['ifindex'] = netdev['ifindex']

    TOPOLOGY_REQUIRED_KEYS = frozenset({
        "vpci", "local_ip", "netmask", "local_mac", "driver", "dpdk_port_num"})

    def map_topology_to_infrastructure(self, context_cfg, topology):
        """ This method should verify if the available resources defined in pod.yaml
        match the topology.yaml file.

        :param topology:
        :return: None. Side effect: context_cfg is updated
        """

        for node, node_dict in context_cfg["nodes"].items():

            cmd = "PATH=$PATH:/sbin:/usr/sbin ip addr show"
            with SshManager(node_dict) as conn:
                exit_status = conn.execute(cmd)[0]
                if exit_status != 0:
                    raise IncorrectSetup("Node's %s lacks ip tool." % node)
                exit_status, stdout, _ = conn.execute(
                    self.FIND_NETDEVICE_STRING)
                if exit_status != 0:
                    raise IncorrectSetup(
                        "Cannot find netdev info in sysfs" % node)
                netdevs = node_dict['netdevs'] = self.parse_netdev_info(
                    stdout)
                self._sort_dpdk_port_num(netdevs)

                for network in node_dict["interfaces"].values():
                    missing = self.TOPOLOGY_REQUIRED_KEYS.difference(network)
                    if missing:
                        try:
                            self._probe_missing_values(netdevs, network,
                                                       missing)
                        except KeyError:
                            pass
                        else:
                            missing = self.TOPOLOGY_REQUIRED_KEYS.difference(
                                network)
                        if missing:
                            raise IncorrectConfig(
                                "Require interface fields '%s' "
                                "not found, topology file "
                                "corrupted" % ', '.join(missing))

        # 3. Use topology file to find connections & resolve dest address
        self._resolve_topology(context_cfg, topology)
        self._update_context_with_topology(context_cfg, topology)

    FIND_NETDEVICE_STRING = r"""find /sys/devices/pci* -type d -name net -exec sh -c '{ grep -sH ^ \
$1/ifindex $1/address $1/operstate $1/device/vendor $1/device/device \
$1/device/subsystem_vendor $1/device/subsystem_device ; \
printf "%s/driver:" $1 ; basename $(readlink -s $1/device/driver); } \
' sh  \{\}/* \;
"""
    BASE_ADAPTER_RE = re.compile(
        '^/sys/devices/(.*)/net/([^/]*)/([^:]*):(.*)$', re.M)

    @classmethod
    def parse_netdev_info(cls, stdout):
        network_devices = defaultdict(dict)
        matches = cls.BASE_ADAPTER_RE.findall(stdout)
        for bus_path, interface_name, name, value in matches:
            dirname, bus_id = os.path.split(bus_path)
            if 'virtio' in bus_id:
                # for some stupid reason VMs include virtio1/
                # in PCI device path
                bus_id = os.path.basename(dirname)
            # remove extra 'device/' from 'device/vendor,
            # device/subsystem_vendor', etc.
            if 'device/' in name:
                name = name.split('/')[1]
            network_devices[interface_name][name] = value
            network_devices[interface_name][
                'interface_name'] = interface_name
            network_devices[interface_name]['pci_bus_id'] = bus_id
        # convert back to regular dict
        return dict(network_devices)

    @classmethod
    def get_vnf_impl(cls, vnf_model_id):
        """ Find the implementing class from vnf_model["vnf"]["name"] field

        :param vnf_model_id: parsed vnfd model ID field
        :return: subclass of GenericVNF
        """
        import_modules_from_package(
            "yardstick.network_services.vnf_generic.vnf")
        expected_name = vnf_model_id
        classes_found = []

        def impl():
            for name, class_ in ((c.__name__, c) for c in itersubclasses(GenericVNF)):
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
    def update_interfaces_from_node(vnfd, node):
        for intf in vnfd["vdu"][0]["external-interface"]:
            node_intf = node['interfaces'][intf['name']]
            intf['virtual-interface'].update(node_intf)

    def load_vnf_models(self, scenario_cfg, context_cfg):
        """ Create VNF objects based on YAML descriptors

        :param scenario_cfg:
        :type scenario_cfg:
        :param context_cfg:
        :return:
        """
        vnfs = []
        for node_name, node in context_cfg["nodes"].items():
            LOG.debug(node)
            with open_relative_file(node["VNF model"],
                                    scenario_cfg['task_path']) as stream:
                vnf_model = stream.read()
            vnfd = vnfdgen.generate_vnfd(vnf_model, node)
            # TODO: here add extra context_cfg["nodes"] regardless of template
            vnfd = vnfd["vnfd:vnfd-catalog"]["vnfd"][0]
            self.update_interfaces_from_node(vnfd, node)
            vnf_impl = self.get_vnf_impl(vnfd['id'])
            vnf_instance = vnf_impl(vnfd)
            vnf_instance.name = node_name
            vnfs.append(vnf_instance)

        return vnfs

    def setup(self):
        """ Setup infrastructure, provission VNFs & start traffic

        :return:
        """
        # 1. Verify if infrastructure mapping can meet topology
        self.map_topology_to_infrastructure(self.context_cfg, self.topology)
        # 1a. Load VNF models
        self.vnfs = self.load_vnf_models(self.scenario_cfg, self.context_cfg)
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
