from __future__ import absolute_import
import sys
import os
import yaml
import re
import time
import xml.etree.ElementTree as ET
from yardstick import ssh
from yardstick.benchmark.contexts.standalone import StandaloneContext

BIN_PATH="/opt/isb_bin/"
DPDK_NIC_BIND="dpdk_nic_bind.py"

VM_TEMPLATE = """
<domain type="kvm">
 <name>vm1</name>
  <uuid>18230c0c-635d-4c50-b2dc-a213d30acb34</uuid>
  <memory unit="KiB">102400</memory>
  <currentMemory unit="KiB">102400</currentMemory>
  <memoryBacking>
    <hugepages />
  </memoryBacking>
  <vcpu placement="static">20</vcpu>
  <os>
    <type arch="x86_64" machine="pc-i440fx-utopic">hvm</type>
    <boot dev="hd" />
  </os>
  <features>
    <acpi />
    <apic />
    <pae />
  </features>
  <cpu match="exact" mode="custom">
    <model fallback="allow">SandyBridge</model>
    <topology cores="10" sockets="1" threads="2" />
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
      <address bus="0x00" domain="0x0000"
function="0x0" slot="0x04" type="pci" />
    </disk>
    <controller index="0" model="ich9-ehci1" type="usb">
      <address bus="0x00" domain="0x0000"
function="0x7" slot="0x05" type="pci" />
    </controller>
    <controller index="0" model="ich9-uhci1" type="usb">
      <master startport="0" />
      <address bus="0x00" domain="0x0000" function="0x0"
multifunction="on" slot="0x05" type="pci" />
    </controller>
    <controller index="0" model="ich9-uhci2" type="usb">
      <master startport="2" />
      <address bus="0x00" domain="0x0000"
function="0x1" slot="0x05" type="pci" />
    </controller>
    <controller index="0" model="ich9-uhci3" type="usb">
      <master startport="4" />
      <address bus="0x00" domain="0x0000"
function="0x2" slot="0x05" type="pci" />
    </controller>
    <controller index="0" model="pci-root" type="pci" />
      <serial type="pty">
      <target port="0" />
    </serial>
    <console type="pty">
      <target port="0" type="serial" />
    </console>
    <input bus="usb" type="tablet" />
    <input bus="ps2" type="mouse" />
    <input bus="ps2" type="keyboard" />
    <graphics autoport="yes" listen="0.0.0.0" port="-1" type="vnc" />
    <video>
      <model heads="1" type="cirrus" vram="16384" />
      <address bus="0x00" domain="0x0000"
function="0x0" slot="0x02" type="pci" />
    </video>
    <memballoon model="virtio">
      <address bus="0x00" domain="0x0000"
function="0x0" slot="0x06" type="pci" />
    </memballoon>
    <interface type="bridge">
      <mac address="00:00:00:08:3e:8c" />
      <source bridge="virbr0" />
    </interface>
   </devices>
</domain>
"""


