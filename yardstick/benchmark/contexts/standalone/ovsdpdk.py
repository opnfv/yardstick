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
import time
import glob
import uuid
import random
import itertools
import logging

from yardstick import ssh
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.utils import provision_tool
from yardstick.benchmark.contexts.standalone import StandaloneContext

log = logging.getLogger(__name__)

VM_TEMPLATE = """
<domain type='kvm'>
 <name>{vm_name}</name>
  <uuid>{random_uuid}</uuid>
  <memory unit="MB">{memory}</memory>
  <currentMemory unit="MB">{memory}</currentMemory>
  <memoryBacking>
    <hugepages/>
  </memoryBacking>
  <vcpu placement='static'>{vcpu}</vcpu>
  <os>
    <type arch='x86_64' machine='pc'>hvm</type>
    <boot dev='hd'/>
  </os>
  <features>
    <acpi/>
    <apic/>
  </features>
  <cpu mode='host-passthrough'>
    <topology cores="{cpu}" sockets="{socket}" threads="{threads}" />
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
    </disk>
    <interface type="bridge">
      <source bridge="br-int" />
      <model type='virtio'/>
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


class Ovsdpdk(StandaloneContext):
    def __init__(self, attrs):
        self.name = None
        self.file_path = None
        self.ovs = []
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
        '''initializes itself'''
        log.debug("In init")
        self.parse_pod_and_get_data()

    def parse_pod_and_get_data(self, file_path):
        self.file_path = file_path
        print("parsing pod file: {0}".format(self.file_path))
        try:
            with open(self.file_path) as stream:
                cfg = yaml.load(stream)
        except IOError:
            print("File {0} does not exist".format(self.file_path))
            raise

        self.ovs.extend([node for node in cfg["nodes"]
                         if node["role"] == "Ovsdpdk"])
        self.user = self.ovs[0]['user']
        self.ssh_ip = self.ovs[0]['ip']
        if self.ovs[0]['auth_type'] == "password":
            self.passwd = self.ovs[0]['password']
        else:
            self.ssh_port = self.ovs[0]['ssh_port']
            self.key_filename = self.ovs[0]['key_filename']

    def ssh_remote_machine(self):
        if self.ovs[0]['auth_type'] == "password":
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
        nic_details = {
            'interface': {},
            'pci': self.attrs['phy_ports'],
            'phy_driver': self.attrs['phy_driver'],
            'vports_mac': self.attrs['vports_mac']
        }

        #    Make sure that ports are bound to kernel drivers e.g. i40e/ixgbe
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
        print("{0}".format(nic_details))
        return nic_details

    def setup_ovs(self, vpcis):
        self.connection.execute("/usr/bin/chmod 0666 /dev/vfio/*")
        self.connection.execute("/usr/bin/chmod a+x /dev/vfio")
        self.connection.execute("pkill -9 ovs")
        self.connection.execute("ps -ef | grep ovs | grep -v grep | "
                                "awk '{print $2}' | xargs -r kill -9")
        self.connection.execute("killall -r 'ovs*'")
        self.connection.execute(
            "mkdir -p {0}/etc/openvswitch".format(self.attrs["vpath"]))
        self.connection.execute(
            "mkdir -p {0}/var/run/openvswitch".format(self.attrs["vpath"]))
        self.connection.execute(
            "rm {0}/etc/openvswitch/conf.db".format(self.attrs["vpath"]))
        self.connection.execute(
            "ovsdb-tool create {0}/etc/openvswitch/conf.db "
            "{0}/share/openvswitch/"
            "vswitch.ovsschema".format(self.attrs["vpath"]))
        self.connection.execute("modprobe vfio-pci")
        self.connection.execute("chmod a+x /dev/vfio")
        self.connection.execute("chmod 0666 /dev/vfio/*")
        for vpci in vpcis:
            self.connection.execute(
                "/opt/isb_bin/dpdk_nic_bind.py "
                "--bind=vfio-pci {0}".format(vpci))

    def start_ovs_serverswitch(self):
            self.connection.execute("mkdir -p /usr/local/var/run/openvswitch")
            self.connection.execute(
                "ovsdb-server --remote=punix:"
                "/usr/local/var/run/openvswitch/db.sock  --pidfile --detach")
            self.connection.execute(
                "ovs-vsctl --no-wait set "
                "Open_vSwitch . other_config:dpdk-init=true")
            self.connection.execute(
                "ovs-vsctl --no-wait set "
                "Open_vSwitch . other_config:dpdk-lcore-mask=0x3")
            self.connection.execute(
                "ovs-vsctl --no-wait set "
                "Open_vSwitch . other_config:dpdk-socket-mem='2048,0'")
            self.connection.execute(
                "ovs-vswitchd unix:{0}/"
                "var/run/openvswitch/db.sock --pidfile --detach "
                "--log-file=/var/log/openvswitch/"
                "ovs-vswitchd.log".format(
                    self.attrs["vpath"]))
            self.connection.execute(
                "ovs-vsctl set Open_vSwitch . other_config:pmd-cpu-mask=2C")

    def setup_ovs_bridge(self):
        self.connection.execute("ovs-vsctl del-br br0")
        self.connection.execute(
            "rm -rf /usr/local/var/run/openvswitch/dpdkvhostuser*")
        self.connection.execute(
            "ovs-vsctl add-br br0 -- set bridge br0 datapath_type=netdev")
        self.connection.execute(
            "ovs-vsctl add-port br0 dpdk0 -- set Interface dpdk0 type=dpdk")
        self.connection.execute(
            "ovs-vsctl add-port br0 dpdk1 -- set Interface dpdk1 type=dpdk")
        self.connection.execute(
            "ovs-vsctl add-port br0 dpdkvhostuser0 -- set Interface "
            "dpdkvhostuser0 type=dpdkvhostuser")
        self.connection.execute("ovs-vsctl add-port br0 dpdkvhostuser1 "
                                "-- set Interface dpdkvhostuser1 "
                                "type=dpdkvhostuser")
        self.connection.execute(
            "chmod 0777 {0}/var/run/"
            "openvswitch/dpdkvhostuser*".format(self.attrs["vpath"]))

    def add_oflows(self):
        self.connection.execute("ovs-ofctl del-flows br0")
        for flow in self.attrs["flow"]:
            self.connection.execute(flow)
            self.connection.execute("ovs-ofctl dump-flows br0")
            self.connection.execute(
                "ovs-vsctl set Interface dpdk0 options:n_rxq=4")
            self.connection.execute(
                "ovs-vsctl set Interface dpdk1 options:n_rxq=4")

    def setup_ovs_context(self, pcis, nic_details, host_driver):

        ''' 1: Setup vm_ovs.xml to launch VM.'''
        cfg_ovs = '/tmp/vm_ovs.xml'
        mac = [0x00, 0x24, 0x81,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        mac_address = ':'.join(map(lambda x: "%02x" % x, mac))
        memory = self.vm_flavor.get('ram', '4096')
        extra_spec = self.vm_flavor.get('extra_spec', {})
        cpu = extra_spec.get('hw:cpu_cores', '2')
        socket = extra_spec.get('hw:cpu_sockets', '1')
        threads = extra_spec.get('hw:cpu_threads', '2')
        vcpu = int(cpu) * int(threads)
        vm_name = "vm_0"

        vm_ovs_xml = VM_TEMPLATE.format(
            vm_name=vm_name,
            random_uuid=uuid.uuid4(),
            mac_addr=mac_address,
            memory=memory, vcpu=vcpu, cpu=cpu,
            socket=socket, threads=threads,
            vm_image=self.vm_flavor["images"])

        with open(cfg_ovs, 'w') as f:
            f.write(vm_ovs_xml)

        ''' 2: Create and start the VM'''
        self.connection.put(cfg_ovs, cfg_ovs)
        time.sleep(10)
        err, out = self.check_output("virsh list --name | grep -i %s" % vm_name)
        try:
            if out == vm_name:
                log.info("VM '%s' is already present" % vm_name)
            else:
                ''' FIXME: launch through libvirt'''
                print("virsh create ...")
                err, out, _ = self.connection.execute(
                    "virsh create /tmp/vm_ovs.xml")
                time.sleep(10)
                print("err : {0}".format(err))
                print("{0}".format(_))
                print("out : {0}".format(out))
        except ValueError:
            raise

        ''' 3: Tuning for better performace.'''
        self.pin_vcpu(pcis, vm_name, vcpu)
        self.vm_names.append(vm_name)
        self.connection.execute(
            "echo 1 > /sys/module/kvm/parameters/"
            "allow_unsafe_assigned_interrupts")
        self.connection.execute(
            "echo never > /sys/kernel/mm/transparent_hugepage/enabled")
        print("After tuning performance ...")

    ''' This is roughly compatible with check_output function in subprocess
     module which is only available in python 2.7.'''
    def check_output(self, cmd, stderr=None):
        '''Run a command and capture its output'''
        err, out, _ = self.connection.execute(cmd)
        return err, out

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
        print("{0}".format(nodes))
        num_nodes = len(nodes)
        for i in range(0, 10):
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
                print("cpulist: {0}".format(cpulist))
            nodes[num] = self.split_cpu_list(cpulist)
        print("nodes: {0}".format(nodes))
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
