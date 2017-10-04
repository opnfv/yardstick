# Copyright (c) 2016-2018 Intel Corporation
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
import logging
import os

import re
from collections import defaultdict
from itertools import chain

from yardstick.common.utils import validate_non_string_sequence
from yardstick.error import IncorrectConfig
from yardstick.error import IncorrectSetup
from yardstick.error import IncorrectNodeSetup
from yardstick.error import SSHTimeout
from yardstick.error import SSHError

NETWORK_KERNEL = 'network_kernel'
NETWORK_DPDK = 'network_dpdk'
NETWORK_OTHER = 'network_other'
CRYPTO_KERNEL = 'crypto_kernel'
CRYPTO_DPDK = 'crypto_dpdk'
CRYPTO_OTHER = 'crypto_other'

LOG = logging.getLogger(__name__)


class DpdkBindHelperException(Exception):
    pass


class DpdkInterface(object):
    TOPOLOGY_REQUIRED_KEYS = frozenset({
        "vpci", "local_ip", "netmask", "local_mac", "driver"})

    def __init__(self, dpdk_node, interface):
        super(DpdkInterface, self).__init__()
        self.dpdk_node = dpdk_node
        self.interface = interface

        try:
            assert self.local_mac
        except (AssertionError, KeyError):
            raise IncorrectConfig

    @property
    def local_mac(self):
        return self.interface['local_mac']

    @property
    def mac_lower(self):
        return self.local_mac.lower()

    @property
    def missing_fields(self):
        return self.TOPOLOGY_REQUIRED_KEYS.difference(self.interface)

    @staticmethod
    def _detect_socket(netdev):
        try:
            socket = netdev['numa_node']
        except KeyError:
            # Where is this documented?
            # It seems for dual-sockets systems the second socket PCI bridge
            # will have an address > 0x0f, e.g.
            # Bridge PCI->PCI (P#524320 busid=0000:80:02.0 id=8086:6f04
            if netdev['pci_bus_id'][5] == "0":
                socket = 0
            else:
                # this doesn't handle quad-sockets
                # TODO: fix this for quad-socket
                socket = 1
        return socket

    def probe_missing_values(self):
        try:
            for netdev in self.dpdk_node.netdevs.values():
                if netdev['address'].lower() == self.mac_lower:
                    socket = self._detect_socket(netdev)
                    self.interface.update({
                        'vpci': netdev['pci_bus_id'],
                        'driver': netdev['driver'],
                        'socket': socket,
                        # don't need ifindex
                    })

        except KeyError:
            # if we don't find all the keys then don't update
            pass

        except (IncorrectNodeSetup, SSHError, SSHTimeout):
            raise IncorrectConfig(
                "Unable to probe missing interface fields '%s', on node %s "
                "SSH Error" % (', '.join(self.missing_fields), self.dpdk_node.node_key))


class DpdkNode(object):

    def __init__(self, node_name, interfaces, ssh_helper, timeout=120):
        super(DpdkNode, self).__init__()
        self.interfaces = interfaces
        self.ssh_helper = ssh_helper
        self.node_key = node_name
        self.timeout = timeout
        self._dpdk_helper = None
        self.netdevs = {}

        try:
            self.dpdk_interfaces = {intf['name']: DpdkInterface(self, intf['virtual-interface'])
                                    for intf in self.interfaces}
        except IncorrectConfig:
            template = "MAC address is required for all interfaces, missing on: {}"
            errors = (intf['name'] for intf in self.interfaces if
                      'local_mac' not in intf['virtual-interface'])
            raise IncorrectSetup(template.format(", ".join(errors)))

    @property
    def dpdk_helper(self):
        if not isinstance(self._dpdk_helper, DpdkBindHelper):
            self._dpdk_helper = DpdkBindHelper(self.ssh_helper)
        return self._dpdk_helper

    @property
    def _interface_missing_iter(self):
        return chain.from_iterable(self._interface_missing_map.values())

    @property
    def _interface_missing_map(self):
        return {name: intf.missing_fields for name, intf in self.dpdk_interfaces.items()}

    def _probe_netdevs(self):
        self.netdevs.update(self.dpdk_helper.find_net_devices())

    def _force_rebind(self):
        return self.dpdk_helper.force_dpdk_rebind()

    def _probe_dpdk_drivers(self):
        self.dpdk_helper.probe_real_kernel_drivers()
        for pci, driver in self.dpdk_helper.real_kernel_interface_driver_map.items():
            for intf in self.interfaces:
                vintf = intf['virtual-interface']
                # stupid substring matches
                # don't use netdev use interface
                if vintf['vpci'].endswith(pci):
                    vintf['driver'] = driver
                    # we can't update netdevs because we may not have netdev info

    def _probe_missing_values(self):
        for intf in self.dpdk_interfaces.values():
            intf.probe_missing_values()

    def check(self):
        # only ssh probe if there are missing values
        # ssh probe won't work on Ixia, so we had better define all our values
        try:
            missing_fields_set = set(self._interface_missing_iter)

            # if we are only missing driver then maybe we can get kernel module
            # this requires vpci
            if missing_fields_set == {'driver'}:
                self._probe_dpdk_drivers()
                # we can't reprobe missing values because we may not have netdev info

            # if there are any other missing then we have to netdev probe
            if missing_fields_set.difference({'driver'}):
                self._probe_netdevs()
                try:
                    self._probe_missing_values()
                except IncorrectConfig:
                    # ignore for now
                    pass

                # check again and verify we have all the fields
                if set(self._interface_missing_iter):
                    # last chance fallback, rebind everything and probe
                    # this probably won't work
                    self._force_rebind()
                    self._probe_netdevs()
                    self._probe_missing_values()

            errors = ("{} missing: {}".format(name, ", ".join(missing_fields)) for
                      name, missing_fields in self._interface_missing_map.items() if
                      missing_fields)
            errors = "\n".join(errors)
            if errors:
                raise IncorrectSetup(errors)

        finally:
            self._dpdk_helper = None


