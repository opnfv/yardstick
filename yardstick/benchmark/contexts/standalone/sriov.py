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
import xml.etree.ElementTree as ET
from itertools import izip, chain, repeat

from yardstick import ssh
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.utils import provision_tool
from yardstick.benchmark.contexts.standalone import StandaloneContext

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
      <mac address="{mac_addr}" />
      <source bridge="br-int" />
      <model type='virtio'/>
    </interface>
   </devices>
</domain>
"""


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
        self.attrs = attrs

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
        self.user = self.sriov[0]['user']
        self.ssh_ip = self.sriov[0]['ip']
        if self.sriov[0]['auth_type'] == "password":
            self.passwd = self.sriov[0]['password']
        else:
            self.ssh_port = self.sriov[0]['ssh_port']
            self.key_filename = self.sriov[0]['key_filename']

    def ssh_remote_machine(self):
        if self.sriov[0]['auth_type'] == "password":
            self.connection = ssh.SSH(
                self.user,
                self.ssh_ip,
                password=self.passwd)
            self.connection.wait()
        else:
            if self.ssh_port is not None:
                ssh_port = self.ssh_port
            else:
                ssh_port = ssh.DEFAULT_PORT
            self.connection = ssh.SSH(
                self.user,
                self.ssh_ip,
                port=ssh_port,
                key_filename=self.key_filename)
            self.connection.wait()
        self.dpdk_nic_bind = provision_tool(
            self.connection,
            os.path.join(get_nsb_option("bin_path"), "dpdk_nic_bind.py"))

    def get_nic_details(self):
        nic_details = {}
        nic_details = {
            'interface': {},
            'pci': self.attrs['phy_ports'],
            'phy_driver': self.attrs['phy_driver'],
            'vf_macs': self.attrs['vf_macs']
        }
        #   Make sure that ports are bound to kernel drivers e.g. i40e/ixgbe
        for i, _ in enumerate(nic_details['pci']):
            err, out, _ = self.connection.execute(
                "{dpdk_nic_bind} --force -b {driver} {port}".format(
                    dpdk_nic_bind=self.dpdk_nic_bind,
                    driver=nic_details['phy_driver'],
                    port=nic_details['pci'][i]))
            err, out, _ = self.connection.execute(
                "lshw -c network -businfo | grep '{port}'".format(
                    port=nic_details['pci'][i]))
            a = out.split()[1]
            err, out, _ = self.connection.execute(
                "ip -s link show {interface}".format(
                    interface=out.split()[1]))
            nic_details['interface'][i] = str(a)
        log.info("{0}".format(nic_details))
        return nic_details

    def configure_nics_for_sriov(self, host_driver, nic_details):
        vf_pci = []
        self.connection.execute(
            "rmmod {0}".format(host_driver))[1].splitlines()
        self.connection.execute(
            "modprobe {0} num_vfs=1".format(host_driver))[1].splitlines()
        nic_details['vf_pci'] = {}
        for i in range(len(nic_details['pci'])):
            self.connection.execute(
                "echo 1 > /sys/bus/pci/devices/{0}/sriov_numvfs".format(
                    nic_details['pci'][i]))
            err, out, _ = self.connection.execute(
                "ip link set {interface} vf 0 mac {mac}".format(
                    interface=nic_details['interface'][i],
                    mac=nic_details['vf_macs'][i]))
            time.sleep(3)
            vf_pci.append(self.get_vf_datas(
                'vf_pci',
                nic_details['pci'][i],
                nic_details['vf_macs'][i],
                nic_details['interface'][i]))
            nic_details['vf_pci'][i] = vf_pci[i]
        log.debug("NIC DETAILS : {0}".format(nic_details))
        return nic_details, vf_pci

    def setup_sriov_context(self, pcis, nic_details, host_driver):
        blacklist = "/etc/modprobe.d/blacklist.conf"

        #   1 : Blacklist the vf driver in /etc/modprobe.d/blacklist.conf
        vfnic = "{0}vf".format(host_driver)
        lines = self.read_from_file(blacklist)
        if vfnic not in lines:
            vfblacklist = "blacklist {vfnic}".format(vfnic=vfnic)
            self.connection.execute(
                "echo {vfblacklist} >> {blacklist}".format(
                    vfblacklist=vfblacklist,
                    blacklist=blacklist))

        #   2 : modprobe host_driver with num_vfs
        nic_details, vf_list = self.configure_nics_for_sriov(host_driver, nic_details)

        nic = int(self.vm_flavor["nic"])
        for index, vfs in enumerate(list(izip(*[chain(vf_list, repeat(None, nic - 1))] * nic))):
            #   3: Setup vm_sriov.xml to launch VM
            cfg_sriov = '/tmp/vm_sriov_%s.xml' % str(index)
            mac = [0x00, 0x24, 0x81,
                   random.randint(0x00, 0x7f),
                   random.randint(0x00, 0xff),
                   random.randint(0x00, 0xff)]
            mac_address = ':'.join(map(lambda x: "%02x" % x, mac))
            vm_name = "vm_%s" % str(index)

            # vnf_desc
            log.info(self.attrs)
            log.info(self.vm_flavor)
            memory = self.vm_flavor.get('ram', '4096')
            extra_spec = self.vm_flavor.get('extra_spec', {})
            cpu = extra_spec.get('hw:cpu_cores', '2')
            socket = extra_spec.get('hw:cpu_sockets', '1')
            threads = extra_spec.get('hw:cpu_threads', '2')
            vcpu = int(cpu) * int(threads)

            vm_sriov_xml = VM_TEMPLATE.format(
                vm_name=vm_name,
                random_uuid=uuid.uuid4(),
                mac_addr=mac_address,
                memory=memory, vcpu=vcpu, cpu=cpu,
                socket=socket, threads=threads,
                vm_image=self.vm_flavor["images"])
            with open(cfg_sriov, 'w') as f:
                f.write(vm_sriov_xml)

            for i, vf in enumerate(vfs):
                self.add_sriov_interface(
                    index + i,
                    vf['vf_pci'],
                    vf['mac'],
                    "%s" % cfg_sriov)
                self.connection.execute(
                    "ifconfig {interface} up".format(
                        interface=vf['pf_if']))

            #   4: Create and start the VM
            self.connection.put(cfg_sriov, cfg_sriov)
            time.sleep(10)
            err, out = self.check_output("virsh list --name | grep -i %s" % vm_name)
            try:
                if out == vm_name:
                    log.info("VM '%s' is already present" % vm_name)
                else:
                    #    FIXME: launch through libvirt
                    log.info("virsh create ...")
                    err, out, _ = self.connection.execute(
                        "virsh create %s" % cfg_sriov)
                    time.sleep(10)
                    log.error("err : {0}".format(err))
                    log.error("{0}".format(_))
                    log.debug("out : {0}".format(out))
            except ValueError:
                    raise

            #    5: Tunning for better performace
            self.pin_vcpu(pcis, vm_name, vcpu)
            self.vm_names.append(vm_name)

        self.connection.execute(
            "echo 1 > /sys/module/kvm/parameters/"
            "allow_unsafe_assigned_interrupts")
        self.connection.execute(
            "echo never > /sys/kernel/mm/transparent_hugepage/enabled")

    def add_sriov_interface(self, index, vf_pci, vfmac, xml):
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
        vf_pci.set('domain', '0x0000')
        vf_pci.set('bus', '0x00')
        vf_pci.set('slot', '0x0{0}'.format(index + 7))
        vf_pci.set('function', '0x00')

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

    def pin_vcpu(self, pcis, vm_name, cpu):
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
        host_driver = self.attrs["phy_driver"]
        for vm in self.vm_names:
            err, out = self.check_output("virsh list --name | grep -i %s" % vm)
            log.info("{0}".format(out))
            if err == 0:
                self.connection.execute("virsh shutdown %s" % vm)
                self.connection.execute("virsh destroy %s" % vm)
                self.check_output("rmmod {0}".format(host_driver))[1].splitlines()
                self.check_output("modprobe {0}".format(host_driver))[
                    1].splitlines()
            else:
                log.error("error : {0}".format(err))