class Sriov(StandaloneContext):
    def __init__(self):
        self.name = None
        self.file_path = None
        self.nodes = []
        self.vm_deploy = False
        self.sriov = []
        self.first_run = True
        '''self.dpdk_nic_bind = provision_tool(self.connection, os.path.join(s
elf.bin_path, "dpdk_nic_bind.py"))'''
        self.dpdk_nic_bind = BIN_PATH + DPDK_NIC_BIND
        self.user = ""
        self.ssh_ip = ""
        self.passwd = ""

    def init(self):
        self.parse_pod_and_get_data()
        '''if self.first_run is True:
            self.__install_req_libs()
        self.__setup_sriov_context(self.sriov[0]['phy_ports'],
                                   nic_details,
                                   self.sriov[0]['phy_driver'])'''

    def parse_pod_and_get_data(self, file_path):
        self.file_path = file_path
        print("parsing pod file: {0}".format(self.file_path))
        try:
            with open(self.file_path) as stream:
                cfg = yaml.load(stream)
        except IOError as ioerror:
            print("File {0} does not exist".format(self.file_path))
            raise ioerror
            #sys.exit(ioerror)

        self.nodes.extend([node for node in cfg["nodes"]
                           if node["role"] != "Sriov"])
        self.sriov.extend([node for node in cfg["nodes"]
                           if node["role"] == "Sriov"])
        self.user = self.sriov[0]['user']
        self.ssh_ip = self.sriov[0]['ip']
        self.passwd = self.sriov[0]['password']

    def ssh_remote_machine(self):
        self.connection = ssh.SSH(self.user, self.ssh_ip, password=self.passwd)
        self.connection.wait()

    def get_nic_details(self):
        nic_details = {}
        nic_details['interface'] = {}
        nic_details['pci'] = self.sriov[0]['phy_ports']
        nic_details['phy_driver'] = self.sriov[0]['phy_driver']
        nic_details['vf_macs'] = self.sriov[0]['vf_macs']
        '''Make sure that ports are bound to kernel drivers e.g. i40e/ixgbe'''
        #for i in range(len(nic_details['pci'])):
        for i, _ in enumerate(nic_details['pci']):
            err, out, _ = self.connection.execute(
                "{dpdk_nic_bind} --force -b {driver} {port}".format(
                    dpdk_nic_bind=self.dpdk_nic_bind,
                    driver=self.sriov[0]['phy_driver'],
                    port=self.sriov[0]['phy_ports'][i]))
            err, out, _ = self.connection.execute(
                "lshw -c network -businfo | grep '{port}'".format(
                    port=self.sriov[0]['phy_ports'][i]))
            a = out.split()[1]
            err, out, _ = self.connection.execute(
                "ip -s link show {interface}".format(
                    interface=out.split()[1]))
            nic_details['interface'][i] = str(a)
            '''#if err is 0:
                #try:
            #    print interface[i]
            #    nic_details['interface'][i] = str(a)
                #except:
                #    raise SystemExit()
            #else:
            #    print _
                #raise SystemExit()'''
        print("{0}".format(nic_details))
        return nic_details

    def install_req_libs(self):
        if self.first_run:
            print("inside install_req_libs")
            err, out, _ = self.connection.execute("apt-get update")
            print("{0}".format(out))
            err, out, _ = self.connection.execute(
                "apt-get -y install qemu-kvm libvirt-bin")
            print("{0}".format(out))
            err, out, _ = self.connection.execute(
                "apt-get -y install libvirt-dev  bridge-utils numactl")
            print("{0}".format(out))
            self.first_run = False

    def configure_nics_for_sriov(self, host_driver, nic_details):
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
            vf_pci = [[], []]
            vf_pci[i] = self.get_vf_datas(
                'vf_pci',
                nic_details['pci'][i],
                nic_details['vf_macs'][i])
            nic_details['vf_pci'][i] = vf_pci[i]
        print("{0}".format(nic_details))
        return nic_details

    def setup_sriov_context(self, pcis, nic_details, host_driver):
        blacklist = "/etc/modprobe.d/blacklist.conf"

        ''' 1 : Blacklist the vf driver in /etc/modprobe.d/blacklist.conf'''
        vfnic = "{0}vf".format(host_driver)
        lines = self.read_from_file(blacklist)
        if vfnic not in lines:
            vfblacklist = "blacklist {vfnic}".format(vfnic=vfnic)
            self.connection.execute(
                "echo {vfblacklist} >> {blacklist}".format(
                    vfblacklist=vfblacklist,
                    blacklist=blacklist))

        ''' 2 : modprobe host_driver with num_vfs '''
        nic_details = self.configure_nics_for_sriov(host_driver, nic_details)

        ''' 3: Setup vm_sriov.xml to launch VM.'''
        cfg_sriov = '/tmp/vm_sriov.xml'
        vm_sriov_xml = VM_TEMPLATE.format(vm_image=self.sriov[0]["images"])
        with open(cfg_sriov, 'w') as f:
            f.write(vm_sriov_xml)

        vf = nic_details['vf_pci']
        for index in range(len(nic_details['vf_pci'])):
            self.add_sriov_interface(
                index,
                vf[index]['vf_pci'],
                vf[index]['mac'],
                "/tmp/vm_sriov.xml")
            self.connection.execute(
                "ifconfig {interface} up".format(
                    interface=nic_details['interface'][index]))

        ''' 4: Create and start the VM'''
        self.connection.put(cfg_sriov, cfg_sriov)
        time.sleep(10)
        err, out = self.check_output("virsh list --name | grep -i vm1")
        if out == "vm1":
            print("VM is already present")
        else:
            ''' FIXME: launch through libvirt'''
            print("virsh create ..")
            err, out, _ = self.connection.execute(
                "virsh create /tmp/vm_sriov.xml")
            time.sleep(10)
            print("err : (0}".format(err))
            print("(0}".format(_))
            print("out : {0}".format(out))

        ''' 5: Tunning for better performace.'''
        self.pin_vcpu(pcis)
        self.connection.execute(
            "echo 1 > /sys/module/kvm/parameters/"
            "allow_unsafe_assigned_interrupts")
        self.connection.execute(
            "echo never > /sys/kernel/mm/transparent_hugepage/enabled")

    def add_sriov_interface(self, index, vf_pci, vfmac, xml):
        root = ET.parse(xml)
        pattern = "0000:(\d+):(\d+).(\d+)"
        m = re.search(pattern, vf_pci, re.MULTILINE)
        device = root.find('devices')

        interface = ET.SubElement(device, 'interface')
        interface.set('managed', 'yes')
        interface.set('type', 'hostdev')

        mac = ET.SubElement(interface, 'mac')
        mac.set('address', vfmac)
        source = ET.SubElement(interface, 'source')

        addr = ET.SubElement(source, "address")
        addr.set('domain', "0x0")
        addr.set('bus', "{0}".format(m.group(1)))
        addr.set('function', "{0}".format(m.group(3)))
        addr.set('slot', "{0}".format(m.group(2)))
        addr.set('type', "pci")

        vf_pci = ET.SubElement(interface, 'address')
        vf_pci.set('type', 'pci')
        vf_pci.set('domain', '0x0000')
        vf_pci.set('bus', '0x00')
        vf_pci.set('slot', '0x0{0}'.format(index + 7))
        vf_pci.set('function', '0x00')

        root.write(xml)

    ''' This is roughly compatible with check_output function in subprocess
     module which is only available in python 2.7.'''
    def check_output(self, cmd, stderr=None):
        '''Run a command and capture its output'''
        err, out, _ = self.connection.execute(cmd)
        return err, out

    def get_virtual_devices(self, pci):
        pf_vfs = {}
        err, extra_info = self.check_output(
            "cat /sys/bus/pci/devices/{0}/virtfn0/uevent".format(pci))
        pattern = "PCI_SLOT_NAME=(?P<name>[0-9:.\s.]+)"
        m = re.search(pattern, extra_info, re.MULTILINE)

        if m:
            pf_vfs.update({pci: str(m.group(1).rstrip())})
        print("pf_vfs : {0}".format(pf_vfs))
        return pf_vfs

    def get_vf_datas(self, key, value, vfmac):
        vfret = {}
        pattern = "0000:(\d+):(\d+).(\d+)"

        vfret["mac"] = vfmac
        vfs = self.get_virtual_devices(value)
        print("vfs: {0}".format(vfs))
        for k, v in vfs.items():
            m = re.search(pattern, k, re.MULTILINE)
            m1 = re.search(pattern, value, re.MULTILINE)
            if m.group(1) == m1.group(1):
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

    def pin_vcpu(self, pcis):
        key = "node0"
        nodes = self.numa_nodes()
        print("{0}".format(nodes))
        pattern1 = "0000:(\d+):(\d+).(\d+)"
        m1 = re.search(pattern1, pcis[0], re.MULTILINE)
        if m1 and int(m1.group(1)[0]) != 0:
            key = "node1"
        for i in range(0, 10):
            self.connection.execute(
                "virsh vcpupin vm1 {0} {1}".format(
                    i, nodes[key]['lcores'][i]))

    def numa_nodes(self):
        list_cores = {}
        nodes = [[], []]
        cores = self.check_output("dmidecode  | grep 'Core Count'")[
            1].split(os.linesep)
        num_cores = int(cores[0].split(":")[1])
        numas = self.check_output("numactl --hardware")[1]
        string, value = numas.split("available: ")
        val, other = value.split("nodes")
        val = int(val)
        for i in range(val):
            ''' Node 0'''
            node = numas.split("cpus: ")[1]
            node0 = node.split("node")
            nodes[i] = {}
            nodes[i]['cores'] = num_cores - 1
            nodes[i]['lcores'] = node0[0].split()
            list_cores.update({"node0": nodes[i]})
        print("{0}".format(list_cores))
        return list_cores

    def destroy_vm(self):
        host_driver = self.sriov[0]["phy_driver"]
        err, out = self.check_output("virsh list --name | grep -i vm1")
        print("{0}".format(out))
        if err == 0:
            self.connection.execute("virsh shutdown vm1")
            self.connection.execute("virsh destroy vm1")
            self.check_output("rmmod {0}".format(host_driver))[1].splitlines()
            self.check_output("modprobe {0}".format(host_driver))[
                1].splitlines()
        else:
            print("error : ", err)
