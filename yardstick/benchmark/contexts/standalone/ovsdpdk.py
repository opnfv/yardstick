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
import time
import logging

from yardstick.benchmark.contexts.standalone import StandaloneContext

BIN_PATH = "/opt/isb_bin/"
DPDK_NIC_BIND = "dpdk_nic_bind.py"

log = logging.getLogger(__name__)

OVSDPDK_VM_TEMPLATE = """
<domain type='kvm'>
  <name>vm1</name>
  <uuid>18230c0c-635d-4c50-b2dc-a213d30acb34</uuid>
  <memory unit='KiB'>20971520</memory>
  <currentMemory unit="KiB">20971520</currentMemory>
  <memoryBacking>
    <hugepages/>
  </memoryBacking>
  <vcpu placement='static'>20</vcpu>
  <os>
    <type arch='x86_64' machine='pc'>hvm</type>
    <boot dev='hd'/>
  </os>
  <features>
    <acpi/>
    <apic/>
  </features>
  <cpu match="exact" mode='host-model'>
    <model fallback='allow'/>
    <topology sockets='1' cores='10' threads='2'/>
  </cpu>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none'/>
      <source file="{vm_image}"/>
      <target dev='vda' bus='virtio'/>
      <address bus="0x00" domain="0x0000"
      function="0x0" slot="0x04" type="pci" />
    </disk>
    <!--disk type='dir' device='disk'>
      <driver name='qemu' type='fat'/>
      <source dir='/opt/isb_bin/dpdk'/>
      <target dev='vdb' bus='virtio'/>
      <readonly/>
    </disk-->
    <interface type="bridge">
      <mac address="00:00:00:ab:cd:ef" />
      <source bridge="br-int" />
    </interface>
    <interface type='vhostuser'>
      <mac address='00:00:00:00:00:01'/>
      <source type='unix' path='/usr/local/var/run/openvswitch/dpdkvhostuser0' mode='client'/>
       <model type='virtio'/>
      <driver queues='4'>
        <host mrg_rxbuf='off'/>
      </driver>
    </interface>
    <interface type='vhostuser'>
      <mac address='00:00:00:00:00:02'/>
      <source type='unix' path='/usr/local/var/run/openvswitch/dpdkvhostuser1' mode='client'/>
      <model type='virtio'/>
      <driver queues='4'>
        <host mrg_rxbuf='off'/>
      </driver>
    </interface>
    <serial type='pty'>
      <target port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
    <graphics autoport="yes" listen="0.0.0.0" port="1" type="vnc" />
  </devices>
</domain>
"""


class OvsdpdkStandalone(StandaloneContext):

    CONTEXT_TYPE = 'OVSDPDK'
    VM_TEMPLATE = OVSDPDK_VM_TEMPLATE

    def _install_required_libraries(self):
        if not self.first_run:
            return

        self.first_run = False

        cmd_list = [
            "apt-get update",
            "apt-get -y install qemu-kvm libvirt-bin",
            "apt-get -y install libvirt-dev  bridge-utils numactl",
        ]
        for cmd in cmd_list:
            out = self.ssh_helper.execute(cmd)[1]
            log.debug(out)

    def _make_vm_template(self):
        return self.VM_TEMPLATE.format(vm_image=self.nodes[0]["images"])

    def _setup_ovs(self, vpcis):
        vpath = self.nodes[0]["vpath"]
        xargs_kill = "ps -ef | grep ovs | grep -v grep | awk '{print $2}' | xargs -r kill -9"

        create_from = os.path.join(vpath, 'etc/openvswitch/conf.db')
        create_to = os.path.join(vpath, 'share/openvswitch/vswitch.ovsschema')

        cmd_list = [
            "/usr/bin/chmod 0666 /dev/vfio/*",
            "/usr/bin/chmod a+x /dev/vfio",
            "pkill -9 ovs",
            xargs_kill,
            "killall -r 'ovs*'",
            "mkdir -p {0}/etc/openvswitch".format(vpath),
            "mkdir -p {0}/var/run/openvswitch".format(vpath),
            "rm {0}/etc/openvswitch/conf.db".format(vpath),
            "ovsdb-tool create {0} {1}".format(create_from, create_to),
            "modprobe vfio-pci",
            "chmod a+x /dev/vfio",
            "chmod 0666 /dev/vfio/*",
        ]

        for cmd in cmd_list:
            self.ssh_helper.execute(cmd)

        nic_bind_cmd = "/opt/isb_bin/dpdk_nic_bind.py --bind=vfio-pci {0}"
        for vpci in vpcis:
            self.ssh_helper.execute(nic_bind_cmd.format(vpci))

    def _start_ovs_serverswitch(self):
        ovs_sock_path = '/var/run/openvswitch/db.sock'
        log_path = '/var/log/openvswitch/ovs-vswitchd.log'

        ovs_other_config = "ovs-vsctl {0}set Open_vSwitch . other_config:{1}"
        detach_cmd = "ovs-vswitchd unix:{0}{1} --pidfile --detach --log-file={2}"

        cmd_list = {
            "mkdir -p /usr/local/var/run/openvswitch",
            "ovsdb-server --remote=punix:/usr/local{}  --pidfile --detach".format(ovs_sock_path),
            ovs_other_config.format("--no-wait ", "dpdk-init=true"),
            ovs_other_config.format("--no-wait ", "dpdk-lcore-mask=0x3"),
            ovs_other_config.format("--no-wait ", "dpdk-socket-mem='2048,0'"),
            detach_cmd.format(self.nodes[0]["vpath"], ovs_sock_path, log_path),
            ovs_other_config.format("", "pmd-cpu-mask=2C"),
        }

        for cmd in cmd_list:
            self.ssh_helper.execute(cmd)

    def _setup_ovs_bridge(self):
        ovs_add_port = "ovs-vsctl add-port {br} {port} -- set Interface {port} type={type_}"
        chmod_vpath = "chmod 0777 {0}/var/run/openvswitch/dpdkvhostuser*"

        cmd_list = [
            "ovs-vsctl del-br br0",
            "rm -rf /usr/local/var/run/openvswitch/dpdkvhostuser*",
            "ovs-vsctl add-br br0 -- set bridge br0 datapath_type=netdev",
            ovs_add_port.format(br='br0', port='dpdk0', type_='dpdk'),
            ovs_add_port.format(br='br0', port='dpdk1', type_='dpdk'),
            ovs_add_port.format(br='br0', port='dpdkhostuser0', type_='dpdkhostuser'),
            ovs_add_port.format(br='br0', port='dpdkhostuser1', type_='dpdkhostuser'),
            chmod_vpath.format(self.nodes[0]["vpath"]),
        ]

        for cmd in cmd_list:
            self.ssh_helper.execute(cmd)

    def _add_oflows(self):
        self.ssh_helper.execute("ovs-ofctl del-flows br0")
        for flow in self.nodes[0]["flow"]:
            self.ssh_helper.execute(flow)
            self.ssh_helper.execute("ovs-ofctl dump-flows br0")
            self.ssh_helper.execute("ovs-vsctl set Interface dpdk0 options:n_rxq=4")
            self.ssh_helper.execute("ovs-vsctl set Interface dpdk1 options:n_rxq=4")

    def _setup_context(self):
        node0, nic_details = self.get_nic_details()
        phy_ports = node0["phy_ports"]
        self._setup_ovs(phy_ports)
        self._start_ovs_serverswitch()
        time.sleep(5)
        self._setup_ovs_bridge()
        self._add_oflows()
