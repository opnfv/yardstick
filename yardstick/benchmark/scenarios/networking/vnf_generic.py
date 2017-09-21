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

import ipaddress
import os
import sys
import re
from itertools import chain

import six
import yaml
from collections import defaultdict

from yardstick.benchmark.scenarios import base
from yardstick.common.constants import LOG_DIR
from yardstick.common.process import terminate_children
from yardstick.common.utils import import_modules_from_package, itersubclasses
from yardstick.common.yaml_loader import yaml_load
from yardstick.network_services.collector.subscriber import Collector
from yardstick.network_services.vnf_generic import vnfdgen
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.traffic_profile.base import TrafficProfile
from yardstick.network_services.utils import get_nsb_option
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
    def __init__(self, node, timeout=120):
        super(SshManager, self).__init__()
        self.node = node
        self.conn = None
        self.timeout = timeout

    def __enter__(self):
        """
        args -> network device mappings
        returns -> ssh connection ready to be used
        """
        try:
            self.conn = ssh.SSH.from_node(self.node)
            self.conn.wait(timeout=self.timeout)
        except SSHError as error:
            LOG.info("connect failed to %s, due to %s", self.node["ip"], error)
        # self.conn defaults to None
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()


def find_relative_file(path, task_path):
    """
    Find file in one of places: in abs of path or
    relative to TC scenario file. In this order.

    :param path:
    :param task_path:
    :return str: full path to file
    """
    # fixme: create schema to validate all fields have been provided
    for lookup in [os.path.abspath(path), os.path.join(task_path, path)]:
        try:
            with open(lookup):
                return lookup
        except IOError:
            pass
    raise IOError(errno.ENOENT, 'Unable to find {} file'.format(path))


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
            topology_yaml = yaml_load(stream)

        self.topology = topology_yaml["nsd:nsd-catalog"]["nsd"][0]
        self.vnfs = []
        self.collector = None
        self.traffic_profile = None
        self.node_netdevs = {}

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
        with open_relative_file(profile, path) as infile:
            return infile.read()

    def _fill_traffic_profile(self):
        traffic_mapping = self._get_traffic_profile()
        traffic_map_data = {
            'flow': self._get_traffic_flow(),
            'imix': self._get_traffic_imix(),
            TrafficProfile.UPLINK: {},
            TrafficProfile.DOWNLINK: {},
        }

        traffic_vnfd = vnfdgen.generate_vnfd(traffic_mapping, traffic_map_data)
        self.traffic_profile = TrafficProfile.get(traffic_vnfd)
        return self.traffic_profile

    def _find_vnf_name_from_id(self, vnf_id):
        return next((vnfd["vnfd-id-ref"]
                     for vnfd in self.topology["constituent-vnfd"]
                     if vnf_id == vnfd["member-vnf-index"]), None)

    @staticmethod
    def get_vld_networks(networks):
        # network name is vld_id
        vld_map = {}
        for name, n in networks.items():
            try:
                vld_map[n['vld_id']] = n
            except KeyError:
                vld_map[name] = n
        return vld_map

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
                vld_networks = self.get_vld_networks(self.context_cfg["networks"])
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

    def _find_vnfd_from_vnf_idx(self, vnf_idx):
        return next((vnfd for vnfd in self.topology["constituent-vnfd"]
                     if vnf_idx == vnfd["member-vnf-index"]), None)

    def _update_context_with_topology(self):
        for vnfd in self.topology["constituent-vnfd"]:
            vnf_idx = vnfd["member-vnf-index"]
            vnf_name = self._find_vnf_name_from_id(vnf_idx)
            vnfd = self._find_vnfd_from_vnf_idx(vnf_idx)
            self.context_cfg["nodes"][vnf_name].update(vnfd)

    def _probe_netdevs(self, node, node_dict, timeout=120):
        try:
            return self.node_netdevs[node]
        except KeyError:
            pass

        netdevs = {}
        cmd = "PATH=$PATH:/sbin:/usr/sbin ip addr show"

        with SshManager(node_dict, timeout=timeout) as conn:
            if conn:
                exit_status = conn.execute(cmd)[0]
                if exit_status != 0:
                    raise IncorrectSetup("Node's %s lacks ip tool." % node)
                exit_status, stdout, _ = conn.execute(
                    self.FIND_NETDEVICE_STRING)
                if exit_status != 0:
                    raise IncorrectSetup(
                        "Cannot find netdev info in sysfs" % node)
                netdevs = node_dict['netdevs'] = self.parse_netdev_info(stdout)

        self.node_netdevs[node] = netdevs
        return netdevs

    @classmethod
    def _probe_missing_values(cls, netdevs, network):

        mac_lower = network['local_mac'].lower()
        for netdev in netdevs.values():
            if netdev['address'].lower() != mac_lower:
                continue
            network.update({
                'driver': netdev['driver'],
                'vpci': netdev['pci_bus_id'],
                'ifindex': netdev['ifindex'],
            })

    def _generate_pod_yaml(self):
        context_yaml = os.path.join(LOG_DIR, "pod-{}.yaml".format(self.scenario_cfg['task_id']))
        # convert OrderedDict to a list
        # pod.yaml nodes is a list
        nodes = []
        for node in self.context_cfg["nodes"].values():
            # name field is required
            # remove context suffix
            node['name'] = node['name'].split('.')[0]
            nodes.append(node)
        nodes = self._convert_pkeys_to_string(nodes)
        pod_dict = {
            "nodes": nodes,
            "networks": self.context_cfg["networks"]
        }
        with open(context_yaml, "w") as context_out:
            yaml.safe_dump(pod_dict, context_out, default_flow_style=False,
                           explicit_start=True)

    @staticmethod
    def _convert_pkeys_to_string(nodes):
        # make copy because we are mutating
        nodes = nodes[:]
        for i, node in enumerate(nodes):
            try:
                nodes[i] = dict(node, pkey=ssh.convert_key_to_str(node["pkey"]))
            except KeyError:
                pass
        return nodes

    TOPOLOGY_REQUIRED_KEYS = frozenset({
        "vpci", "local_ip", "netmask", "local_mac", "driver"})

    def map_topology_to_infrastructure(self):
        """ This method should verify if the available resources defined in pod.yaml
        match the topology.yaml file.

        :return: None. Side effect: context_cfg is updated
        """
        num_nodes = len(self.context_cfg["nodes"])
        # OpenStack instance creation time is probably proportional to the number
        # of instances
        timeout = 120 * num_nodes
        for node, node_dict in self.context_cfg["nodes"].items():

            for network in node_dict["interfaces"].values():
                missing = self.TOPOLOGY_REQUIRED_KEYS.difference(network)
                if not missing:
                    continue

                # only ssh probe if there are missing values
                # ssh probe won't work on Ixia, so we had better define all our values
                try:
                    netdevs = self._probe_netdevs(node, node_dict, timeout=timeout)
                except (SSHError, SSHTimeout):
                    raise IncorrectConfig(
                        "Unable to probe missing interface fields '%s', on node %s "
                        "SSH Error" % (', '.join(missing), node))
                try:
                    self._probe_missing_values(netdevs, network)
                except KeyError:
                    pass
                else:
                    missing = self.TOPOLOGY_REQUIRED_KEYS.difference(
                        network)
                if missing:
                    raise IncorrectConfig(
                        "Require interface fields '%s' not found, topology file "
                        "corrupted" % ', '.join(missing))

        # we have to generate pod.yaml here so we have vpci and driver
        self._generate_pod_yaml()
        # 3. Use topology file to find connections & resolve dest address
        self._resolve_topology()
        self._update_context_with_topology()

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
        # we assume OrderedDict for consistenct in instantiation
        for node_name, node in context_cfg["nodes"].items():
            LOG.debug(node)
            try:
                file_name = node["VNF model"]
            except KeyError:
                LOG.debug("no model for %s, skipping", node_name)
                continue
            file_path = scenario_cfg['task_path']
            with open_relative_file(file_name, file_path) as stream:
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
        """ Setup infrastructure, provission VNFs & start traffic

        :return:
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

        # 3. Run experiment
        # Start listeners first to avoid losing packets
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

        # this is the only method that is check from the runner
        # so if we have any fatal error it must be raised via these methods
        # otherwise we will not terminate

        for vnf in self.vnfs:
            # Result example:
            # {"VNF1: { "tput" : [1000, 999] }, "VNF2": { "latency": 100 }}
            LOG.debug("collect KPI for %s", vnf.name)
            result.update(self.collector.get_kpi(vnf))

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