class DpdkBindHelper(object):
    DPDK_STATUS_CMD = "{dpdk_devbind} --status"
    DPDK_BIND_CMD = "sudo {dpdk_devbind} {force} -b {driver} {vpci}"

    NIC_ROW_RE = re.compile(r"([^ ]+) '([^']+)' (?:if=([^ ]+) )?drv=([^ ]+) "
                            r"unused=([^ ]*)(?: (\*Active\*))?")
    SKIP_RE = re.compile('(====|<none>|^$)')
    NIC_ROW_FIELDS = ['vpci', 'dev_type', 'iface', 'driver', 'unused', 'active']

    UIO_DRIVER = "uio"

    HEADER_DICT_PAIRS = [
        (re.compile('^Network.*DPDK.*$'), NETWORK_DPDK),
        (re.compile('^Network.*kernel.*$'), NETWORK_KERNEL),
        (re.compile('^Other network.*$'), NETWORK_OTHER),
        (re.compile('^Crypto.*DPDK.*$'), CRYPTO_DPDK),
        (re.compile('^Crypto.*kernel$'), CRYPTO_KERNEL),
        (re.compile('^Other crypto.*$'), CRYPTO_OTHER),
    ]

    FIND_NETDEVICE_STRING = r"""\
find /sys/devices/pci* -type d -name net -exec sh -c '{ grep -sH ^ \
$1/ifindex $1/address $1/operstate $1/device/vendor $1/device/device \
$1/device/subsystem_vendor $1/device/subsystem_device $1/device/numa_node ; \
printf "%s/driver:" $1 ; basename $(readlink -s $1/device/driver); } \
' sh  \{\}/* \;
"""

    BASE_ADAPTER_RE = re.compile('^/sys/devices/(.*)/net/([^/]*)/([^:]*):(.*)$', re.M)
    DPDK_DEVBIND = "dpdk-devbind.py"

    @classmethod
    def parse_netdev_info(cls, stdout):
        network_devices = defaultdict(dict)
        match_iter = (match.groups() for match in cls.BASE_ADAPTER_RE.finditer(stdout))
        for bus_path, interface_name, name, value in match_iter:
            dir_name, bus_id = os.path.split(bus_path)
            if 'virtio' in bus_id:
                # for some stupid reason VMs include virtio1/
                # in PCI device path
                bus_id = os.path.basename(dir_name)

            # remove extra 'device/' from 'device/vendor,
            # device/subsystem_vendor', etc.
            if 'device' in name:
                name = name.split('/')[1]

            network_devices[interface_name].update({
                name: value,
                'interface_name': interface_name,
                'pci_bus_id': bus_id,
            })

        # convert back to regular dict
        return dict(network_devices)

    def clean_status(self):
        self.dpdk_status = {
            NETWORK_KERNEL: [],
            NETWORK_DPDK: [],
            CRYPTO_KERNEL: [],
            CRYPTO_DPDK: [],
            NETWORK_OTHER: [],
            CRYPTO_OTHER: [],
        }

    # TODO: add support for driver other than igb_uio
    def __init__(self, ssh_helper, dpdk_driver="igb_uio"):
        self.ssh_helper = ssh_helper
        self.real_kernel_interface_driver_map = {}
        self.dpdk_driver = dpdk_driver
        self.dpdk_status = None
        self.status_nic_row_re = None
        self.dpdk_devbind = self.ssh_helper.join_bin_path(self.DPDK_DEVBIND)
        self._status_cmd_attr = None
        self.used_drivers = None
        self.real_kernel_drivers = {}

        self.ssh_helper = ssh_helper
        self.clean_status()

    def _dpdk_execute(self, *args, **kwargs):
        res = self.ssh_helper.execute(*args, **kwargs)
        if res[0] != 0:
            template = '{} command failed with rc={}'
            raise DpdkBindHelperException(template.format(self.dpdk_devbind, res[0]))
        return res

    def load_dpdk_driver(self):
        cmd_template = "sudo modprobe {} && sudo modprobe {}"
        self.ssh_helper.execute(cmd_template.format(self.UIO_DRIVER, self.dpdk_driver))

    def check_dpdk_driver(self):
        return self.ssh_helper.execute("lsmod | grep -i {}".format(self.dpdk_driver))[0]

    @property
    def _status_cmd(self):
        if self._status_cmd_attr is None:
            self._status_cmd_attr = self.DPDK_STATUS_CMD.format(dpdk_devbind=self.dpdk_devbind)
        return self._status_cmd_attr

    def _add_line(self, active_list, line):
        if active_list is None:
            return

        res = self.NIC_ROW_RE.match(line)
        if res is None:
            return

        new_data = {k: v for k, v in zip(self.NIC_ROW_FIELDS, res.groups())}
        new_data['active'] = bool(new_data['active'])
        self.dpdk_status[active_list].append(new_data)

    @classmethod
    def _switch_active_dict(cls, a_row, active_dict):
        for regexp, a_dict in cls.HEADER_DICT_PAIRS:
            if regexp.match(a_row):
                return a_dict
        return active_dict

    def _parse_dpdk_status_output(self, output):
        active_dict = None
        self.clean_status()
        for a_row in output.splitlines():
            if self.SKIP_RE.match(a_row):
                continue
            active_dict = self._switch_active_dict(a_row, active_dict)
            self._add_line(active_dict, a_row)
        return self.dpdk_status

    def _get_bound_pci_addresses(self, active_dict):
        return [iface['vpci'] for iface in self.dpdk_status[active_dict]]

    @property
    def dpdk_bound_pci_addresses(self):
        return self._get_bound_pci_addresses(NETWORK_DPDK)

    @property
    def kernel_bound_pci_addresses(self):
        return self._get_bound_pci_addresses(NETWORK_KERNEL)

    @property
    def interface_driver_map(self):
        return {interface['vpci']: interface['driver']
                for interface in chain.from_iterable(self.dpdk_status.values())}

    def read_status(self):
        return self._parse_dpdk_status_output(self._dpdk_execute(self._status_cmd)[1])

    def find_net_devices(self):
        exit_status, stdout, _ = self.ssh_helper.execute(self.FIND_NETDEVICE_STRING)
        if exit_status != 0:
            return {}

        return self.parse_netdev_info(stdout)

    def bind(self, pci_addresses, driver, force=True):
        # accept single PCI or sequence of PCI
        pci_addresses = validate_non_string_sequence(pci_addresses, [pci_addresses])

        cmd = self.DPDK_BIND_CMD.format(dpdk_devbind=self.dpdk_devbind,
                                        driver=driver,
                                        vpci=' '.join(list(pci_addresses)),
                                        force='--force' if force else '')
        LOG.debug(cmd)
        self._dpdk_execute(cmd)

        # update the inner status dict
        self.read_status()

    def probe_real_kernel_drivers(self):
        self.read_status()
        self.save_real_kernel_interface_driver_map()

    def force_dpdk_rebind(self):
        self.load_dpdk_driver()
        self.read_status()
        self.save_real_kernel_interface_driver_map()
        self.save_used_drivers()

        real_driver_map = {}
        # only rebind devices that are bound to DPDK
        for pci in self.dpdk_bound_pci_addresses:
            # messy
            real_driver = self.real_kernel_interface_driver_map[pci]
            real_driver_map.setdefault(real_driver, []).append(pci)
        for real_driver, pcis in real_driver_map.items():
            self.bind(pcis, real_driver, force=True)

    def save_used_drivers(self):
        # invert the map, so we can bind by driver type
        self.used_drivers = {}
        # sort for stability
        for vpci, driver in sorted(self.interface_driver_map.items()):
            self.used_drivers.setdefault(driver, []).append(vpci)

    KERNEL_DRIVER_RE = re.compile(r"Kernel modules: (\S+)", re.M)
    VIRTIO_DRIVER_RE = re.compile(r"Ethernet.*Virtio network device", re.M)
    VIRTIO_DRIVER = "virtio-pci"

    def save_real_kernel_drivers(self):
        # invert the map, so we can bind by driver type
        self.real_kernel_drivers = {}
        # sort for stability
        for vpci, driver in sorted(self.real_kernel_interface_driver_map.items()):
            self.used_drivers.setdefault(driver, []).append(vpci)

    def get_real_kernel_driver(self, pci):
        out = self.ssh_helper.execute('lspci -k -s %s' % pci)[1]
        match = self.KERNEL_DRIVER_RE.search(out)
        if match:
            return match.group(1)

        match = self.VIRTIO_DRIVER_RE.search(out)
        if match:
            return self.VIRTIO_DRIVER

        return None

    def save_real_kernel_interface_driver_map(self):
        iter1 = ((pci, self.get_real_kernel_driver(pci)) for pci in self.interface_driver_map)
        self.real_kernel_interface_driver_map = {pci: driver for pci, driver in iter1 if driver}

    def rebind_drivers(self, force=True):
        for driver, vpcis in self.used_drivers.items():
            self.bind(vpcis, driver, force)
