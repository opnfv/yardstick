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

""" This module handles all the libvirt updates to launch VM"""
from __future__ import absolute_import
import os
import re
import time
import glob
import uuid
import logging

from itertools import chain, cycle
from netaddr import IPNetwork
import xml.etree.ElementTree as ET

from yardstick import ssh
from yardstick.common.constants import YARDSTICK_ROOT_PATH
from yardstick.network_services.utils import PciAddress
from yardstick.network_services.utils import MacAddress
from yardstick.common.utils import write_file
from yardstick.common.utils import YamlFilePathWrapper

LOG = logging.getLogger(__name__)

VM_TEMPLATE = """
<domain type="kvm">
 <name>{vm_name}</name>
  <uuid>{random_uuid}</uuid>
  <memory unit="MB">{memory}</memory>
  <currentMemory unit="MB">{memory}</currentMemory>
  <memoryBacking>
    <hugepages />
  </memoryBacking>
  <vcpu placement="static">{vcpu}</vcpu>
  <os>
    <type arch="x86_64" machine="pc-i440fx-utopic">hvm</type>
    <boot dev="hd" />
  </os>
  <features>
    <acpi />
    <apic />
    <pae />
  </features>
  <cpu mode='host-passthrough'>
    <topology cores="{cpu}" sockets="{socket}" threads="{threads}" />
    <numa>
       <cell id='0' cpus='{numa_cpus}' memory='{memory}' unit='MB' memAccess='shared'/>
    </numa>
  </cpu>
  <clock offset="utc">
    <timer name="rtc" tickpolicy="catchup" />
    <timer name="pit" tickpolicy="delay" />
    <timer name="hpet" present="no" />
  </clock>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <devices>
    <emulator>/usr/bin/kvm-spice</emulator>
    <disk device="disk" type="file">
      <driver name="qemu" type="qcow2" />
      <source file="{vm_image}"/>
      <target bus="virtio" dev="vda" />
    </disk>
    <disk device="cdrom" type="file">
      <driver name="qemu" type="raw"/>
      <source file="/var/lib/yardstick/vm{index}/vm{index}-cidata.iso"/>
      <target bus="virtio" dev ="vdb" />
    </disk>
    <graphics autoport="yes" listen="0.0.0.0" port="-1" type="vnc" />
    <interface type="bridge">
      <mac address='{mac_addr}'/>
      <source bridge="br-int" />
      <model type='virtio'/>
    </interface>
   </devices>
</domain>
"""
WAIT_FOR_BOOT = 30


def check_if_vm_exists_and_delete(vm_name, connection):
    cmd_template = "virsh list --name | grep -i %s"
    status = connection.execute(cmd_template % vm_name)[0]
    if status == 0:
        LOG.info("VM '%s' is already present.. destroying" % vm_name)
        virsh_destroy_vm(vm_name, connection)


def virsh_create_vm(connection, cfg):
    status = connection.execute("virsh create %s" % cfg)[0]
    LOG.info("VM create status: %s" % status)


def virsh_destroy_vm(vm_name, connection):
    connection.execute("virsh destroy %s" % vm_name)


def add_interface_address(interface, pci_address):
    vm_pci = ET.SubElement(interface, 'address')
    vm_pci.set('type', 'pci')
    vm_pci.set('domain', '0x%s' % pci_address.domain)
    vm_pci.set('bus', '0x%s' % pci_address.bus)
    vm_pci.set('slot', '0x%s' % pci_address.slot)
    vm_pci.set('function', '0x%s' % pci_address.function)
    return vm_pci


