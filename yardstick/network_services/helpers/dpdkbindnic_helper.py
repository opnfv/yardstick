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
import logging
import os

import re
import itertools
from collections import defaultdict

from yardstick.common.utils import validate_non_string_sequence
from yardstick.common.utils import value_iter_from_value_list_iter_if_key_in
from yardstick.error import IncorrectConfig
from yardstick.error import IncorrectSetup
from yardstick.error import IncorrectNodeSetup
from yardstick.error import SSHTimeout
from yardstick.error import SSHError
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.vnf_generic.vnf.vnf_ssh_helper import VnfSshHelper

NETWORK_KERNEL = 'network_kernel'
NETWORK_DPDK = 'network_dpdk'
NETWORK_OTHER = 'network_other'
CRYPTO_KERNEL = 'crypto_kernel'
CRYPTO_DPDK = 'crypto_dpdk'
CRYPTO_OTHER = 'crypto_other'


LOG = logging.getLogger(__name__)

TOPOLOGY_REQUIRED_KEYS = frozenset({
    "vpci", "local_ip", "netmask", "local_mac", "driver"})

TOPOLOGY_UPDATABLE_MAP = {
    "vpci": "pci_bus_id",
    "driver": "driver",
    "ifindex": "ifindex",
}


class DpdkBindHelperException(Exception):
    pass


class DpdkInterface(object):

    def __init__(self, dpdk_node, interface):
        super(DpdkInterface, self).__init__()
        self.dpdk_node = dpdk_node
        self.interface = interface
        self._missing_fields = None

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
        self._missing_fields = TOPOLOGY_REQUIRED_KEYS.difference(self.interface)
        return self._missing_fields

    def probe_missing_values(self):
        try:
            for netdev in self.dpdk_node.netdevs.values():
                if netdev['address'].lower() == self.mac_lower:
                    self.interface.update({
                        'vpci': netdev['pci_bus_id'],
                        'driver': netdev['driver'],
                        'ifindex': netdev['ifindex'],
                    })

        except KeyError:
            # if we don't find all the keys then don't update
            pass

        except (IncorrectNodeSetup, SSHError, SSHTimeout):
            raise IncorrectConfig(
                "Unable to probe missing interface fields '%s', on node %s "
                "SSH Error" % (', '.join(self.missing_fields), self.dpdk_node.node_key))

    def check(self):
        if not self.missing_fields:
            return

        self.probe_missing_values()

        # rebind
        self.dpdk_node.force_rebind()

        # probe gain
        self.dpdk_node.probe_devices()
        if not self.missing_fields:
            return

        template = "Required interface fields not found\n{0}: {1}"
        raise IncorrectSetup(template.format(self.local_mac, ", ".join(self._missing_fields)))


class DpdkNode(object):

    def __init__(self, node_key, node_dict, timeout=120):
        super(DpdkNode, self).__init__()
        self.node_key = node_key
        self.node_dict = node_dict
        self.overrides = {'wait': timeout}
        self._ssh_helper = None
        self._dpdk_helper = None
        self._netdevs = None

    @property
    def ssh_helper(self):
        if self._ssh_helper is None:
            self._ssh_helper = VnfSshHelper.from_node(self.node_dict, overrides=self.overrides)
        return self._ssh_helper

    @property
    def dpdk_helper(self):
        if not isinstance(self._dpdk_helper, DpdkBindHelper):
            self._dpdk_helper = DpdkBindHelper(self.ssh_helper, get_nsb_option('bin_path'))
        return self._dpdk_helper

    @property
    def netdevs(self):
        self.probe_devices()
        return self._netdevs

    def probe_devices(self):
        cmd = "PATH=$PATH:/sbin:/usr/sbin ip addr show"
        exit_status = self.ssh_helper.execute(cmd)[0]
        if exit_status != 0:
            raise IncorrectNodeSetup("Node %s had an error running ip tool." % self.node_key)

        try:
            return self.probe_netdevs()

        except IncorrectSetup:
            pass

        self.dpdk_helper.force_dpdk_rebind()

        # rediscover MAC address, PCI and driver after forced rebind
        return self.probe_netdevs()

    def probe_netdevs(self):
        try:
            netdevs = self.dpdk_helper.find_net_devices()

        except DpdkBindHelperException:
            raise IncorrectSetup("Cannot find netdev info in sysfs for node %s" % self.node_key)

        self.node_dict['netdevs'] = netdevs
        self._netdevs = netdevs
        return netdevs

    def force_rebind(self):
        return self.dpdk_helper.force_dpdk_rebind()

    def check(self):
        # if any interface is missing a value we must probe
        # only ssh probe if there are missing values
        # ssh probe won't work on Ixia, so we had better define all our values
        try:
            for interface in self.node_dict["interfaces"].values():
                dpdk_interface = DpdkInterface(self, interface)
                try:
                    dpdk_interface.check()

                except (SSHTimeout, SSHError):
                    pass

        finally:
            self._dpdk_helper = None
            if self._ssh_helper:
                self._ssh_helper.close()
                self._ssh_helper = None


