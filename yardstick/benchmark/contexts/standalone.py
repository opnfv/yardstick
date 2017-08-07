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
"""This module handle non managed standalone virtualization node."""

from __future__ import absolute_import
import logging
import os
import errno
import collections
import time

from yardstick.benchmark.contexts.base import Context
from yardstick.common.constants import YARDSTICK_ROOT_PATH
from yardstick.common.utils import import_modules_from_package, itersubclasses
from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)


class StandaloneContext(Context):
    """ This class handles standalone nodes - VM running on Non-Managed NFVi
    Configuration: vswitch, ovs, ovs-dpdk, sr-iov, linuxbridge
    """

    __context_type__ = "Standalone"

    def __init__(self):
        self.name = None
        self.file_path = None
        self.nodes = []
        self.networks = {}
        self.nfvi_node = []
        self.nfvi_obj = None
        self.attrs = {}
        super(StandaloneContext, self).__init__()

    def read_config_file(self):
        """Read from config file"""

        with open(self.file_path) as stream:
            LOG.info("Parsing pod file: %s", self.file_path)
            cfg = yaml_load(stream)
        return cfg

    def get_nfvi_obj(self):
        print("{0}".format(self.nfvi_node[0]['role']))
        context_type = self.get_context_impl(self.nfvi_node[0]['role'])
        nfvi_obj = context_type()
        nfvi_obj.__init__()
        nfvi_obj.parse_pod_and_get_data(self.file_path)
        return nfvi_obj

    def init(self, attrs):
        """initializes itself from the supplied arguments"""

        self.name = attrs["name"]
        self.file_path = file_path = attrs.get("file", "pod.yaml")

        try:
            cfg = self.read_config_file()
        except IOError as io_error:
            if io_error.errno != errno.ENOENT:
                raise
            self.file_path = os.path.join(YARDSTICK_ROOT_PATH, file_path)
            cfg = self.read_config_file()

        self.vm_deploy = attrs.get("vm_deploy", True)
        self.nodes.extend([node for node in cfg["nodes"]
                           if str(node["role"]) != "Sriov" and
                           str(node["role"]) != "Ovsdpdk"])
        for node in cfg["nodes"]:
            if str(node["role"]) == "Sriov":
                self.nfvi_node.extend([node for node in cfg["nodes"]
                                       if str(node["role"]) == "Sriov"])
            if str(node["role"]) == "Ovsdpdk":
                self.nfvi_node.extend([node for node in cfg["nodes"]
                                       if str(node["role"]) == "Ovsdpdk"])
                LOG.info("{0}".format(node["role"]))
            else:
                LOG.debug("Node role is other than SRIOV and OVS")
        self.nfvi_obj = self.get_nfvi_obj()
        self.attrs = attrs
        # add optional static network definition
        self.networks.update(cfg.get("networks", {}))
        self.nfvi_obj = self.get_nfvi_obj()
        LOG.debug("Nodes: %r", self.nodes)
        LOG.debug("NFVi Node: %r", self.nfvi_node)
        LOG.debug("Networks: %r", self.networks)

    def deploy(self):
        """don't need to deploy"""

        # Todo: NFVi deploy (sriov, vswitch, ovs etc) based on the config.
        if not self.vm_deploy:
            return

        #    Todo: NFVi deploy (sriov, vswitch, ovs etc) based on the config.
        self.nfvi_obj.ssh_remote_machine()
        if self.nfvi_obj.first_run is True:
            self.nfvi_obj.install_req_libs()

        nic_details = self.nfvi_obj.get_nic_details()
        print("{0}".format(nic_details))

        if self.nfvi_node[0]["role"] == "Sriov":
            self.nfvi_obj.setup_sriov_context(
                self.nfvi_obj.sriov[0]['phy_ports'],
                nic_details,
                self.nfvi_obj.sriov[0]['phy_driver'])
        if self.nfvi_node[0]["role"] == "Ovsdpdk":
            self.nfvi_obj.setup_ovs(self.nfvi_obj.ovs[0]["phy_ports"])
            self.nfvi_obj.start_ovs_serverswitch()
            time.sleep(5)
            self.nfvi_obj.setup_ovs_bridge()
            self.nfvi_obj.add_oflows()
            self.nfvi_obj.setup_ovs_context(
                self.nfvi_obj.ovs[0]['phy_ports'],
                nic_details,
                self.nfvi_obj.ovs[0]['phy_driver'])
            pass

    def undeploy(self):
        """don't need to undeploy"""

        if not self.vm_deploy:
            return
        # Todo: NFVi undeploy (sriov, vswitch, ovs etc) based on the config.
        # self.nfvi_obj = self.get_nfvi_obj()
        self.nfvi_obj.ssh_remote_machine()
        self.nfvi_obj.destroy_vm()
        pass

    def _get_server(self, attr_name):
        """lookup server info by name from context

        Keyword arguments:
        attr_name -- A name for a server listed in nodes config file
        """
        node_name, name = self.split_name(attr_name)
        if name is None or self.name != name:
            return None

        matching_nodes = (n for n in self.nodes if n["name"] == node_name)
        try:
            # A clone is created in order to avoid affecting the
            # original one.
            node = dict(next(matching_nodes))
        except StopIteration:
            return None

        try:
            duplicate = next(matching_nodes)
        except StopIteration:
            pass
        else:
            raise ValueError("Duplicate nodes!!! Nodes: %s %s",
                             (node, duplicate))

        node["name"] = attr_name
        return node

    def _get_network(self, attr_name):
        if not isinstance(attr_name, collections.Mapping):
            network = self.networks.get(attr_name)

        else:
            # Don't generalize too much  Just support vld_id
            vld_id = attr_name.get('vld_id', {})
            # for standalone context networks are dicts
            iter1 = (n for n in self.networks.values() if n.get('vld_id') == vld_id)
            network = next(iter1, None)

        if network is None:
            return None

        result = {
            # name is required
            "name": network["name"],
            "vld_id": network.get("vld_id"),
            "segmentation_id": network.get("segmentation_id"),
            "network_type": network.get("network_type"),
            "physical_network": network.get("physical_network"),
        }
        return result

    def get_context_impl(self, nfvi_type):
        """ Find the implementing class from vnf_model["vnf"]["name"] field

        :param vnf_model: dictionary containing a parsed vnfd
        :return: subclass of GenericVNF
        """
        import_modules_from_package(
            "yardstick.benchmark.contexts")
        expected_name = nfvi_type
        impl = [c for c in itersubclasses(StandaloneContext)
                if c.__name__ == expected_name]
        try:
            return next(iter(impl))
        except StopIteration:
            raise ValueError("No implementation for %s", expected_name)