def add_ovs_interface(vpath, port_num, vpci, vports_mac, xml):
    vhost_path = '{0}/var/run/openvswitch/dpdkvhostuser{1}'
    root = ET.parse(xml)
    pci_address = PciAddress.parse_address(vpci.strip(), multi_line=True)
    device = root.find('devices')

    interface = ET.SubElement(device, 'interface')
    interface.set('type', 'vhostuser')
    mac = ET.SubElement(interface, 'mac')
    mac.set('address', vports_mac)

    source = ET.SubElement(interface, 'source')
    source.set('type', 'unix')
    source.set('path', vhost_path.format(vpath, port_num))
    source.set('mode', 'client')

    model = ET.SubElement(interface, 'model')
    model.set('type', 'virtio')

    driver = ET.SubElement(interface, 'driver')
    driver.set('queues', '4')

    host = ET.SubElement(driver, 'host')
    host.set('mrg_rxbuf', 'off')

    add_interface_address(interface, pci_address)

    root.write(xml)


def add_sriov_interfaces(vm_pci, vf_pci, vfmac, xml):
    root = ET.parse(xml)
    pci_address = PciAddress.parse_address(vf_pci.strip(), multi_line=True)
    device = root.find('devices')

    interface = ET.SubElement(device, 'interface')
    interface.set('managed', 'yes')
    interface.set('type', 'hostdev')

    mac = ET.SubElement(interface, 'mac')
    mac.set('address', vfmac)
    source = ET.SubElement(interface, 'source')

    addr = ET.SubElement(source, "address")
    addr.set('domain', "0x0")
    addr.set('bus', "{0}".format(pci_address.bus))
    addr.set('function', "{0}".format(pci_address.function))
    addr.set('slot', "0x{0}".format(pci_address.slot))
    addr.set('type', "pci")

    pci_vm_address = PciAddress.parse_address(vm_pci.strip(), multi_line=True)
    add_interface_address(interface, pci_vm_address)

    root.write(xml)


def create_snapshot_qemu(connection, index, vm_image):
    # build snapshot image
    image = "/var/lib/libvirt/images/%s.qcow2" % index
    connection.execute("rm %s" % image)
    qemu_template = "qemu-img create -f qcow2 -o backing_file=%s %s"
    connection.execute(qemu_template % (vm_image, image))

    return image


def build_vm_xml(connection, flavor, cfg, vm_name, index):
    extra_spec = flavor.get('extra_specs', {})
    cpu = extra_spec.get('hw:cpu_cores', '2')
    threads = extra_spec.get('hw:cpu_threads', '2')
    vcpu = int(cpu) * int(threads)
    mac = MacAddress.make_random(0x00)

    kwargs = {
        'memory': flavor.get('ram', '4096'),
        'extra_spec': extra_spec,
        'cpu': cpu,
        'socket': extra_spec.get('hw:cpu_sockets', '1'),
        'threads': threads,
        'vcpu': vcpu,
        'numa_cpus': '0-%s' % (vcpu - 1),
        'mac_addr': mac,
        'vm_image': create_snapshot_qemu(connection, index, flavor.get("images")),
        'index': index,
        'random_uuid': uuid.uuid4(),
        'vm_name': vm_name
    }
    vm_xml = VM_TEMPLATE.format(**kwargs)

    write_file(cfg, vm_xml)

    return vcpu, mac


def split_cpu_list(cpu_list):
    if not cpu_list:
        return []

    bounds = (cycle((int(b) for b in r.split('-'))) for r in cpu_list.split(','))
    range_objects = (range(next(bound), next(bound) + 1) for bound in bounds)
    return sorted(chain.from_iterable(range_objects))


def get_numa_nodes():
    nodes_sysfs = glob.iglob("/sys/devices/system/node/node*")
    nodes = {}
    for node_sysfs in nodes_sysfs:
        num = os.path.basename(node_sysfs).replace("node", "")
        with open(os.path.join(node_sysfs, "cpulist")) as cpulist_file:
            cpulist = cpulist_file.read().strip()
        nodes[num] = split_cpu_list(cpulist)
    LOG.info("nodes: %s", nodes)
    return nodes


def update_interrupts_hugepages_perf(connection):
    connection.execute("echo 1 > /sys/module/kvm/parameters/allow_unsafe_assigned_interrupts")
    connection.execute("echo never > /sys/kernel/mm/transparent_hugepage/enabled")


