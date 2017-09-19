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

from __future__ import absolute_import
import os
import yaml
import re
import time
import glob
import uuid
import random
import logging
import itertools
import collections
import errno
import time

from netaddr import IPNetwork
import xml.etree.ElementTree as ET
from itertools import izip, chain, repeat
from collections import OrderedDict

from yardstick import ssh
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.utils import provision_tool
from yardstick.orchestrator.heat import get_short_key_uuid
from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.contexts.standalone.model import Libvirt
from yardstick.benchmark.contexts.standalone.model import HelperClass
from yardstick.benchmark.contexts.standalone.model import Server
from yardstick.common.constants import YARDSTICK_ROOT_PATH
from yardstick.common.utils import import_modules_from_package, itersubclasses
from yardstick.common.yaml_loader import yaml_load
from yardstick.network_services.utils import PciAddress

LOG = logging.getLogger(__name__)


class SriovContext(Context):
    """ This class handles SRIOV standalone nodes - VM running on Non-Managed NFVi
    Configuration: sr-iov
    """

    __context_type__ = "StandaloneSriov"


    def __init__(self):
        self.file_path = None
        self.sriov = []
        self.first_run = True
        self.dpdk_nic_bind = ""
        self.vm_names = []
        self.name = None
        self.nfvi_host = []
        self.nodes = []
        self.networks = {}
        self.attrs = {}
        self.vm_flavor = None
        self.servers = None
        self.libvirt = Libvirt()
        self.helper = HelperClass()
        self.drivers = []
        super(SriovContext, self).__init__()

    def init(self, attrs):
        """initializes itself from the supplied arguments"""

        self.name = attrs["name"]
        self.file_path = file_path = attrs.get("file", "pod.yaml")

        self.nodes, self.nfvi_host, self.host_mgmt = \
            self.helper.parse_pod_file(self.file_path, 'Sriov')

        self.attrs = attrs
        self.vm_flavor = attrs.get('flavor', {})
        self.servers = attrs.get('servers', {})
        self.vm_deploy = attrs.get("vm_deploy", True)
        # add optional static network definition
        self.networks= attrs.get("networks", {})

        LOG.debug("Nodes: %r", self.nodes)
        LOG.debug("NFVi Node: %r", self.nfvi_host)
        LOG.debug("Networks: %r", self.networks)

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
        self.helper.install_req_libs(self.connection)
        self.networks = self.helper.get_nic_details(self.connection, self.networks, self.dpdk_nic_bind)
        self.nodes = self.setup_sriov_context()

        LOG.debug("Waiting for VM to come up...")
        self.nodes = self.helper.wait_for_vnfs_to_start(self.connection, self.servers, self.nodes)

    def undeploy(self):
        """don't need to undeploy"""

        if not self.vm_deploy:
            return

        # Todo: NFVi undeploy (sriov, vswitch, ovs etc) based on the config.
        for vm in self.vm_names:
            self.libvirt.check_if_vm_exists_and_delete(vm, self.connection)

        # Bind nics back to kernel
        for driver in self.drivers:
            self.connection.execute("rmmod %s" % driver)
            self.connection.execute("modprobe %s" % driver)

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

    def configure_nics_for_sriov(self):
        for key, ports in self.networks.items():
            vf_pci = []
            host_driver = ports.get('driver')
            if host_driver not in self.drivers:
                self.connection.execute("rmmod %s" % host_driver)
                self.connection.execute("modprobe %s num_vfs=1" % host_driver)
                self.connection.execute("rmmod %svf" % host_driver)
                self.drivers.append(host_driver)

            # enable VFs for given...
            build_vfs = "echo 1 > /sys/bus/pci/devices/{0}/sriov_numvfs" 
            self.connection.execute(build_vfs.format(ports.get('phy_port')))

            # configure VFs...
            mac = self.helper.get_mac_address()
            interface = ports.get('interface')
            if interface is not None:
                vf_cmd = "ip link set {0} vf 0 mac {1}"
                self.connection.execute(vf_cmd.format(interface, mac))

            vf_pci = self.get_vf_datas('vf_pci', ports.get('phy_port'), mac, interface)
            self.networks[key].update({
                'vf_pci': vf_pci,
                'mac': mac
            })

        LOG.info("Ports %s" % self.networks)

    def _enable_interfaces(self, index, idx, vfs, cfg):
        vf = self.networks[vfs[0]]
        vpci = PciAddress.parse_address(vf['vpci'].strip(), multi_line=True)
        # Generate the vpci for the interfaces
        slot = format((index + 10) + (idx), '#04x')[2:]
        vf['vpci'] = \
            "0000:{}:{}.{}".format(vpci.bus, slot, vpci.function)
        self.libvirt.add_sriov_interfaces(
            vf['vpci'], vf['vf_pci']['vf_pci'], vf['mac'], str(cfg))
        self.connection.execute("ifconfig %s up" % vf['interface'])

    def setup_sriov_context(self):
        nodes = []

        #   1 : modprobe host_driver with num_vfs
        self.configure_nics_for_sriov()

        serverslist = OrderedDict(self.servers)
        for index, key in enumerate(serverslist):
            cfg = '/tmp/vm_sriov_%s.xml' % str(index)
            vm_name = "vm_%s" % str(index)

            # 1. Check and delete VM if already exists
            self.libvirt.check_if_vm_exists_and_delete(vm_name, self.connection)

            vcpu, mac = self.libvirt.build_vm_xml(self.connection, self.vm_flavor, cfg, vm_name, index)
            # 2: Cleanup already available VMs
            vnf = serverslist[key]
            ordervnf = OrderedDict(vnf["network_ports"])
            for idx, vkey in enumerate(ordervnf):
                vfs = ordervnf[vkey]
                if vkey == "mgmt":
                    continue
                self._enable_interfaces(index, idx, vfs, cfg)

            # copy xml to target... 
            self.connection.put(cfg, cfg)
            try:
                #    FIXME: launch through libvirt
                LOG.info("virsh create ...")
                self.libvirt.virsh_create_vm(self.connection, cfg)
            except ValueError:
                    raise

            #    5: Tunning for better performace
            self.libvirt.pin_vcpu_for_perf(self.connection, vm_name, vcpu)
            self.vm_names.append(vm_name)

            # build vnf node details
            vnf_node = Server()
            nodes.append(vnf_node.generate_vnf_instance(self.vm_flavor,
                                                        self.networks,
                                                        self.host_mgmt['ip'],
                                                        key, vnf, mac))

        return nodes

    def get_vf_datas(self, key, value, vfmac, pfif):
        vfret = {}
        vfret["mac"] = vfmac
        vfret["pf_if"] = pfif
        vfs = self.helper.get_virtual_devices(self.connection, value)
        for k, v in vfs.items():
            m = PciAddress.parse_address(k.strip(), multi_line=True)
            m1 = PciAddress.parse_address(value.strip(), multi_line=True)
            if m.bus == m1.bus:
                vfret["vf_pci"] = str(v)
                break

        return vfret
