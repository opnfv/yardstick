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
import re
import time
import uuid
import random
import logging
import errno

from netaddr import IPNetwork
import xml.etree.ElementTree as ET

from yardstick import ssh
from yardstick.common import constants
from yardstick.common import exceptions
from yardstick.common.yaml_loader import yaml_load
from yardstick.network_services.utils import PciAddress
from yardstick.network_services.helpers.cpu import CpuSysCores


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
  <vcpu cpuset='{cpuset}'>{vcpu}</vcpu>
 {cputune}
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
    <graphics autoport="yes" listen="0.0.0.0" port="-1" type="vnc" />
    <interface type="bridge">
      <mac address='{mac_addr}'/>
      <source bridge="br-int" />
      <model type='virtio'/>
    </interface>
    <serial type='pty'>
      <target port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
  </devices>
</domain>
"""
WAIT_FOR_BOOT = 30


class Libvirt(object):
    """ This class handles all the libvirt updates to lauch VM
    """

    @staticmethod
    def check_if_vm_exists_and_delete(vm_name, connection):
        cmd_template = "virsh list --name | grep -i %s"
        status = connection.execute(cmd_template % vm_name)[0]
        if status == 0:
            LOG.info("VM '%s' is already present... destroying", vm_name)
            connection.execute("virsh destroy %s" % vm_name)

    @staticmethod
    def virsh_create_vm(connection, cfg):
        LOG.info('VM create, XML config: %s', cfg)
        status, _, error = connection.execute('virsh create %s' % cfg)
        if status:
            raise exceptions.LibvirtCreateError(error=error)

    @staticmethod
    def virsh_destroy_vm(vm_name, connection):
        LOG.info('VM destroy, VM name: %s', vm_name)
        status, _, error = connection.execute('virsh destroy %s' % vm_name)
        if status:
            LOG.warning('Error destroying VM %s. Error: %s', vm_name, error)

    @staticmethod
    def _add_interface_address(interface, pci_address):
        """Add a PCI 'address' XML node

        <address type='pci' domain='0x0000' bus='0x00' slot='0x08'
         function='0x0'/>

        Refence: https://software.intel.com/en-us/articles/
                 configure-sr-iov-network-virtual-functions-in-linux-kvm
        """
        vm_pci = ET.SubElement(interface, 'address')
        vm_pci.set('type', 'pci')
        vm_pci.set('domain', '0x{}'.format(pci_address.domain))
        vm_pci.set('bus', '0x{}'.format(pci_address.bus))
        vm_pci.set('slot', '0x{}'.format(pci_address.slot))
        vm_pci.set('function', '0x{}'.format(pci_address.function))
        return vm_pci

    @classmethod
    def add_ovs_interface(cls, vpath, port_num, vpci, vports_mac, xml_str):
        """Add a DPDK OVS 'interface' XML node in 'devices' node

        <devices>
            <interface type='vhostuser'>
                <mac address='00:00:00:00:00:01'/>
                <source type='unix' path='/usr/local/var/run/openvswitch/
                 dpdkvhostuser0' mode='client'/>
                <model type='virtio'/>
                <driver queues='4'>
                    <host mrg_rxbuf='off'/>
                </driver>
                <address type='pci' domain='0x0000' bus='0x00' slot='0x03'
                 function='0x0'/>
            </interface>
            ...
        </devices>

        Reference: http://docs.openvswitch.org/en/latest/topics/dpdk/
                   vhost-user/
        """

        vhost_path = ('{0}/var/run/openvswitch/dpdkvhostuser{1}'.
                      format(vpath, port_num))
        root = ET.fromstring(xml_str)
        pci_address = PciAddress(vpci.strip())
        device = root.find('devices')

        interface = ET.SubElement(device, 'interface')
        interface.set('type', 'vhostuser')
        mac = ET.SubElement(interface, 'mac')
        mac.set('address', vports_mac)

        source = ET.SubElement(interface, 'source')
        source.set('type', 'unix')
        source.set('path', vhost_path)
        source.set('mode', 'client')

        model = ET.SubElement(interface, 'model')
        model.set('type', 'virtio')

        driver = ET.SubElement(interface, 'driver')
        driver.set('queues', '4')

        host = ET.SubElement(driver, 'host')
        host.set('mrg_rxbuf', 'off')

        cls._add_interface_address(interface, pci_address)

        return ET.tostring(root)

    @classmethod
    def add_sriov_interfaces(cls, vm_pci, vf_pci, vf_mac, xml_str):
        """Add a SR-IOV 'interface' XML node in 'devices' node

        <devices>
           <interface type='hostdev' managed='yes'>
             <source>
               <address type='pci' domain='0x0000' bus='0x00' slot='0x03'
                function='0x0'/>
             </source>
             <mac address='52:54:00:6d:90:02'>
             <address type='pci' domain='0x0000' bus='0x02' slot='0x04'
              function='0x1'/>
           </interface>
           ...
         </devices>

        Reference: https://access.redhat.com/documentation/en-us/
            red_hat_enterprise_linux/6/html/
            virtualization_host_configuration_and_guest_installation_guide/
            sect-virtualization_host_configuration_and_guest_installation_guide
            -sr_iov-how_sr_iov_libvirt_works
        """

        root = ET.fromstring(xml_str)
        device = root.find('devices')

        interface = ET.SubElement(device, 'interface')
        interface.set('managed', 'yes')
        interface.set('type', 'hostdev')

        mac = ET.SubElement(interface, 'mac')
        mac.set('address', vf_mac)

        source = ET.SubElement(interface, 'source')
        pci_address = PciAddress(vf_pci.strip())
        cls._add_interface_address(source, pci_address)

        pci_vm_address = PciAddress(vm_pci.strip())
        cls._add_interface_address(interface, pci_vm_address)

        return ET.tostring(root)

    @staticmethod
    def create_snapshot_qemu(connection, index, vm_image):
        # build snapshot image
        image = "/var/lib/libvirt/images/%s.qcow2" % index
        connection.execute("rm %s" % image)
        qemu_template = "qemu-img create -f qcow2 -o backing_file=%s %s"
        connection.execute(qemu_template % (vm_image, image))

        return image

    @classmethod
    def build_vm_xml(cls, connection, flavor, vm_name, index):
        """Build the XML from the configuration parameters"""
        memory = flavor.get('ram', '4096')
        extra_spec = flavor.get('extra_specs', {})
        cpu = extra_spec.get('hw:cpu_cores', '2')
        socket = extra_spec.get('hw:cpu_sockets', '1')
        threads = extra_spec.get('hw:cpu_threads', '2')
        vcpu = int(cpu) * int(threads)
        numa_cpus = '0-%s' % (vcpu - 1)
        hw_socket = flavor.get('hw_socket', '0')
        cpuset = Libvirt.pin_vcpu_for_perf(connection, hw_socket)

        cputune = extra_spec.get('cputune', '')
        mac = StandaloneContextHelper.get_mac_address(0x00)
        image = cls.create_snapshot_qemu(connection, index,
                                         flavor.get("images", None))
        vm_xml = VM_TEMPLATE.format(
            vm_name=vm_name,
            random_uuid=uuid.uuid4(),
            mac_addr=mac,
            memory=memory, vcpu=vcpu, cpu=cpu,
            numa_cpus=numa_cpus,
            socket=socket, threads=threads,
            vm_image=image, cpuset=cpuset, cputune=cputune)

        return vm_xml, mac

    @staticmethod
    def update_interrupts_hugepages_perf(connection):
        connection.execute("echo 1 > /sys/module/kvm/parameters/allow_unsafe_assigned_interrupts")
        connection.execute("echo never > /sys/kernel/mm/transparent_hugepage/enabled")

    @classmethod
    def pin_vcpu_for_perf(cls, connection, socket='0'):
        threads = ""
        sys_obj = CpuSysCores(connection)
        soc_cpu = sys_obj.get_core_socket()
        sys_cpu = int(soc_cpu["cores_per_socket"])
        socket = str(socket)
        cores = "%s-%s" % (soc_cpu[socket][0], soc_cpu[socket][sys_cpu - 1])
        if int(soc_cpu["thread_per_core"]) > 1:
            threads = "%s-%s" % (soc_cpu[socket][sys_cpu], soc_cpu[socket][-1])
        cpuset = "%s,%s" % (cores, threads)
        return cpuset

    @classmethod
    def write_file(cls, file_name, xml_str):
        """Dump a XML string to a file"""
        root = ET.fromstring(xml_str)
        et = ET.ElementTree(element=root)
        et.write(file_name, encoding='utf-8', method='xml')


class StandaloneContextHelper(object):
    """ This class handles all the common code for standalone
    """
    def __init__(self):
        self.file_path = None
        super(StandaloneContextHelper, self).__init__()

    @staticmethod
    def install_req_libs(connection, extra_pkgs=None):
        extra_pkgs = extra_pkgs or []
        pkgs = ["qemu-kvm", "libvirt-bin", "bridge-utils", "numactl", "fping"]
        pkgs.extend(extra_pkgs)
        cmd_template = "dpkg-query -W --showformat='${Status}\\n' \"%s\"|grep 'ok installed'"
        for pkg in pkgs:
            if connection.execute(cmd_template % pkg)[0]:
                connection.execute("apt-get update")
                connection.execute("apt-get -y install %s" % pkg)

    @staticmethod
    def get_kernel_module(connection, pci, driver):
        if not driver:
            out = connection.execute("lspci -k -s %s" % pci)[1]
            driver = out.split("Kernel modules:").pop().strip()
        return driver

    @classmethod
    def get_nic_details(cls, connection, networks, dpdk_devbind):
        for key, ports in networks.items():
            if key == "mgmt":
                continue

            phy_ports = ports['phy_port']
            phy_driver = ports.get('phy_driver', None)
            driver = cls.get_kernel_module(connection, phy_ports, phy_driver)

            # Make sure that ports are bound to kernel drivers e.g. i40e/ixgbe
            bind_cmd = "{dpdk_devbind} --force -b {driver} {port}"
            lshw_cmd = "lshw -c network -businfo | grep '{port}'"
            link_show_cmd = "ip -s link show {interface}"

            cmd = bind_cmd.format(dpdk_devbind=dpdk_devbind,
                                  driver=driver, port=ports['phy_port'])
            connection.execute(cmd)

            out = connection.execute(lshw_cmd.format(port=phy_ports))[1]
            interface = out.split()[1]

            connection.execute(link_show_cmd.format(interface=interface))

            ports.update({
                'interface': str(interface),
                'driver': driver
            })
        LOG.info(networks)

        return networks

    @staticmethod
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

    def read_config_file(self):
        """Read from config file"""

        with open(self.file_path) as stream:
            LOG.info("Parsing pod file: %s", self.file_path)
            cfg = yaml_load(stream)
        return cfg

    def parse_pod_file(self, file_path, nfvi_role='Sriov'):
        self.file_path = file_path
        nodes = []
        nfvi_host = []
        try:
            cfg = self.read_config_file()
        except IOError as io_error:
            if io_error.errno != errno.ENOENT:
                raise
            self.file_path = os.path.join(constants.YARDSTICK_ROOT_PATH,
                                          file_path)
            cfg = self.read_config_file()

        nodes.extend([node for node in cfg["nodes"] if str(node["role"]) != nfvi_role])
        nfvi_host.extend([node for node in cfg["nodes"] if str(node["role"]) == nfvi_role])
        if not nfvi_host:
            raise("Node role is other than SRIOV")

        host_mgmt = {'user': nfvi_host[0]['user'],
                     'ip': str(IPNetwork(nfvi_host[0]['ip']).ip),
                     'password': nfvi_host[0]['password'],
                     'ssh_port': nfvi_host[0].get('ssh_port', 22),
                     'key_filename': nfvi_host[0].get('key_filename')}

        return [nodes, nfvi_host, host_mgmt]

    @staticmethod
    def get_mac_address(end=0x7f):
        mac = [0x52, 0x54, 0x00,
               random.randint(0x00, end),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        mac_address = ':'.join('%02x' % x for x in mac)
        return mac_address

    @staticmethod
    def get_mgmt_ip(connection, mac, cidr, node):
        mgmtip = None
        times = 10
        while not mgmtip and times:
            connection.execute("fping -c 1 -g %s > /dev/null 2>&1" % cidr)
            out = connection.execute("ip neighbor | grep '%s'" % mac)[1]
            LOG.info("fping -c 1 -g %s > /dev/null 2>&1", cidr)
            if out.strip():
                mgmtip = str(out.split(" ")[0]).strip()
                client = ssh.SSH.from_node(node, overrides={"ip": mgmtip})
                client.wait()
                break

            time.sleep(WAIT_FOR_BOOT)  # FixMe: How to find if VM is booted?
            times = times - 1
        return mgmtip

    @classmethod
    def wait_for_vnfs_to_start(cls, connection, servers, nodes):
        for node in nodes:
            vnf = servers[node["name"]]
            mgmtip = vnf["network_ports"]["mgmt"]["cidr"]
            ip = cls.get_mgmt_ip(connection, node["mac"], mgmtip, node)
            if ip:
                node["ip"] = ip
        return nodes


class Server(object):
    """ This class handles geting vnf nodes
    """

    @staticmethod
    def build_vnf_interfaces(vnf, ports):
        interfaces = {}
        index = 0

        for key, vfs in vnf["network_ports"].items():
            if key == "mgmt":
                mgmtip = str(IPNetwork(vfs['cidr']).ip)
                continue

            vf = ports[vfs[0]]
            ip = IPNetwork(vf['cidr'])
            interfaces.update({
                key: {
                    'vpci': vf['vpci'],
                    'driver': "%svf" % vf['driver'],
                    'local_mac': vf['mac'],
                    'dpdk_port_num': index,
                    'local_ip': str(ip.ip),
                    'netmask': str(ip.netmask)
                    },
            })
            index = index + 1

        return mgmtip, interfaces

    @classmethod
    def generate_vnf_instance(cls, flavor, ports, ip, key, vnf, mac):
        mgmtip, interfaces = cls.build_vnf_interfaces(vnf, ports)

        result = {
            "ip": mgmtip,
            "mac": mac,
            "host": ip,
            "user": flavor.get('user', 'root'),
            "interfaces": interfaces,
            "routing_table": [],
            # empty IPv6 routing table
            "nd_route_tbl": [],
            "name": key, "role": key
        }

        try:
            result['key_filename'] = flavor['key_filename']
        except KeyError:
            pass

        try:
            result['password'] = flavor['password']
        except KeyError:
            pass
        LOG.info(result)
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
        StandaloneContextHelper.install_req_libs(self.connection, pkgs)

    def ovs_deploy(self):
        ovs_deploy = os.path.join(constants.YARDSTICK_ROOT_PATH,
                                  "yardstick/resources/scripts/install/",
                                  self.OVS_DEPLOY_SCRIPT)
        if os.path.isfile(ovs_deploy):
            self.prerequisite()
            remote_ovs_deploy = os.path.join(self.bin_path, self.OVS_DEPLOY_SCRIPT)
            LOG.info(remote_ovs_deploy)
            self.connection.put(ovs_deploy, remote_ovs_deploy)

            http_proxy = os.environ.get('http_proxy', '')
            ovs_details = self.ovs_properties.get("version", {})
            ovs = ovs_details.get("ovs", "2.6.0")
            dpdk = ovs_details.get("dpdk", "16.11.1")

            cmd = "sudo -E %s --ovs='%s' --dpdk='%s' -p='%s'" % (remote_ovs_deploy,
                                                                 ovs, dpdk, http_proxy)
            exit_status, _, stderr = self.connection.execute(cmd)
            if exit_status:
                raise exceptions.OVSDeployError(stderr=stderr)