def pin_vcpu_for_perf(connection, vm_name, cpu):
    nodes = get_numa_nodes()
    core_node = nodes[str(len(nodes) - 1)]
    core_node_len = len(core_node)
    vcpu_pin_template = "virsh vcpupin {0} {1} {2}"
    for i in range(int(cpu)):
        core = core_node[i % core_node_len]
        connection.execute(vcpu_pin_template.format(vm_name, i, core))
    update_interrupts_hugepages_perf(connection)


def install_req_libs(connection, extra_pkgs=None):
    pkgs = ["qemu-kvm", "libvirt-bin", "bridge-utils", "numactl", "fping"]
    seen = set()
    if extra_pkgs:
        pkgs.extend(extra_pkgs)
    cmd_template = "dpkg-query -W --showformat='${Status}\\n' \"%s\"|grep 'ok installed'"
    for pkg in pkgs:
        if pkg in seen:
            continue
        seen.add(pkg)
        if connection.execute(cmd_template % pkg)[0]:
            connection.execute("apt-get update")
            connection.execute("apt-get -y install %s" % pkg)


def get_kernel_module(connection, pci, driver):
    if not driver:
        out = connection.execute("lspci -k -s %s" % pci)[1]
        driver = out.split("Kernel modules:").pop().strip()
    return driver


def populate_nic_details(connection, networks, dpdk_nic_bind):
    for key, ports in networks.items():
        if key == "mgmt":
            continue

        phy_port = ports['phy_port']
        phy_driver = ports.get('phy_driver')
        driver = get_kernel_module(connection, phy_port, phy_driver)

        # Make sure that ports are bound to kernel drivers e.g. i40e/ixgbe
        bind_cmd = "{dpdk_nic_bind} --force -b {driver} {port}"
        lshw_cmd = "lshw -c network -businfo | grep '{port}'"
        link_show_cmd = "ip -s link show {interface}"

        cmd = bind_cmd.format(dpdk_nic_bind=dpdk_nic_bind, driver=driver, port=phy_port)
        connection.execute(cmd)

        out = connection.execute(lshw_cmd.format(port=phy_port))[1]
        interface = out.split()[1]

        connection.execute(link_show_cmd.format(interface=interface))

        ports.update({
            'interface': str(interface),
            'driver': driver
        })

    LOG.info('%s', networks)


def get_virtual_devices(connection, pci):
    cmd = "cat /sys/bus/pci/devices/{0}/virtfn0/uevent"
    output = connection.execute(cmd.format(pci))[1]

    pattern = "PCI_SLOT_NAME=({})".format(PciAddress.PCI_PATTERN_STR)
    m = re.search(pattern, output, re.MULTILINE)

    pf_vfs = {}
    if m:
        pf_vfs = {pci: m.group(1).rstrip()}

    LOG.info("pf_vfs:\n%s", pf_vfs)

    return pf_vfs


def parse_pod_file(file_path, nfvi_role='Sriov'):
    nodes = []
    nfvi_host = []

    LOG.info("Parsing pod file: %s", file_path)
    cfg = YamlFilePathWrapper(file_path).get_data()

    nodes.extend(node for node in cfg["nodes"] if str(node["role"]) != nfvi_role)
    nfvi_host.extend(node for node in cfg["nodes"] if str(node["role"]) == nfvi_role)
    if not nfvi_host:
        raise RuntimeError("Node role is other than SRIOV")

    host_mgmt = {
        'user': nfvi_host[0]['user'],
        'ip': str(IPNetwork(nfvi_host[0]['ip']).ip),
        'password': nfvi_host[0]['password'],
        'ssh_port': nfvi_host[0].get('ssh_port', 22),
        'key_filename': nfvi_host[0].get('key_filename')
    }

    return nodes, nfvi_host, host_mgmt


