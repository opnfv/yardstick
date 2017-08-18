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

import re
import time
import uuid
import logging
import xml.etree.ElementTree as ET

from yardstick.common.utils import make_dict_iter
from yardstick.common.utils import make_random_mac_addr
from yardstick.common.utils import make_random_octet
from yardstick.benchmark.contexts.standalone import StandaloneContext

log = logging.getLogger(__name__)

SRIOV_VM_TEMPLATE = """
<domain type="kvm">
 <name>vm1</name>
  <uuid>{random_uuid}</uuid>
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
      <address bus="0x00" domain="0x0000" function="0x0" slot="0x04" type="pci" />
    </disk>
    <controller index="0" model="ich9-ehci1" type="usb">
      <address bus="0x00" domain="0x0000" function="0x7" slot="0x05" type="pci" />
    </controller>
    <controller index="0" model="ich9-uhci1" type="usb">
      <master startport="0" />
      <address bus="0x00" domain="0x0000" function="0x0" multifunction="on" \
slot="0x05" type="pci" />
    </controller>
    <controller index="0" model="ich9-uhci2" type="usb">
      <master startport="2" />
      <address bus="0x00" domain="0x0000" function="0x1" slot="0x05" type="pci" />
    </controller>
    <controller index="0" model="ich9-uhci3" type="usb">
      <master startport="4" />
      <address bus="0x00" domain="0x0000" function="0x2" slot="0x05" type="pci" />
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
      <address bus="0x00" domain="0x0000" function="0x0" slot="0x02" type="pci" />
    </video>
    <memballoon model="virtio">
      <address bus="0x00" domain="0x0000" function="0x0" slot="0x06" type="pci" />
    </memballoon>
    <interface type="bridge">
      <mac address="{mac_addr}" />
      <source bridge="virbr0" />
    </interface>
   </devices>
</domain>
"""


class SriovStandaloneContext(StandaloneContext):

    CONTEXT_TYPE = 'SRIOV'
    VM_TEMPLATE = SRIOV_VM_TEMPLATE

    @staticmethod
    def add_sriov_interface(index, vf_pci, vf_mac, xml):
        root = ET.parse(xml)
        pattern = "0000:(\d+):(\d+).(\d+)"
        m = re.search(pattern, vf_pci, re.MULTILINE)

        device = root.find('devices')

        interface = ET.SubElement(device, 'interface')
        interface.set('managed', 'yes')
        interface.set('type', 'hostdev')

        mac = ET.SubElement(interface, 'mac')
        mac.set('address', vf_mac)
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
        vf_pci.set('slot', '{0:#04x}'.format(index + 7))
        vf_pci.set('function', '0x00')

        root.write(xml)

    def __init__(self):
        super(SriovStandaloneContext, self).__init__()
        self.vm_mac_address = None

    def _install_required_libraries(self):
        if not self.first_run:
            return

        self.first_run = False
        log.info("Installing required libraries...")
        cmd_list = [
            "apt-get update",
            "apt-get -y install qemu-kvm libvirt-bin",
            "apt-get -y install libvirt-dev  bridge-utils numactl",
        ]
        for cmd in cmd_list:
            self.ssh_helper.execute(cmd, log.debug)

    def _configure_nics_for_sriov(self):
        node0, nic_details = self.get_nic_details()
        phy_driver = node0['phy_driver']
        self.ssh_helper.execute("rmmod {0}".format(phy_driver))
        self.ssh_helper.execute("modprobe {0} num_vfs=1".format(phy_driver))

        nic_details['vf_pci'] = {}
        keys = 'pci', 'interface', 'vf_macs'
        for index, (pci, interface, vf_mac) in enumerate(make_dict_iter(nic_details, keys)):
            cmd = "echo 1 > /sys/bus/pci/devices/{0}/sriov_numvfs"
            self.ssh_helper.execute(cmd.format(pci))

            cmd = "ip link set {0} vf 0 mac {1}"
            err, out, _ = self.ssh_helper.execute(cmd.format(interface, vf_mac))

            time.sleep(3)
            nic_details['vf_pci'][index] = self.match_vf_value(pci, vf_mac)

        log.debug("Updated NIC details:\n%s", nic_details)

    def _setup_context(self):
        pass

    def _setup_xml_template(self):
        self._blacklist_driver()
        self._configure_nics_for_sriov()
        self._enable_interfaces()
        super(SriovStandaloneContext, self)._setup_xml_template()

    def _blacklist_driver(self):
        node0, nic_details = self.get_nic_details()
        phy_driver = node0['phy_driver']

        kwargs = {
            'blacklist_file': "/etc/modprobe.d/blacklist.conf",
            'vf_nic': "{0}vf".format(phy_driver),
        }

        lines = self.read_from_file(kwargs['blacklist_file'])
        if kwargs['vf_nic'] not in lines:
            cmd = "echo blacklist {vf_nic} >> {blacklist_file}"
            self.ssh_helper.execute(cmd.format(**kwargs))

    def _enable_interfaces(self):
        node0, nic_details = self.get_nic_details()
        keys = 'interface', 'vf_pci'
        for index, (interface, vf_pci) in enumerate(make_dict_iter(nic_details, keys)):
            self.add_sriov_interface(index, vf_pci, self.vm_mac_address, "/tmp/vm_sriov.xml")
            self.ssh_helper.execute("ifconfig {interface} up".format(interface=interface))

    def _make_vm_template(self):
        self.vm_mac_address = make_random_mac_addr(0, 0x24, 0x81, make_random_octet(high=0x7f))
        kwargs = {
            'random_uuid': uuid.uuid4(),
            'mac_addr': self.vm_mac_address,
            'vm_image': self.nodes[0]["images"],
        }
        return SRIOV_VM_TEMPLATE.format(**kwargs)

    def match_vf_value(self, value, vf_mac):
        vf_match = {"mac": vf_mac}

        vfs = self.ssh_helper.get_virtual_devices(value)
        log.info("vfs: %s", vfs)
        value_match = self.PCI_PATTERN.search(value).group(1)

        for vf_key, vf_value in vfs.items():
            key_match = self.PCI_PATTERN.search(vf_key)
            if key_match.group(1) == value_match:
                vf_match["vf_pci"] = str(vf_value)
                break

        return vf_match
