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
from netaddr import IPNetwork
import xml.etree.ElementTree as ET
from itertools import izip, chain, repeat
from collections import OrderedDict

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
    <numa>
       <cell id='0' cpus='{numa_cpus}' memory='{memory}' unit='MB' memAccess='shared'/>
    </numa>
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
      <mac address='{mac_addr}'/>
      <model type='virtio'/>
    </interface>
    <graphics autoport="yes" listen="0.0.0.0" port="1" type="vnc" />
  </devices>
</domain>
"""
WAIT_FOR_BOOT = 30


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
        self.vm_flavor = attrs.get('flavor', {})
        self.ports = attrs.get('networks', {})
        self.attrs = attrs
        self.servers = attrs.get('servers', {})
        self.ovs_properties = attrs.get('ovs_properties', {})


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
        self.host_mgmt = { 'user': self.ovs[0]['user'],
                           'ip': str(IPNetwork(self.ovs[0]['ip']).ip),
                           'password': self.ovs[0]['password'],
                           'ssh_port': self.ovs[0].get('ssh_port', 22),
                           'key_filename': self.ovs[0]['key_filename']}

    def ssh_remote_machine(self):
        self.connection = ssh.SSH.from_node(self.host_mgmt)
        self.dpdk_nic_bind = provision_tool(
            self.connection,
            os.path.join(get_nsb_option("bin_path"), "dpdk_nic_bind.py"))

    def get_kernel_module(self, pci, driver):
        if not driver:
            self.connection.execute("pkill -9 ovs")
            out = self.connection.execute("lspci -k -s %s" % pci)[1]
            driver = out.split("Kernel modules:").pop().strip()
        return driver

    def get_nic_details(self):
        for key, ports in self.ports.items():
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

    def setup_ovs(self):
        self.connection.execute("chmod 0666 /dev/vfio/*")
        self.connection.execute("chmod a+x /dev/vfio")
        self.connection.execute("pkill -9 ovs")
        self.connection.execute("ps -ef | grep ovs | grep -v grep | "
                                "awk '{print $2}' | xargs -r kill -9")
        self.connection.execute("killall -r 'ovs*'")
        self.connection.execute(
            "mkdir -p {0}/etc/openvswitch".format(self.ovs_properties["vpath"]))
        self.connection.execute(
            "mkdir -p {0}/var/run/openvswitch".format(self.ovs_properties["vpath"]))
        self.connection.execute(
            "rm {0}/etc/openvswitch/conf.db".format(self.ovs_properties["vpath"]))
        self.connection.execute(
            "ovsdb-tool create {0}/etc/openvswitch/conf.db "
            "{0}/share/openvswitch/"
            "vswitch.ovsschema".format(self.ovs_properties["vpath"]))
        self.connection.execute("modprobe vfio-pci")
        self.connection.execute("chmod a+x /dev/vfio")
        self.connection.execute("chmod 0666 /dev/vfio/*")
        for key, port in self.ports.items():
            self.connection.execute(
                "{0} --bind=vfio-pci {1}".format(self.dpdk_nic_bind, port["phy_port"]))

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
                "Open_vSwitch . other_config:dpdk-socket-mem='4096,0'")
            self.connection.execute(
                "ovs-vswitchd unix:{0}/"
                "var/run/openvswitch/db.sock --pidfile --detach "
                "--log-file=/var/log/openvswitch/"
                "ovs-vswitchd.log".format(
                    self.ovs_properties["vpath"]))
            self.connection.execute(
                "ovs-vsctl set Open_vSwitch . other_config:pmd-cpu-mask=2C")

    def setup_ovs_bridge_add_flows(self):
        self.connection.execute("ovs-vsctl del-br br0")
        self.connection.execute(
            "rm -rf /usr/local/var/run/openvswitch/dpdkvhostuser*")
        self.connection.execute(
            "ovs-vsctl add-br br0 -- set bridge br0 datapath_type=netdev")

        dpdk_args = ""
        for key, vnf in self.ports.items():
            if (int(self.ovs_properties.get("ovs", "2.6.0").replace(".", "")) >= 270):
                dpdk_args = " options:dpdk-devargs=%s" % vnf["phy_port"]
            index = self.ports.keys().index(key)
            self.connection.execute(
                "ovs-vsctl add-port br0 dpdk%s -- set Interface dpdk%s type=dpdki %s" % (index, index, dpdk_args))
            self.connection.execute(
                "ovs-vsctl set Interface dpdk%s options:n_rxq=%s" % (index, self.ovs_properties["queues"]))

        for key, vnf in self.ports.items():
            index = self.ports.keys().index(key)
            self.connection.execute(
                "ovs-vsctl add-port br0 dpdkvhostuser%s -- set Interface dpdkvhostuser%s type=dpdkvhostuser" % (index, index))
            self.connection.execute("ovs-ofctl del-flows br0")

        # Fixme: add flows code
        for key, vnf in self.ports.items():
            index = self.ports.keys().index(key)
            in_port = index + 1
            output = in_port + len(self.ports.keys())
            self.connection.execute("ovs-ofctl add-flow br0 in_port=%s,action=output:%s" % (in_port, output))
            self.connection.execute("ovs-ofctl add-flow br0 in_port=%s,action=output:%s" % (output, in_port))

        self.connection.execute(
            "chmod 0777 {0}/var/run/openvswitch/dpdkvhostuser*".format(self.ovs_properties["vpath"]))

    def get_mac_address(self, end=0x7f):
        mac = [0x52, 0x54, 0x00,
               random.randint(0x00, end),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        mac_address = ':'.join(map(lambda x: "%02x" % x, mac))
        return mac_address

    def add_ovs_interface(self, index, vpci, vports_mac, xml):
        root = ET.parse(xml)
        device = root.find('devices')

        interface = ET.SubElement(device, 'interface')
        interface.set('type', 'vhostuser')
        mac = ET.SubElement(interface, 'mac')
        mac.set('address', vports_mac)

        source = ET.SubElement(interface, 'source')
        source.set('type', 'unix')
        source.set('path', '/usr/local/var/run/openvswitch/dpdkvhostuser{0}'.format(index))
        source.set('mode', 'client')

        model = ET.SubElement(interface, 'model')
        model.set('type', 'virtio')

        driver = ET.SubElement(interface, 'driver')
        driver.set('queues', '4')

        host = ET.SubElement(driver, 'host')
        host.set('mrg_rxbuf', 'off')

        virto_pci = ET.SubElement(interface, 'address')
        virto_pci.set('type', 'pci')
        virto_pci.set('domain', '0x%s' % vpci[0])
        virto_pci.set('bus', '0x%s' % vpci[1])
        virto_pci.set('slot', '0x%s' % vpci[2])
        virto_pci.set('function', '0x%s' % vpci[3])

        root.write(xml)

    def spilt_pci_addr(self, pci):
         m = pci.split(":")
         slot = m[2].split(".")
         return [m[0], m[1], slot[0], slot[1]]

    def configure_nics_for_ovs(self):
        portlist = OrderedDict(self.ports)
        for key, ports in portlist.items():
            index = portlist.keys().index(key)
            mac = self.get_mac_address()
            portlist[key].update({'mac': mac})
        self.ports = portlist
        log.info("Ports %s" % self.ports)

    def setup_ovs_context(self):
        nodes = []

        #   1 : modprobe host_driver with num_vfs
        self.configure_nics_for_ovs()

        serverslist = OrderedDict(self.servers)
        for key, vnf in serverslist.items():
            index = serverslist.keys().index(key)
            cfg_ovs = '/tmp/vm_ovs_%s.xml' % str(index)
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
            mac = self.get_mac_address(0x00)

            # build snapshot image
            image = "/var/lib/libvirt/images/%s.qcow2" % index
            self.connection.execute("rm %s" % image)
            self.connection.execute(
                "qemu-img create -f qcow2 -o backing_file=%s %s" % (self.vm_flavor["images"],
                                                                    image))
	    ''' 1: Setup vm_ovs.xml to launch VM.'''
	    vm_ovs_xml = VM_TEMPLATE.format(
		    vm_name=vm_name,
		    random_uuid=uuid.uuid4(),
		    mac_addr=mac,
		    numa_cpus=numa_cpus,
		    memory=memory, vcpu=vcpu, cpu=cpu,
		    socket=socket, threads=threads,
		    vm_image=image)

	    with open(cfg_ovs, 'w') as f:
		f.write(vm_ovs_xml)

            ordervnf = OrderedDict(vnf["network_ports"])
            for vkey, vfs in ordervnf.items():
                if vkey != "mgmt":
                    vf = self.ports[vfs[0]]
                    vpci = self.spilt_pci_addr(vf['vpci'])
                    # Generate the vpci for the interfaces
                    vpci[2] = format((index + 10) + (int(vf['port_num'])), '#04x')[2:]
                    vf['vpci'] = \
                        "{}:{}:{}.{}".format(vpci[0], vpci[1], vpci[2], vpci[3])
                    self.add_ovs_interface(
                            vf['port_num'],
                            self.spilt_pci_addr(vf['vpci']),
                            vf['mac'],
                            "%s" % cfg_ovs)

	    ''' 2: Create and start the VM'''
	    self.connection.put(cfg_ovs, cfg_ovs)
	    try:
	        ''' FIXME: launch through libvirt'''
	        print("virsh create ...")
	        err, out, _ = self.connection.execute("virsh create %s" % cfg_ovs)
	        print("err : {0}".format(err))
	        print("{0}".format(_))
	        print("out : {0}".format(out))
	    except ValueError:
	        raise

	    ''' 3: Tuning for better performace.'''
	    self.pin_vcpu(vm_name, vcpu)
            self.vm_names.append(vm_name)
            nodes.append(self.generate_vnf_instance(key, vnf, mac))
        self.connection.execute(
            "echo 1 > /sys/module/kvm/parameters/"
            "allow_unsafe_assigned_interrupts")
        self.connection.execute(
            "echo never > /sys/kernel/mm/transparent_hugepage/enabled")
        print("After tuning performance ...")
        return nodes

    def get_mgmt_ip(self, mac, ip, node):
        mgmtip = None
        times = 10
        while not mgmtip and times:
            self.connection.execute("fping -c 1 -g %s > /dev/null 2>&1" % ip)
            log.info("fping -c 1 -g %s > /dev/null 2>&1" % ip)
            err, out, _ = self.connection.execute("ip neighbor | grep '%s'" % mac)
            if not err:
               mgmtip = str(out.split(" ")[0]).strip()
               log.info(ip)
               client = ssh.SSH.from_node(node, overrides={"ip": mgmtip})
               client.wait()
               break
            log.info("waiting for VM to boot with ip.....")
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

    def build_vnf_interfaces(self, vnf):
        interfaces = {}
        index = 0

        for key, vfs in vnf["network_ports"].items():
            if key != "mgmt":
                vf = self.ports[vfs[0]]
                ip = IPNetwork(vf['cidr'])
                interfaces.update({key: {}})
                interfaces[key].update({'vpci': vf['vpci']})
                interfaces[key].update({'driver': "virtio-pci"})
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
            "host": self.ssh_ip,
            "user": self.vm_flavor.get('user', 'root'),
            "password": self.vm_flavor.get('password', 'root'),
            "key_filename": key_filename,
            "interfaces": interfaces,
            "routing_table": [],
            # empty IPv6 routing table
            "nd_route_tbl": [],
            "name": key, "role": key
        }

        return result

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

    def pin_vcpu(self, vm_name, cpu):
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
        for vm in self.vm_names:
            err, out = self.check_output("virsh list --name | grep -i %s" % vm)
            log.info("{0}".format(out))
            if err == 0:
                self.connection.execute("virsh shutdown %s" % vm)
                self.connection.execute("virsh destroy %s" % vm)
            else:
                log.error("error : {0}".format(err))
