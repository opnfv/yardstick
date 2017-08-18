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

import glob
import logging
import os
import errno
from collections import Mapping

import itertools

import re
import yaml
import time

from yardstick.benchmark.contexts.base import Context
from yardstick.common.constants import YARDSTICK_ROOT_PATH
from yardstick.common.utils import import_modules_from_package
from yardstick.common.utils import itersubclasses
from yardstick.common.utils import range_list_str_generator
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.vnf_generic.vnf.sample_vnf import VnfSshHelper

LOG = logging.getLogger(__name__)

TRANSPARENT_HUGEPAGE_ENABLED = '/sys/kernel/mm/transparent_hugepage/enabled'
UNSAFE_INTERRUPTS_PATH = "/sys/module/kvm/parameters/allow_unsafe_assigned_interrupts"


class StandaloneContext(Context):
    """ This class handles standalone nodes - VM running on Non-Managed NFVi
    Configuration: vswitch, ovs, ovs-dpdk, sr-iov, linuxbridge
    """

    CONTEXT_TYPE = "Standalone"
    PCI_PATTERN = re.compile("0000:(\d+):(\d+).(\d+)", re.MULTILINE)
    VM_TEMPLATE = None

    @staticmethod
    def read_from_file(filename):
        with open(filename, 'r') as handle:
            data = handle.read()
        return data

    @staticmethod
    def write_to_file(filename, content):
        with open(filename, 'w') as handle:
            handle.write(content)

    @staticmethod
    def get_numa_nodes():
        nodes_sysfs = glob.iglob("/sys/devices/system/node/node*")
        nodes = {}
        for node_sysfs in nodes_sysfs:
            node_num = os.path.basename(node_sysfs).partition("node")[2]
            with open(os.path.join(node_sysfs, "cpulist")) as cpulist_file:
                cpulist = cpulist_file.read().strip()

            ranges = (range(x, y) for x, y in range_list_str_generator(cpulist))
            # TODO: use set to eliminate duplicates?
            nodes[node_num] = sorted(itertools.chain.from_iterable(ranges))
        LOG.info("numa nodes: %s", nodes)
        return nodes

    def __init__(self):
        super(StandaloneContext, self).__init__()
        self.name = None
        self.bin_path = get_nsb_option("bin_path")
        self.nic_details = None
        self.file_path = None
        self.nodes = []
        self.networks = {}
        self.attrs = {}
        self._ssh_helper = None
        self.vm_deploy = None
        self.first_run = True
        self.dpdk_nic_bind = ""

    @property
    def ssh_helper(self):
        if not self._ssh_helper:
            self._ssh_helper = VnfSshHelper(self.nodes[0], self.bin_path, wait=True)
        return self._ssh_helper

    def _read_config_file(self):
        """Read from config file"""
        with open(self.file_path) as stream:
            cfg = yaml.safe_load(stream)
        return cfg

    def read_config_file(self):
        try:
            return self._read_config_file()
        except IOError as io_error:
            if io_error.errno != errno.ENOENT:
                raise
            self.file_path = os.path.join(YARDSTICK_ROOT_PATH, self.file_path)
            return self._read_config_file()

    def _parse_pod_and_get_data(self):
        LOG.info("Parsing pod file: %s", self.file_path)
        try:
            cfg = self.read_config_file()
        except IOError:
            LOG.error("File %s does not exist", self.file_path)
            raise

        LOG.info("Parsed pod file: %s", self.file_path)

        # add optional static network definition
        self.networks.update(cfg.get("networks", {}))

        for node in cfg['nodes']:
            self.nodes.append(node)

    def _extra_init(self):
        pass

    def init(self, attrs):
        """initializes itself from the supplied arguments"""

        self.attrs = attrs
        self.name = attrs["name"]
        self.file_path = attrs.get("file", "pod.yaml")
        self.vm_deploy = attrs.get("vm_deploy", True)

        self._parse_pod_and_get_data()
        self.dpdk_nic_bind = self.ssh_helper.provision_tool(tool_file="dpdk_nic_bind.py")
        self._extra_init()

        LOG.debug("%s Node: %r", self.CONTEXT_TYPE, self.nodes)
        LOG.debug("Networks: %r", self.networks)

    def get_nic_details(self):
        node0 = self.nodes[0]

        if self.nic_details:
            return node0, self.nic_details

        interface_dict = {}
        phy_ports = node0['phy_ports']
        phy_driver = node0['phy_driver']

        self.nic_details = nic_details = {
            'interface': interface_dict,
            'pci': phy_ports,
            'phy_driver': phy_driver,
            'vf_macs': node0['vf_macs'],
        }

        #   Make sure that ports are bound to kernel drivers e.g. i40e/ixgbe
        bind_cmd = "{dpdk_nic_bind} --force -b {driver} {port}"
        lshw_cmd = "lshw -c network -businfo | grep '{port}'"
        link_show_cmd = "ip -s link show {interface}"
        for index, phy_port in enumerate(phy_ports):
            cmd = bind_cmd.format(dpdk_nic_bind=self.dpdk_nic_bind,
                                  driver=phy_driver, port=phy_port)

            self._ssh_helper.execute(cmd)
            out = self._ssh_helper.execute(lshw_cmd.format(port=phy_port))[1]
            interface = out.split()[1]

            self._ssh_helper.execute(link_show_cmd.format(interface=interface))
            interface_dict[index] = interface

        LOG.info('Got NIC details:\n%s', nic_details)
        return node0, self.nic_details

    def pin_vcpu(self):
        nodes = self.get_numa_nodes()
        the_node = nodes[str(len(nodes) - 1)]
        the_node_len = len(the_node)
        cmd = "virsh vcpupin vm1 {0} {1}"
        for i in range(0, 10):
            self._ssh_helper.execute(cmd.format(i, the_node[i % the_node_len]))

    def _install_required_libraries(self):
        raise NotImplementedError

    def _setup_context(self):
        raise NotImplementedError

    def _make_vm_template(self):
        raise NotImplementedError

    def _deploy_vm(self):
        self._setup_xml_template()
        self._start_vm()
        self._tune_vm()

    def _setup_xml_template(self):
        cfg_file = '/tmp/vm_{0}.xml'.format(self.CONTEXT_TYPE.lower())
        self.write_to_file(cfg_file, self._make_vm_template())
        self._ssh_helper.put(cfg_file, cfg_file)
        time.sleep(10)

    def _start_vm(self):
        status, out, _ = self.ssh_helper.execute("virsh list --name | grep -i vm1")
        if out == "vm1":
            LOG.info("VM is already present")
            return

        # FIXME: launch through libvirt
        LOG.info("virsh create ...")
        status, out, err = self._ssh_helper.execute("virsh create /tmp/vm_ovs.xml")
        time.sleep(10)
        LOG.debug("err    : {0}".format(err))
        LOG.debug("out    : {0}".format(out))
        LOG.info("status : {0}".format(status))

    def _tune_vm(self):
        self.pin_vcpu()
        self._ssh_helper.echo_to_file("1", UNSAFE_INTERRUPTS_PATH)
        self._ssh_helper.echo_to_file("never", TRANSPARENT_HUGEPAGE_ENABLED)
        LOG.info("After tuning performance ...")

    def deploy(self):
        """Deploy the VNF, if appropriate"""

        # TODO: NFVi deploy (sriov, vswitch, ovs etc) based on the config.
        if not self.vm_deploy:
            # don't need to deploy
            return

        self._deploy_vm()

        # TODO: NFVi deploy (sriov, vswitch, ovs etc) based on the config.
        if self.first_run:
            self._install_required_libraries()

        self._setup_context()

    def destroy_vm(self):
        host_driver = self.nodes[0]['phy_driver']
        status, out, error = self._ssh_helper.execute("virsh list --name | grep -i vm1")
        if status != 0:
            LOG.info("output: %s", out)
            LOG.info("error: %s", error)
            LOG.error("destroy vm status: %s", status)
            return

        self._ssh_helper.execute("virsh shutdown vm1")
        self._ssh_helper.execute("virsh destroy vm1")
        self._ssh_helper.execute("rmmod {0}".format(host_driver))
        self._ssh_helper.execute("modprobe {0}".format(host_driver))

    def undeploy(self):
        """Undeploy, if necessary"""

        if not self.vm_deploy:
            # don't need to undeploy
            return

        # TODO: NFVi undeploy (sriov, vswitch, ovs etc) based on the config.
        self.destroy_vm()

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
            raise ValueError("Duplicate nodes!!! Nodes: %s %s" % (node, duplicate))

        node["name"] = attr_name
        return node

    def get_context_type(self, nfvi_type=None):
        """ Find the implementing class from vnf_model["vnf"]["name"] field

        :param nfvi_type: dictionary containing a parsed vnfd
        :return: subclass of GenericVNF
        """
        if nfvi_type is None:
            nfvi_type = self.nodes[0]['role']

        import_modules_from_package("yardstick.benchmark.contexts")
        expected_name = nfvi_type
        impl = (c for c in itersubclasses(StandaloneContext) if c.__name__ == expected_name)
        try:
            return next(iter(impl))
        except StopIteration:
            raise ValueError("No implementation for %s", expected_name)

    def _get_network(self, attr_name):
        if not isinstance(attr_name, Mapping):
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
