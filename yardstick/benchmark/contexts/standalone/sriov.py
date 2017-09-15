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
from netaddr import IPNetwork
import xml.etree.ElementTree as ET
from itertools import izip, chain, repeat
from collections import OrderedDict

from yardstick import ssh
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.utils import provision_tool
from yardstick.benchmark.contexts.standalone import StandaloneContext
from yardstick.orchestrator.heat import get_short_key_uuid

log = logging.getLogger(__name__)

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


class Sriov(StandaloneContext):
    def __init__(self, attrs):
        self.file_path = None
        self.sriov = []
        self.first_run = True
        self.dpdk_nic_bind = ""
        self.user = ""
        self.ssh_ip = ""
        self.passwd = ""
        self.ssh_port = ""
        self.auth_type = ""
        self.vm_names = []
        self.vm_flavor = attrs.get('flavor', {})
        self.ports = attrs.get('networks', {})
        self.attrs = attrs
        self.servers = attrs.get('servers', {})

    def init(self):
        log.debug("In init")
        self.parse_pod_and_get_data(self.file_path)

    def parse_pod_and_get_data(self, file_path):
        self.file_path = file_path
        log.debug("parsing pod file: {0}".format(self.file_path))
        try:
            with open(self.file_path) as stream:
                cfg = yaml.load(stream)
        except IOError:
            log.error("File {0} does not exist".format(self.file_path))
            raise

        self.sriov.extend([node for node in cfg["nodes"]
                           if node["role"] == "Sriov"])
        self.host_mgmt = { 'user': self.sriov[0]['user'],
                           'ip': str(IPNetwork(self.sriov[0]['ip']).ip),
                           'password': self.sriov[0]['password'],
                           'ssh_port': self.sriov[0].get('ssh_port', 22),
                           'key_filename': self.sriov[0]['key_filename']}

    def ssh_remote_machine(self):
        self.connection = ssh.SSH.from_node(self.host_mgmt)
        self.dpdk_nic_bind = provision_tool(
            self.connection,
            os.path.join(get_nsb_option("bin_path"), "dpdk_nic_bind.py"))

    def get_kernel_module(self, pci, driver):
        if not driver:
            out = self.connection.execute("lspci -k -s %s" % pci)[1]
            driver = out.split("Kernel modules:").pop().strip()
        return driver

    def get_nic_details(self):
        log.info(self.ports)
        for key, ports in self.ports.items():
            log.info(key)
            log.info(ports)
            if key != "mgmt":
                driver=self.get_kernel_module(ports['phy_port'], ports.get('phy_driver', None))
                err, out, _ = self.connection.execute(
                    "{dpdk_nic_bind} --force -b {driver} {port}".format(
                        dpdk_nic_bind=self.dpdk_nic_bind,
                        driver=driver,
                        port=ports['phy_port']))
                err, out, _ = self.connection.execute(
                    "lshw -c network -businfo | grep '{port}'".format(
                        port=ports['phy_port']))
                a = out.split()[1]
                err, out, _ = self.connection.execute(
                    "ip -s link show {interface}".format(
                        interface=out.split()[1]))
                self.ports[key].update({'interface': str(a)})
                self.ports[key].update({'driver': driver})
        log.info("{0}".format(self.ports))

    def get_mac_address(self):
        mac = [0x52, 0x54, 0x00,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        mac_address = ':'.join(map(lambda x: "%02x" % x, mac))
        return mac_address

    def configure_nics_for_sriov(self):
        drivers = []
        for key, ports in self.ports.items():
            if key != 'mgmt':
                vf_pci = []
                log.info(ports)
                if ports.get('driver') not in drivers:
                    host_driver = ports['driver']
                    self.connection.execute("rmmod %s" % host_driver)
                    self.connection.execute("modprobe %s num_vfs=1" % host_driver)
                    self.connection.execute("rmmod %svf" % host_driver)
                    drivers.append(host_driver)

                self.connection.execute(
                    "echo 1 > /sys/bus/pci/devices/{0}/sriov_numvfs".format(
                        ports.get('phy_port')))
                mac = self.get_mac_address()
                err, out, _ = self.connection.execute(
                    "ip link set {interface} vf 0 mac {mac}".format(
                        interface=ports.get('interface'),mac=mac))
                time.sleep(3)
                vf_pci = self.get_vf_datas(
                    'vf_pci', ports.get('phy_port'), mac, ports.get('interface'))
                self.ports[key].update({'vf_pci': vf_pci})
                self.ports[key].update({'mac': mac})
        log.info("Ports %s" % self.ports)

    def get_mgmt_ip(self, mac, ip, node):
        mgmtip = None
        times = 10
        while not mgmtip and times:
            self.connection.execute("fping -c 1 -g 10.223.166.0/24 > /dev/null 2>&1")
            err, out, _ = self.connection.execute("ip neighbor | grep '%s'" % mac)
            if not err:
               mgmtip = str(out.split(" ")[0]).strip()
               log.info(ip)
               client = ssh.SSH.from_node(node, overrides={"ip": mgmtip})
               client.wait()
               break
            time.sleep(WAIT_FOR_BOOT) # FixMe: How to find if VM is booted?
            times = times - 1
        return mgmtip

    def wait_for_vnfs_to_start(self, nodes):
        for node in nodes:
            vnf = self.servers[node["name"]]
            mgmtip = vnf["network_ports"]["mgmt"]["cidr"]
            ip = self.get_mgmt_ip(node["mac"], mgmtip, node)
            if ip:
                node["ip"] = ip
        return nodes

    def setup_sriov_context(self):
        nodes = []

        #   1 : modprobe host_driver with num_vfs
        self.configure_nics_for_sriov()

        serverslist = OrderedDict(self.servers)
        for key, vnf in serverslist.items():
            index = serverslist.keys().index(key)
            cfg_sriov = '/tmp/vm_sriov_%s.xml' % str(index)
            vm_name = "vm_%s" % str(index)

            # 2: Cleanup already available VMs
            status = self.check_output("virsh list --name | grep -i %s" % vm_name)[0]
            if not status:
                log.info("VM '%s' is already present.. destroying" % vm_name)
                self.connection.execute("virsh destroy %s" % vm_name)

            #   3: Setup vm_sriov.xml to launch VM
            # vnf_desc
            memory = self.vm_flavor.get('ram', '4096')
            extra_spec = self.vm_flavor.get('extra_specs', {})
            cpu = extra_spec.get('hw:cpu_cores', '2')
            socket = extra_spec.get('hw:cpu_sockets', '1')
            threads = extra_spec.get('hw:cpu_threads', '2')
            vcpu = int(cpu) * int(threads)
            numa_cpus = '0-%s' % (vcpu - 1)

            mac = self.get_mac_address()

            # build snapshot image
            image = "/var/lib/libvirt/images/%s.qcow2" % index
            self.connection.execute("rm %s" % image)
            self.connection.execute(
                "qemu-img create -f qcow2 -o backing_file=%s %s" % (self.vm_flavor["images"],
                                                                    image))
            vm_sriov_xml = VM_TEMPLATE.format(
                vm_name=vm_name,
                random_uuid=uuid.uuid4(),
                mac_addr=mac,
                memory=memory, vcpu=vcpu, cpu=cpu,
                numa_cpus=numa_cpus,
                socket=socket, threads=threads,
                vm_image=image)
            with open(cfg_sriov, 'w') as f:
                f.write(vm_sriov_xml)

            ordervnf = OrderedDict(vnf["network_ports"])
            for vkey, vfs in ordervnf.items():
                idx = ordervnf.keys().index(vkey)
                if vkey != "mgmt":
                    vf = self.ports[vfs[0]]
                    vpci = self.spilt_pci_addr(vf['vpci'])
                    # Generate the vpci for the interfaces
                    vpci[2] = format((index + 10) + (idx), '#04x')[2:]
                    vf['vpci'] = \
                        "{}:{}:{}.{}".format(vpci[0], vpci[1], vpci[2], vpci[3])
                    self.add_sriov_interface(
                            self.spilt_pci_addr(vf['vpci']),
                            vf['vf_pci']['vf_pci'],
                            vf['mac'],
                            "%s" % cfg_sriov)
                    self.connection.execute(
                            "ifconfig {interface} up".format(
                                interface=vf['interface']))

            #   4: Create and start the VM
            self.connection.put(cfg_sriov, cfg_sriov)
            time.sleep(10)
            try:
                #    FIXME: launch through libvirt
                log.info("virsh create ...")
                err, out, _ = self.connection.execute(
                    "virsh create %s" % cfg_sriov)
                log.error("err : {0}".format(err))
                log.error("{0}".format(_))
                log.debug("out : {0}".format(out))
            except ValueError:
                    raise

            #    5: Tunning for better performace
            self.pin_vcpu(vm_name, vcpu)
            self.vm_names.append(vm_name)
            nodes.append(self.generate_vnf_instance(key, vnf, mac))

        self.connection.execute(
            "echo 1 > /sys/module/kvm/parameters/"
            "allow_unsafe_assigned_interrupts")
        self.connection.execute(
            "echo never > /sys/kernel/mm/transparent_hugepage/enabled")
        return nodes

    def build_vnf_interfaces(self, vnf):
        interfaces = {}
        index = 0

        for key, vfs in vnf["network_ports"].items():
            if key != "mgmt":
                vf = self.ports[vfs[0]]
                ip = IPNetwork(vf['cidr'])
                interfaces.update({key: {}})
                interfaces[key].update({'vpci': vf['vpci']})
                interfaces[key].update({'driver': "%svf" % vf['driver']})
                interfaces[key].update({'local_mac': vf['mac']})
                interfaces[key].update({'dpdk_port_num': index})
                interfaces[key].update({'local_ip': str(ip.ip)})
                interfaces[key].update({'netmask': str(ip.netmask)})
                index = index + 1
                log.info(vf['cidr'])
                log.info(IPNetwork(vf['cidr']).ip)
                log.info(interfaces[key]['local_ip'])
            else:
                mgmtip = str(IPNetwork(vfs['cidr']).ip)

        return mgmtip, interfaces

    def generate_vnf_instance(self, key, vnf, mac):
        key_filename = "/root/.ssh/id_rsa"
        mgmtip, interfaces = self.build_vnf_interfaces(vnf)
        result = {
            "ip": mgmtip,
            "mac": mac,
            "host": self.host_mgmt['ip'],
            "user": self.vm_flavor.get('user', 'root'),
            "password": self.vm_flavor.get('password', 'root'),
            "key_filename": key_filename,
            "interfaces": interfaces,
            "routing_table": [],
            # empty IPv6 routing table
            "nd_route_tbl": [],
            "name": key, "role": key
        }

        log.info(result)
        return result

    def add_sriov_interface(self, vpci, vf_pci, vfmac, xml):
        root = ET.parse(xml)
        m = self.spilt_pci_addr(vf_pci)
        log.info(m)
        device = root.find('devices')

        interface = ET.SubElement(device, 'interface')
        interface.set('managed', 'yes')
        interface.set('type', 'hostdev')

        mac = ET.SubElement(interface, 'mac')
        mac.set('address', vfmac)
        source = ET.SubElement(interface, 'source')

        addr = ET.SubElement(source, "address")
        addr.set('domain', "0x0")
        addr.set('bus', "{0}".format(m[1]))
        addr.set('function', "{0}".format(m[3]))
        addr.set('slot', "0x{0}".format(m[2]))
        addr.set('type', "pci")

        vf_pci = ET.SubElement(interface, 'address')
        vf_pci.set('type', 'pci')
        vf_pci.set('domain', '0x%s' % vpci[0])
        vf_pci.set('bus', '0x%s' % vpci[1])
        vf_pci.set('slot', '0x%s' % vpci[2])
        vf_pci.set('function', '0x%s' % vpci[3])

        root.write(xml)

    #   This is roughly compatible with check_output function in subprocess
    #   module which is only available in python 2.7
    def check_output(self, cmd, stderr=None):
        #   Run a command and capture its output
        err, out, _ = self.connection.execute(cmd)
        return err, out

    def get_virtual_devices(self, pci):
        pf_vfs = {}
        err, extra_info = self.check_output(
            "cat /sys/bus/pci/devices/{0}/virtfn0/uevent".format(pci))
        pattern = "PCI_SLOT_NAME=(?P<name>[0-9]+:[0-9a-f]+:[0-9a-f]+.[0-9]+)"
        m = re.search(pattern, extra_info, re.MULTILINE)

        if m:
            pf_vfs.update({pci: str(m.group(1).rstrip())})
        log.info("pf_vfs : {0}".format(pf_vfs))
        return pf_vfs

    def spilt_pci_addr(self, pci):
        m = pci.split(":")
        slot = m[2].split(".")
        return [m[0], m[1], slot[0], slot[1]]

    def get_vf_datas(self, key, value, vfmac, pfif):
        vfret = {}
        vfret["mac"] = vfmac
        vfret["pf_if"] = pfif
        vfs = self.get_virtual_devices(value)
        log.info("vfs: {0}".format(vfs))
        for k, v in vfs.items():
            m = self.spilt_pci_addr(str(k))
            m1 = self.spilt_pci_addr(str(value))
            if m[1] == m1[1]:
                vfret["vf_pci"] = str(v)
                break

        return vfret

    def read_from_file(self, filename):
        data = ""
        with open(filename, 'r') as the_file:
            data = the_file.read()
        return data

    def write_to_file(self, filename, content):
        with open(filename, 'w') as the_file:
            the_file.write(content)

    def pin_vcpu(self, vm_name, cpu):
        nodes = self.get_numa_nodes()
        log.info("{0}".format(nodes))
        num_nodes = len(nodes)
        for i in range(0, int(cpu)):
            self.connection.execute(
                "virsh vcpupin {0} {1} {2}".format(
                    vm_name, i, nodes[str(num_nodes - 1)][i % len(nodes[str(num_nodes - 1)])]))

    def get_numa_nodes(self):
        nodes_sysfs = glob.iglob("/sys/devices/system/node/node*")
        nodes = {}
        for node_sysfs in nodes_sysfs:
            num = os.path.basename(node_sysfs).replace("node", "")
            with open(os.path.join(node_sysfs, "cpulist")) as cpulist_file:
                cpulist = cpulist_file.read().strip()
            nodes[num] = self.split_cpu_list(cpulist)
        log.info("nodes: {0}".format(nodes))
        return nodes

    def split_cpu_list(self, cpu_list):
        if cpu_list:
            ranges = cpu_list.split(',')
            bounds = ([int(b) for b in r.split('-')] for r in ranges)
            range_objects =\
                (range(bound[0], bound[1] + 1 if len(bound) == 2
                 else bound[0] + 1) for bound in bounds)

            return sorted(itertools.chain.from_iterable(range_objects))
        else:
            return []

    def destroy_vm(self):
        for vm in self.vm_names:
            err, out = self.check_output("virsh list --name | grep -i %s" % vm)
            log.info("{0}".format(out))
            if err == 0:
                self.connection.execute("virsh shutdown %s" % vm)
                self.connection.execute("virsh destroy %s" % vm)
            else:
                log.error("error : {0}".format(err))
