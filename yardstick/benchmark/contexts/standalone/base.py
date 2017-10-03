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

import logging
from yardstick import ssh
from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.contexts import common
from collections import OrderedDict
from yardstick.benchmark.contexts.standalone import model
from yardstick.network_services.helpers.dpdkbindnic_helper import DpdkBindHelper

LOG = logging.getLogger(__name__)


class StandaloneBase(Context):

    __context_type__ = "StandaloneBase"

    ROLE = None
    DOMAIN_XML_FILE = '/tmp/vm_ovs_%d.xml'

    def __init__(self):
        self.file_path = None
        self.first_run = True
        self.dpdk_bind_helper = None
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
        self.networks = None
        super(StandaloneBase, self).__init__()

    def init(self, attrs):
        """initializes itself from the supplied arguments"""

        self.name = attrs["name"]
        self.file_path = attrs.get("file", "pod.yaml")

        self.nodes, self.nfvi_host, self.host_mgmt = \
            model.parse_pod_file(self.file_path, self.ROLE)

        self.attrs = attrs
        self.vm_flavor = attrs.get('flavor', {})
        self.servers = OrderedDict(sorted(attrs.get('servers', {}).items()))
        self.vm_deploy = attrs.get("vm_deploy", True)
        # add optional static network definition
        self.networks = OrderedDict(sorted(attrs.get("networks", {}).items()))

        LOG.debug("Nodes: %r", self.nodes)
        LOG.debug("NFVi Node: %r", self.nfvi_host)
        LOG.debug("Networks: %r", self.networks)

    def _specific_deploy(self):  # pragma: no cover
        # to be implemented by a subclass
        raise NotImplemented

    def deploy(self):
        if not self.vm_deploy:
            return

        self.connection = ssh.SSH.from_node(self.host_mgmt)
        self.dpdk_bind_helper = DpdkBindHelper(self.connection)
        self.dpdk_bind_helper.read_status()
        self.dpdk_bind_helper.save_used_drivers()
        model.install_req_libs(self.connection)
        model.populate_nic_details(self.connection, self.networks, self.dpdk_bind_helper)

        self._specific_deploy()
        self.nodes = self.setup_context()

        LOG.debug("Waiting for VM to come up...")
        model.wait_for_vnfs_to_start(self.connection, self.servers, self.nodes)

    def _specific_undeploy(self):  # pragma: no cover
        # to be implemented by a subclass
        raise NotImplemented

    def undeploy(self):
        if not self.vm_deploy:
            return

        for vm in self.vm_names:
            model.check_if_vm_exists_and_delete(vm, self.connection)

        self._specific_undeploy()

    def _get_server(self, attr_name):
        return common.get_server(self, attr_name)

    def _get_network(self, attr_name):
        return common.get_network(self, attr_name)

    def setup_context(self):
        nodes = []

        self._configure_nics()

        for vm_index, (key, vnf) in enumerate(self.servers.items()):
            cfg = self.DOMAIN_XML_FILE % vm_index
            vm_name = "vm_%d" % vm_index

            # 1. Check and delete VM if already exists
            model.check_if_vm_exists_and_delete(vm_name, self.connection)

            vcpu, mac = model.build_vm_xml(self.connection, self.vm_flavor, cfg, vm_name, vm_index)

            for port_index, (vkey, vfs) in enumerate(sorted(vnf["network_ports"].items())):
                if vkey == "mgmt":
                    continue
                self._enable_interfaces(vm_index, port_index, vfs, cfg)

            # copy xml to target...
            self.connection.put(cfg, cfg)

            LOG.info("virsh create ...")
            model.virsh_create_vm(self.connection, cfg)

            self.vm_names.append(vm_name)

            # build vnf node details
            nodes.append(model.generate_vnf_instance(self.vm_flavor, self.networks,
                                                     self.host_mgmt.get('ip'), key, vnf, mac))

        return nodes