def query_mgmt_ip(connection, mac, cidr, node):
    connection.execute("fping -c 1 -g %s > /dev/null 2>&1" % cidr)
    out = connection.execute("ip neighbor | grep '%s'" % mac)[1]
    LOG.info("fping -c 1 -g %s > /dev/null 2>&1" % cidr)
    if not out.strip():
        time.sleep(WAIT_FOR_BOOT)  # FixMe: How to find if VM is booted?
        return None

    mgmt_ip = str(out.split(" ")[0]).strip()
    client = ssh.SSH.from_node(node, overrides={"ip": mgmt_ip})
    client.wait()
    return mgmt_ip


def find_mgmt_ip(connection, mac, cidr, node):
    def query():
        return query_mgmt_ip(connection, mac, cidr, node)

    search_iter = zip(range(10), iter(query, object()))
    return next((v for _, v in search_iter if v is not None), None)


def wait_for_vnfs_to_start(connection, servers, nodes):
    for node in nodes:
        vnf = servers[node["name"]]
        mgmt_ip = vnf["network_ports"]["mgmt"]["cidr"]
        ip = find_mgmt_ip(connection, node["mac"], mgmt_ip, node)
        if ip:
            node["ip"] = ip


def build_vnf_interfaces(vnf, ports):
    mgmt_ip = None
    interfaces = {}
    index = 0

    for key, vfs in vnf["network_ports"].items():
        if key == "mgmt":
            mgmt_ip = str(IPNetwork(vfs['cidr']).ip)
            continue

        vf = ports[vfs[0]]
        ip = IPNetwork(vf['cidr'])
        interfaces[key] = {
            'vpci': vf['vpci'],
            'driver': "%svf" % vf['driver'],
            'local_mac': vf['mac'],
            'dpdk_port_num': index,
            'local_ip': str(ip.ip),
            'netmask': str(ip.netmask),
        }
        index = index + 1

    return mgmt_ip, interfaces


def generate_vnf_instance(flavor, ports, ip, key, vnf, mac):
    mgmt_ip, interfaces = build_vnf_interfaces(vnf, ports)

    result = {
        "ip": mgmt_ip,
        "mac": mac,
        "host": ip,
        "user": flavor.get('user', 'root'),
        "interfaces": interfaces,
        "routing_table": [],
        # empty IPv6 routing table
        "nd_route_tbl": [],
        "name": key,
        "role": key,
    }

    try:
        result['key_filename'] = flavor['key_filename']
    except KeyError:
        pass

    try:
        result['password'] = flavor['password']
    except KeyError:
        pass

    LOG.info('%s', result)
    return result


class OvsDeploy(object):
    """ This class handles deploy of ovs dpdk
    Configuration: ovs_dpdk
    """

    OVS_DEPLOY_SCRIPT = "ovs_deploy.bash"

    def __init__(self, connection, bin_path, ovs_properties):
        self.connection = connection
        self.bin_path = bin_path
        self.ovs_properties = ovs_properties

    def prerequisite(self):
        pkgs = ["git", "build-essential", "pkg-config", "automake",
                "autotools-dev", "libltdl-dev", "cmake", "libnuma-dev",
                "libpcap-dev"]
        install_req_libs(self.connection, pkgs)

    def ovs_deploy(self):
        ovs_deploy = os.path.join(YARDSTICK_ROOT_PATH,
                                  "yardstick/resources/scripts/install/",
                                  self.OVS_DEPLOY_SCRIPT)

        if not os.path.isfile(ovs_deploy):
            return

        self.prerequisite()
        remote_ovs_deploy = os.path.join(self.bin_path, self.OVS_DEPLOY_SCRIPT)
        LOG.info(remote_ovs_deploy)
        self.connection.put(ovs_deploy, remote_ovs_deploy)

        http_proxy = os.environ.get('http_proxy', '')
        ovs_details = self.ovs_properties.get("version", {})
        ovs = ovs_details.get("ovs", "2.6.0")
        dpdk = ovs_details.get("dpdk", "16.11.1")

        cmd = "sudo -E %s --ovs='%s' --dpdk='%s' -p='%s'"
        cmd %= remote_ovs_deploy, ovs, dpdk, http_proxy
        self.connection.execute(cmd)
