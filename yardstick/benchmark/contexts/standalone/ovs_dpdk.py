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
import logging
import time

from itertools import chain

from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.utils import MacAddress
from yardstick.benchmark.contexts.standalone import model
from yardstick.benchmark.contexts.standalone.model import OvsDeploy
from yardstick.network_services.utils import PciAddress
from yardstick.benchmark.contexts.standalone.base import StandaloneBase
from yardstick.common.cpu_model import CpuList

LOG = logging.getLogger(__name__)

OVS_ADD_PORT_TEMPLATE = ("ovs-vsctl add-port {br} {port} "
                         "-- set Interface {port} type={type_}{dpdk_args}")

OVS_ADD_QUEUE_TEMPLATE = "ovs-vsctl set Interface {port} options:n_rxq={queue}"


class OvsDpdkContext(StandaloneBase):
    """ This class handles OVS standalone nodes - VM running on Non-Managed NFVi
    Configuration: ovs_dpdk
    """

    __context_type__ = "StandaloneOvsDpdk"

    SUPPORTED_OVS_TO_DPDK_MAP = {
        '2.7.90': '17.02.1',
        '2.8.0': '17.05.2',
    }

    DEFAULT_OVS = '2.6.0'

    PKILL_TEMPLATE = "pkill %s %s"

    ROLE = 'OvsDpdk'

    DOMAIN_XML_FILE = '/tmp/vm_ovs_%d.xml'

    def __init__(self):
        self.ovs_properties = {}
        self.wait_for_vswitchd = 10
        super(OvsDpdkContext, self).__init__()

    def init(self, attrs):
        self.ovs_properties = attrs.get('ovs_properties', {})
        super(OvsDpdkContext, self).init(attrs)

    def _setup_ovs(self):
        vpath = self.ovs_properties.get("vpath", "/usr/local")
        xargs_kill_cmd = self.PKILL_TEMPLATE % ('-9', 'ovs')

        create_from = os.path.join(vpath, 'etc/openvswitch/conf.db')
        create_to = os.path.join(vpath, 'share/openvswitch/vswitch.ovsschema')

        cmd_list = [
            "chmod 0666 /dev/vfio/*",
            "chmod a+x /dev/vfio",
            "pkill -9 ovs",
            xargs_kill_cmd,
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
            self.connection.execute(cmd)

        self.dpdk_bind_helper.bind(pci_addresses=[port.get("phy_port")
                                                  for _, port in self.networks.items()],
                                   driver="vfio-pci")

    def _start_ovs_serverswitch(self):
        vpath = self.ovs_properties.get("vpath")
        LOG.info("PMD threads CPUs: {}".format(self.cpu_properties.pmd_pin))

        ovs_sock_path = '/var/run/openvswitch/db.sock'
        log_path = '/var/log/openvswitch/ovs-vswitchd.log'

        # pmd_mask = hex(sum(2 ** num for num in range(pmd_nums)) << 1)
        pmd_pin = CpuList(self.cpu_properties.pmd_pin)
        pmd_mask = hex(pmd_pin.mask)
        socket0 = self.ovs_properties.get("ram", {}).get("socket_0", "2048")
        socket1 = self.ovs_properties.get("ram", {}).get("socket_1", "2048")

        ovs_other_config = "ovs-vsctl {0}set Open_vSwitch . other_config:{1}"
        detach_cmd = "ovs-vswitchd unix:{0}{1} --pidfile --detach --log-file={2}"

        cmd_list = [
            "mkdir -p /usr/local/var/run/openvswitch",
            "mkdir -p {}".format(os.path.dirname(log_path)),
            "ovsdb-server --remote=punix:/{0}/{1}  --pidfile --detach".format(vpath,
                                                                              ovs_sock_path),
            ovs_other_config.format("--no-wait ", "dpdk-init=true"),
            ovs_other_config.format("--no-wait ", "dpdk-socket-mem='%s,%s'" % (socket0, socket1)),
            detach_cmd.format(vpath, ovs_sock_path, log_path),
            ovs_other_config.format("", "pmd-cpu-mask=%s" % pmd_mask),
        ]

        for cmd in cmd_list:
            LOG.info(cmd)
            self.connection.execute(cmd)
        time.sleep(self.wait_for_vswitchd)

    def _setup_ovs_bridge_add_flows(self):
        vpath = self.ovs_properties.get("vpath", "/usr/local")
        version = self.ovs_properties.get('version', {})
        ovs_ver = [int(x) for x in version.get('ovs', self.DEFAULT_OVS).split('.')]
        chmod_vpath = "chmod 0777 {0}/var/run/openvswitch/dpdkvhostuser*"

        cmd_dpdk_list = [
            "ovs-vsctl del-br br0",
            "rm -rf {0}/var/run/openvswitch/dpdkvhostuser*".format(vpath),
            "ovs-vsctl add-br br0 -- set bridge br0 datapath_type=netdev",
        ]
        dpdk_list = []
        dpdk_vhost_list = []

        dpdk_args = " options:dpdk-devargs={}" if ovs_ver >= [2, 7, 0] else ""

        index = -1
        for index, (key, vnf) in enumerate(self.networks.items()):
            port = 'dpdk%s' % vnf.get("port_num", 0)
            phy_port = vnf.get("phy_port")
            queue = self.ovs_properties.get("queues", 1)

            dpdk_list.append(OVS_ADD_PORT_TEMPLATE.format(br='br0', port=port, type_='dpdk',
                                                          dpdk_args=dpdk_args.format(phy_port)))

            dpdk_list.append(OVS_ADD_QUEUE_TEMPLATE.format(port=port, queue=queue))
            dpdk_vhost_list.append(OVS_ADD_PORT_TEMPLATE.format(br='br0', dpdk_args="",
                                                                port='dpdkvhostuser%s' % index,
                                                                type_='dpdkvhostuser'))

        # Sorting the array to make sure we execute dpdk0... in the order
        dpdk_list.sort()

        for cmd in chain(cmd_dpdk_list, dpdk_list, dpdk_vhost_list):
            LOG.info(cmd)
            self.connection.execute(cmd)

        # Fixme: add flows code
        ovs_flow = "ovs-ofctl add-flow br0 in_port=%s,action=output:%s"

        network_count = index + 1
        for in_port, out_port in zip(range(1, network_count + 1),
                                     range(network_count + 1, network_count * 2 + 1)):
            self.connection.execute(ovs_flow % (in_port, out_port))
            self.connection.execute(ovs_flow % (out_port, in_port))

        self.connection.execute(chmod_vpath.format(vpath))

    def _cleanup_ovs_dpdk_env(self):
        self.connection.execute("ovs-vsctl del-br br0")
        self.connection.execute("pkill -9 ovs")

    def _check_ovs_dpdk_env(self):
        self._cleanup_ovs_dpdk_env()

        version = self.ovs_properties.get("version", {})
        ovs_ver = version.get("ovs", self.DEFAULT_OVS)
        dpdk_ver = version.get("dpdk", "16.07.2").split('.')

        supported_version = self.SUPPORTED_OVS_TO_DPDK_MAP.get(ovs_ver, None)
        if supported_version is None or supported_version.split('.')[:2] != dpdk_ver[:2]:
            raise Exception("Unsupported ovs '{}'. Please check the config...".format(ovs_ver))

        status = self.connection.execute("ovs-vsctl -V | grep -i '%s'" % ovs_ver)[0]
        if status:
            deploy = OvsDeploy(self.connection, get_nsb_option("bin_path"), self.ovs_properties)
            deploy.ovs_deploy()

    def _specific_cpu_handling(self):
        # first satisfy host dpdk
        # allways allocate core 0 for dpdk.
        #  - how do we know core 0 is available...
        #  - core 0 being the master core for the ovs-dpdk seems to be hardcoded somewhere
        self.cpu_model.allocate(CpuList([0]))

        pmd_pin = self.cpu_model.allocate(self.cpu_properties.pmd_threads)
        if pmd_pin is None:
            pmd_pin = self.cpu_properties.pmd_thread_pin
        if pmd_pin is None:
            try:
                pmd_pin = self.cpu_model.allocate(self.attrs['ovs_properties']['pmd_threads'])
            except KeyError:
                pass
        if pmd_pin is None:
            pmd_pin = self.cpu_model.allocate(2)

        self.cpu_properties.pmd_pin = pmd_pin

    def _specific_deploy(self):
        # Check dpdk/ovs version, if not present install
        # Read if there are any user's preferences about PMD and qemu threads
        self._check_ovs_dpdk_env()
        self._setup_ovs()
        self._start_ovs_serverswitch()
        self._setup_ovs_bridge_add_flows()

    def _specific_undeploy(self):
        # Cleanup the ovs installation...
        self._cleanup_ovs_dpdk_env()
        self.dpdk_bind_helper.rebind_drivers()

    def _configure_nics(self):
        for key, ports in self.networks.items():
            ports['mac'] = MacAddress.make_random_str()
        LOG.info("Ports %s" % self.networks)

    def _enable_interfaces(self, vm_index, port_index, vfs, cfg):
        vpath = self.ovs_properties.get("vpath", "/usr/local")
        vf = self.networks[vfs[0]]
        port_num = vf.get('port_num', 0)
        vpci = PciAddress.parse_address(vf['vpci'].strip(), multi_line=True)
        # Generate the vpci for the interfaces
        slot = vm_index + port_num + 10
        vf['vpci'] = \
            "{}:{}:{:02x}.{}".format(vpci.domain, vpci.bus, slot, vpci.function)
        model.add_ovs_interface(vpath, port_num, vf['vpci'], vf['mac'], str(cfg))
