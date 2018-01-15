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

import io
import collections
import logging
import os
import re
import time

from yardstick import ssh
from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.contexts.standalone import model
from yardstick.common import exceptions
from yardstick.network_services import utils


LOG = logging.getLogger(__name__)

MAIN_BRIDGE = 'br0'


class OvsDpdkContext(Context):
    """ This class handles OVS standalone nodes - VM running on Non-Managed NFVi
    Configuration: ovs_dpdk
    """

    __context_type__ = "StandaloneOvsDpdk"

    SUPPORTED_OVS_TO_DPDK_MAP = {
        '2.6.0': '16.07.1',
        '2.6.1': '16.07.2',
        '2.7.0': '16.11.1',
        '2.7.1': '16.11.2',
        '2.7.2': '16.11.3',
        '2.8.0': '17.05.2'
    }

    DEFAULT_OVS = '2.6.0'
    CMD_TIMEOUT = 30
    DEFAULT_USER_PATH = '/usr/local'

    def __init__(self):
        self.file_path = None
        self.sriov = []
        self.first_run = True
        self.dpdk_devbind = ''
        self.vm_names = []
        self.nfvi_host = []
        self.nodes = []
        self.networks = {}
        self.attrs = {}
        self.vm_flavor = None
        self.servers = None
        self.helper = model.StandaloneContextHelper()
        self.vnf_node = model.Server()
        self.ovs_properties = {}
        self.wait_for_vswitchd = 10
        super(OvsDpdkContext, self).__init__()

    def init(self, attrs):
        """initializes itself from the supplied arguments"""
        super(OvsDpdkContext, self).init(attrs)

        self.file_path = attrs.get("file", "pod.yaml")

        self.nodes, self.nfvi_host, self.host_mgmt = \
            self.helper.parse_pod_file(self.file_path, 'OvsDpdk')

        self.attrs = attrs
        self.vm_flavor = attrs.get('flavor', {})
        self.servers = attrs.get('servers', {})
        self.vm_deploy = attrs.get("vm_deploy", True)
        self.ovs_properties = attrs.get('ovs_properties', {})
        # add optional static network definition
        self.networks = attrs.get("networks", {})

        LOG.debug("Nodes: %r", self.nodes)
        LOG.debug("NFVi Node: %r", self.nfvi_host)
        LOG.debug("Networks: %r", self.networks)

    def setup_ovs(self):
        """Initialize OVS-DPDK"""
        vpath = self.ovs_properties.get('vpath', self.DEFAULT_USER_PATH)
        create_from = os.path.join(vpath, 'etc/openvswitch/conf.db')
        create_to = os.path.join(vpath, 'share/openvswitch/vswitch.ovsschema')

        cmd_list = [
            'killall -r "ovs.*" -q | true',
            'mkdir -p {0}/etc/openvswitch'.format(vpath),
            'mkdir -p {0}/var/run/openvswitch'.format(vpath),
            'rm {0}/etc/openvswitch/conf.db | true'.format(vpath),
            'ovsdb-tool create {0} {1}'.format(create_from, create_to),
            'modprobe vfio-pci',
            'chmod a+x /dev/vfio',
            'chmod 0666 /dev/vfio/*',
        ]

        bind_cmd = '%s --force -b vfio-pci {port}' % self.dpdk_devbind
        for port in self.networks.values():
            cmd_list.append(bind_cmd.format(port=port.get('phy_port')))

        for cmd in cmd_list:
            LOG.info(cmd)
            exit_status, _, stderr = self.connection.execute(
                cmd, timeout=self.CMD_TIMEOUT)
            if exit_status:
                raise exceptions.OVSSetupError(command=cmd, error=stderr)

    def start_ovs_serverswitch(self):
        vpath = self.ovs_properties.get("vpath")
        pmd_nums = int(self.ovs_properties.get("pmd_threads", 2))
        ovs_sock_path = '/var/run/openvswitch/db.sock'
        log_path = '/var/log/openvswitch/ovs-vswitchd.log'

        pmd_cpu_mask = self.ovs_properties.get("pmd_cpu_mask", '')
        pmd_mask = hex(sum(2 ** num for num in range(pmd_nums)) << 1)
        if pmd_cpu_mask:
            pmd_mask = pmd_cpu_mask

        socket0 = self.ovs_properties.get("ram", {}).get("socket_0", "2048")
        socket1 = self.ovs_properties.get("ram", {}).get("socket_1", "2048")

        ovs_other_config = "ovs-vsctl {0}set Open_vSwitch . other_config:{1}"
        detach_cmd = "ovs-vswitchd unix:{0}{1} --pidfile --detach --log-file={2}"

        lcore_mask = self.ovs_properties.get("lcore_mask", '')
        if lcore_mask:
            lcore_mask = ovs_other_config.format("--no-wait ", "dpdk-lcore-mask='%s'" % lcore_mask)

        cmd_list = [
            "mkdir -p /usr/local/var/run/openvswitch",
            "mkdir -p {}".format(os.path.dirname(log_path)),
            "ovsdb-server --remote=punix:/{0}/{1}  --pidfile --detach".format(vpath,
                                                                              ovs_sock_path),
            ovs_other_config.format("--no-wait ", "dpdk-init=true"),
            ovs_other_config.format("--no-wait ", "dpdk-socket-mem='%s,%s'" % (socket0, socket1)),
            lcore_mask,
            detach_cmd.format(vpath, ovs_sock_path, log_path),
            ovs_other_config.format("", "pmd-cpu-mask=%s" % pmd_mask),
        ]

        for cmd in cmd_list:
            LOG.info(cmd)
            self.connection.execute(cmd)
        time.sleep(self.wait_for_vswitchd)

    def setup_ovs_bridge_add_flows(self):
        dpdk_args = ""
        dpdk_list = []
        vpath = self.ovs_properties.get("vpath", "/usr/local")
        version = self.ovs_properties.get('version', {})
        ovs_ver = [int(x) for x in version.get('ovs', self.DEFAULT_OVS).split('.')]
        ovs_add_port = ('ovs-vsctl add-port {br} {port} -- '
                        'set Interface {port} type={type_}{dpdk_args}')
        ovs_add_queue = 'ovs-vsctl set Interface {port} options:n_rxq={queue}'
        chmod_vpath = 'chmod 0777 {0}/var/run/openvswitch/dpdkvhostuser*'

        cmd_list = [
            'ovs-vsctl --if-exists del-br {0}'.format(MAIN_BRIDGE),
            'rm -rf {0}/var/run/openvswitch/dpdkvhostuser*'.format(vpath),
            'ovs-vsctl add-br {0} -- set bridge {0} datapath_type=netdev'.
            format(MAIN_BRIDGE)
        ]

        ordered_network = collections.OrderedDict(self.networks)
        for index, vnf in enumerate(ordered_network.values()):
            if ovs_ver >= [2, 7, 0]:
                dpdk_args = " options:dpdk-devargs=%s" % vnf.get("phy_port")
            dpdk_list.append(ovs_add_port.format(
                br=MAIN_BRIDGE, port='dpdk%s' % vnf.get("port_num", 0),
                type_='dpdk', dpdk_args=dpdk_args))
            dpdk_list.append(ovs_add_queue.format(
                port='dpdk%s' % vnf.get("port_num", 0),
                queue=self.ovs_properties.get("queues", 1)))

        # Sorting the array to make sure we execute dpdk0... in the order
        list.sort(dpdk_list)
        cmd_list.extend(dpdk_list)

        # Need to do two for loop to maintain the dpdk/vhost ports.
        for index, _ in enumerate(ordered_network):
            cmd_list.append(ovs_add_port.format(
                br=MAIN_BRIDGE, port='dpdkvhostuser%s' % index,
                type_='dpdkvhostuser', dpdk_args=""))

        ovs_flow = ("ovs-ofctl add-flow {0} in_port=%s,action=output:%s".
                    format(MAIN_BRIDGE))
        network_count = len(ordered_network) + 1
        for in_port, out_port in zip(range(1, network_count),
                                     range(network_count, network_count * 2)):
            cmd_list.append(ovs_flow % (in_port, out_port))
            cmd_list.append(ovs_flow % (out_port, in_port))

        cmd_list.append(chmod_vpath.format(vpath))

        for cmd in cmd_list:
            LOG.info(cmd)
            exit_status, _, stderr = self.connection.execute(
                cmd, timeout=self.CMD_TIMEOUT)
            if exit_status:
                raise exceptions.OVSSetupError(command=cmd, error=stderr)

    def _check_hugepages(self):
        meminfo = io.BytesIO()
        self.connection.get_file_obj('/proc/meminfo', meminfo)
        regex = re.compile(r"HugePages_Total:\s+(?P<hp_total>\d+)[\n\r]"
                           r"HugePages_Free:\s+(?P<hp_free>\d+)")
        match = regex.search(meminfo.getvalue().decode('utf-8'))
        if not match:
            raise exceptions.OVSHugepagesInfoError()
        if int(match.group('hp_total')) == 0:
            raise exceptions.OVSHugepagesNotConfigured()
        if int(match.group('hp_free')) == 0:
            raise exceptions.OVSHugepagesZeroFree(
                total_hugepages=int(match.group('hp_total')))

    def cleanup_ovs_dpdk_env(self):
        self.connection.execute(
            'ovs-vsctl --if-exists del-br {0}'.format(MAIN_BRIDGE))
        self.connection.execute("pkill -9 ovs")

    def check_ovs_dpdk_env(self):
        self.cleanup_ovs_dpdk_env()
        self._check_hugepages()

        version = self.ovs_properties.get("version", {})
        ovs_ver = version.get("ovs", self.DEFAULT_OVS)
        dpdk_ver = version.get("dpdk", "16.07.2").split('.')

        supported_version = self.SUPPORTED_OVS_TO_DPDK_MAP.get(ovs_ver, None)
        if supported_version is None or supported_version.split('.')[:2] != dpdk_ver[:2]:
            raise exceptions.OVSUnsupportedVersion(
                ovs_version=ovs_ver,
                ovs_to_dpdk_map=self.SUPPORTED_OVS_TO_DPDK_MAP)

        status = self.connection.execute("ovs-vsctl -V | grep -i '%s'" % ovs_ver)[0]
        if status:
            deploy = model.OvsDeploy(self.connection,
                                     utils.get_nsb_option("bin_path"),
                                     self.ovs_properties)
            deploy.ovs_deploy()

    def deploy(self):
        """don't need to deploy"""

        # Todo: NFVi deploy (sriov, vswitch, ovs etc) based on the config.
        if not self.vm_deploy:
            return

        self.connection = ssh.SSH.from_node(self.host_mgmt)
        self.dpdk_devbind = utils.provision_tool(
            self.connection,
            os.path.join(utils.get_nsb_option('bin_path'), 'dpdk-devbind.py'))

        # Check dpdk/ovs version, if not present install
        self.check_ovs_dpdk_env()
        #    Todo: NFVi deploy (sriov, vswitch, ovs etc) based on the config.
        model.StandaloneContextHelper.install_req_libs(self.connection)
        self.networks = model.StandaloneContextHelper.get_nic_details(
            self.connection, self.networks, self.dpdk_devbind)

        self.setup_ovs()
        self.start_ovs_serverswitch()
        self.setup_ovs_bridge_add_flows()
        self.nodes = self.setup_ovs_dpdk_context()
        LOG.debug("Waiting for VM to come up...")
        self.nodes = model.StandaloneContextHelper.wait_for_vnfs_to_start(
            self.connection, self.servers, self.nodes)

    def undeploy(self):

        if not self.vm_deploy:
            return

        # Cleanup the ovs installation...
        self.cleanup_ovs_dpdk_env()

        # Bind nics back to kernel
        bind_cmd = "{dpdk_devbind} --force -b {driver} {port}"
        for port in self.networks.values():
            vpci = port.get("phy_port")
            phy_driver = port.get("driver")
            self.connection.execute(bind_cmd.format(
                dpdk_devbind=self.dpdk_devbind, driver=phy_driver, port=vpci))

        # Todo: NFVi undeploy (sriov, vswitch, ovs etc) based on the config.
        for vm in self.vm_names:
            model.Libvirt.check_if_vm_exists_and_delete(vm, self.connection)

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

    def _get_network(self, attr_name):
        if not isinstance(attr_name, collections.Mapping):
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

    def configure_nics_for_ovs_dpdk(self):
        portlist = collections.OrderedDict(self.networks)
        for key in portlist:
            mac = model.StandaloneContextHelper.get_mac_address()
            portlist[key].update({'mac': mac})
        self.networks = portlist
        LOG.info("Ports %s", self.networks)

    def _enable_interfaces(self, index, vfs, xml_str):
        vpath = self.ovs_properties.get("vpath", "/usr/local")
        vf = self.networks[vfs[0]]
        port_num = vf.get('port_num', 0)
        vpci = utils.PciAddress(vf['vpci'].strip())
        # Generate the vpci for the interfaces
        slot = index + port_num + 10
        vf['vpci'] = \
            "{}:{}:{:02x}.{}".format(vpci.domain, vpci.bus, slot, vpci.function)
        return model.Libvirt.add_ovs_interface(
            vpath, port_num, vf['vpci'], vf['mac'], xml_str)

    def setup_ovs_dpdk_context(self):
        nodes = []

        self.configure_nics_for_ovs_dpdk()

        for index, (key, vnf) in enumerate(collections.OrderedDict(
                self.servers).items()):
            cfg = '/tmp/vm_ovs_%d.xml' % index
            vm_name = "vm_%d" % index

            # 1. Check and delete VM if already exists
            model.Libvirt.check_if_vm_exists_and_delete(vm_name,
                                                        self.connection)
            xml_str, mac = model.Libvirt.build_vm_xml(
                self.connection, self.vm_flavor, vm_name, index)

            # 2: Cleanup already available VMs
            for vfs in [vfs for vfs_name, vfs in vnf["network_ports"].items()
                        if vfs_name != 'mgmt']:
                xml_str = self._enable_interfaces(index, vfs, xml_str)

            # copy xml to target...
            model.Libvirt.write_file(cfg, xml_str)
            self.connection.put(cfg, cfg)

            # NOTE: launch through libvirt
            LOG.info("virsh create ...")
            model.Libvirt.virsh_create_vm(self.connection, cfg)

            self.vm_names.append(vm_name)

            # build vnf node details
            nodes.append(self.vnf_node.generate_vnf_instance(self.vm_flavor,
                                                             self.networks,
                                                             self.host_mgmt.get('ip'),
                                                             key, vnf, mac))

        return nodes
