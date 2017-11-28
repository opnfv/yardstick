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
import logging

from yardstick.network_services.utils import MacAddress
from yardstick.network_services.utils import PciAddress
from yardstick.benchmark.contexts.standalone import model
from yardstick.benchmark.contexts.standalone.base import StandaloneBase

LOG = logging.getLogger(__name__)


class SriovContext(StandaloneBase):
    """ This class handles SRIOV standalone nodes - VM running on Non-Managed NFVi
    Configuration: sr-iov
    """

    __context_type__ = "StandaloneSriov"

    ROLE = 'Sriov'
    DOMAIN_XML_FILE = '/tmp/vm_sriov_%d.xml'

    def __init__(self):
        self.sriov = []
        self.drivers = []
        super(SriovContext, self).__init__()

    def _specific_deploy(self):
        pass

    def _specific_undeploy(self):
        # Bind nics back to kernel
        if not self.networks:
            return
        for _, ports in self.networks.items():
            # enable VFs for given...
            build_vfs = "echo 0 > /sys/bus/pci/devices/{0}/sriov_numvfs"
            self.connection.execute(build_vfs.format(ports.get('phy_port')))

    def _configure_nics(self):
        vf_cmd = "ip link set {0} vf 0 mac {1}"
        for _, ports in self.networks.items():
            vf_pci = []
            host_driver = ports.get('driver')
            if host_driver not in self.drivers:
                self.connection.execute("rmmod %svf" % host_driver)
                self.drivers.append(host_driver)

            # enable VFs for given...
            build_vfs = "echo 1 > /sys/bus/pci/devices/{0}/sriov_numvfs"
            self.connection.execute(build_vfs.format(ports.get('phy_port')))

            # configure VFs...
            mac = MacAddress.make_random_str()
            interface = ports.get('interface')
            if interface is not None:
                self.connection.execute(vf_cmd.format(interface, mac))

            vf_pci = self._get_vf_data('vf_pci', ports.get('phy_port'), mac, interface)
            ports.update({
                'vf_pci': vf_pci,
                'mac': mac
            })

        LOG.info("Ports %s", self.networks)

    def _enable_interfaces(self, vm_index, port_index, vfs, cfg):
        vf_spoofchk = "ip link set {0} vf 0 spoofchk off"

        vf = self.networks[vfs[0]]
        vpci = PciAddress.parse_address(vf['vpci'].strip(), multi_line=True)
        # Generate the vpci for the interfaces
        slot = vm_index + port_index + 10
        vf['vpci'] = \
            "{}:{}:{:02x}.{}".format(vpci.domain, vpci.bus, slot, vpci.function)
        model.add_sriov_interfaces(
            vf['vpci'], vf['vf_pci']['vf_pci'], vf['mac'], str(cfg))
        self.connection.execute("ifconfig %s up" % vf['interface'])
        self.connection.execute(vf_spoofchk.format(vf['interface']))

    def _get_vf_data(self, key, value, vfmac, pfif):
        vf_data = {
            "mac": vfmac,
            "pf_if": pfif
        }
        vfs = model.get_virtual_devices(self.connection, value)
        for k, v in vfs.items():
            m = PciAddress.parse_address(k.strip(), multi_line=True)
            m1 = PciAddress.parse_address(value.strip(), multi_line=True)
            if m.bus == m1.bus:
                vf_data.update({"vf_pci": str(v)})
                break

        return vf_data