class DpdkBindHelper(object):
    DPDK_STATUS_CMD = "{dpdk_nic_bind} --status"
    DPDK_BIND_CMD = "sudo {dpdk_nic_bind} {force} -b {driver} {vpci}"

    NIC_ROW_RE = re.compile("([^ ]+) '([^']+)' (?:if=([^ ]+) )?drv=([^ ]+) "
                            "unused=([^ ]*)(?: (\*Active\*))?")
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
$1/device/subsystem_vendor $1/device/subsystem_device ; \
printf "%s/driver:" $1 ; basename $(readlink -s $1/device/driver); } \
' sh  \{\}/* \;
"""

    BASE_ADAPTER_RE = re.compile('^/sys/devices/(.*)/net/([^/]*)/([^:]*):(.*)$', re.M)

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
    def __init__(self, ssh_helper, bin_path, dpdk_driver="igb_uio"):
        self.real_kernel_interface_driver_map = {}
        self.bin_path = bin_path
        self.dpdk_driver = dpdk_driver
        self.dpdk_status = None
        self.status_nic_row_re = None
        self._dpdk_nic_bind_attr = None
        self._status_cmd_attr = None
        self.used_drivers = None
        self.real_kernel_drivers = {}

        self.ssh_helper = ssh_helper
        self.clean_status()

    def _dpdk_execute(self, *args, **kwargs):
        res = self.ssh_helper.execute(*args, **kwargs)
        if res[0] != 0:
            template = '{} command failed with rc={}'
            raise DpdkBindHelperException(template.format(self._dpdk_nic_bind, res[0]))
        return res

    def load_dpdk_driver(self):
        cmd_template = "sudo modprobe {} && sudo modprobe {}"
        self.ssh_helper.execute(cmd_template.format(self.UIO_DRIVER, self.dpdk_driver))

    def check_dpdk_driver(self):
        return self.ssh_helper.execute("lsmod | grep -i {}".format(self.dpdk_driver))[0]

    @property
    def _dpdk_nic_bind(self):
        if self._dpdk_nic_bind_attr is None:
            self._dpdk_nic_bind_attr = self.ssh_helper.provision_tool(tool_path=self.bin_path,
                                                                      tool_file="dpdk-devbind.py")
        return self._dpdk_nic_bind_attr

    @property
    def _status_cmd(self):
        if self._status_cmd_attr is None:
            self._status_cmd_attr = self.DPDK_STATUS_CMD.format(dpdk_nic_bind=self._dpdk_nic_bind)
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

    def parse_dpdk_status_output(self, output):
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
                for interface in itertools.chain.from_iterable(self.dpdk_status.values())}

    def read_status(self):
        return self.parse_dpdk_status_output(self._dpdk_execute(self._status_cmd)[1])

    def find_net_devices(self):
        exit_status, stdout, _ = self.ssh_helper.execute(self.FIND_NETDEVICE_STRING)
        if exit_status != 0:
            raise DpdkBindHelperException()

        return self.parse_netdev_info(stdout)

    def bind(self, pci_addresses, driver, force=True):
        # accept single PCI or sequence of PCI
        pci_addresses = validate_non_string_sequence(pci_addresses, [pci_addresses])

        cmd = self.DPDK_BIND_CMD.format(dpdk_nic_bind=self._dpdk_nic_bind,
                                        driver=driver,
                                        vpci=' '.join(list(pci_addresses)),
                                        force='--force' if force else '')
        LOG.debug(cmd)
        self._dpdk_execute(cmd)

        # update the inner status dict
        self.read_status()

    def force_dpdk_rebind(self):
        self.load_dpdk_driver()
        self.read_status()
        self.get_real_kernel_drivers()
        self.save_used_drivers()

        valid_keys = {self.dpdk_driver}
        for pci in value_iter_from_value_list_iter_if_key_in(self.used_drivers, valid_keys):
            # messy
            real_driver = self.real_kernel_interface_driver_map[pci]
            self.bind([pci], real_driver, force=True)

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

    def get_real_kernel_drivers(self):
        iter1 = ((pci, self.get_real_kernel_driver(pci)) for pci in self.interface_driver_map)
        self.real_kernel_interface_driver_map = {pci: driver for pci, driver in iter1 if driver}

    def rebind_drivers(self, force=True):
        for driver, vpcis in self.used_drivers.items():
            self.bind(vpcis, driver, force)
