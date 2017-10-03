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

import os
import logging
import collections
from yardstick import ssh
from yardstick.network_services.utils import get_nsb_option
from yardstick.benchmark.contexts.base import Context
from collections import OrderedDict
from yardstick.benchmark.contexts.standalone import model
from yardstick.network_services.utils import provision_tool

LOG = logging.getLogger(__name__)


class StandaloneBase(Context):

    __context_type__ = "StandaloneBase"

    ROLE = None
    DOMAIN_XML_FILE = '/tmp/vm_ovs_%d.xml'

    def __init__(self):
        self.file_path = None
        self.first_run = True
        self.dpdk_nic_bind = ""
        self.vm_names = []
        self.name = None
        self.nfvi_host = []
        self.nodes = []
        self.attrs = {}
        self.vm_flavor = None
        self.servers = None
        self.vm_deploy = None
        self.host_mgmt = None
        self.connection = None
        self.networks = OrderedDict()
        super(StandaloneBase, self).__init__()

    def init(self, attrs):
        """initializes itself from the supplied arguments"""

        self.name = attrs["name"]
        self.file_path = attrs.get("file", "pod.yaml")

        self.nodes, self.nfvi_host, self.host_mgmt = \
            model.parse_pod_file(self.file_path, self.ROLE)

        self.attrs = attrs
        self.vm_flavor = attrs.get('flavor', {})
        self.servers = attrs.get('servers', {})
        self.vm_deploy = attrs.get("vm_deploy", True)
        # add optional static network definition
        self.networks = attrs.get("networks", {})

        LOG.debug("Nodes: %r", self.nodes)
        LOG.debug("NFVi Node: %r", self.nfvi_host)
        LOG.debug("Networks: %r", self.networks)

    def specific_deploy(self):
        # to be implemented by a subclass
        raise NotImplemented

    def deploy(self):
        """don't need to deploy"""

        # Todo: NFVi deploy (sriov, vswitch, ovs etc) based on the config.
        if not self.vm_deploy:
            return

        self.connection = ssh.SSH.from_node(self.host_mgmt)
        self.dpdk_nic_bind = provision_tool(
            self.connection,
            os.path.join(get_nsb_option("bin_path"), "dpdk_nic_bind.py"))
        #    Todo: NFVi deploy (sriov, vswitch, ovs etc) based on the config.
        model.install_req_libs(self.connection)
        model.populate_nic_details(self.connection, self.networks, self.dpdk_nic_bind)

        self.specific_deploy()
        self.nodes = self.setup_context()

        LOG.debug("Waiting for VM to come up...")
        model.wait_for_vnfs_to_start(self.connection, self.servers, self.nodes)

    def specific_undeploy(self):
        # to be implemented by a subclass
        raise NotImplemented

    def undeploy(self):
        """don't need to undeploy"""

        if not self.vm_deploy:
            return

        # Todo: NFVi undeploy (sriov, vswitch, ovs etc) based on the config.
        for vm in self.vm_names:
            model.check_if_vm_exists_and_delete(vm, self.connection)

        self.specific_undeploy()

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

    def setup_context(self):
        nodes = []

        self.configure_nics()

        for index, (key, vnf) in enumerate(OrderedDict(self.servers).items()):
            cfg = self.DOMAIN_XML_FILE % index
            vm_name = "vm_%d" % index

            # 1. Check and delete VM if already exists
            model.check_if_vm_exists_and_delete(vm_name, self.connection)

            vcpu, mac = model.build_vm_xml(self.connection, self.vm_flavor, cfg, vm_name, index)
            # 2: Cleanup already available VMs
            for idx, (vkey, vfs) in enumerate(OrderedDict(vnf["network_ports"]).items()):
                if vkey == "mgmt":
                    continue
                self._enable_interfaces(index, vfs, cfg)

            # copy xml to target...
            self.connection.put(cfg, cfg)

            #    FIXME: launch through libvirt
            LOG.info("virsh create ...")
            model.virsh_create_vm(self.connection, cfg)

            self.vm_names.append(vm_name)

            # build vnf node details
            nodes.append(model.generate_vnf_instance(self.vm_flavor, self.networks,
                                                     self.host_mgmt.get('ip'), key, vnf, mac))

        return nodes
