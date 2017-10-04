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

import re
import itertools

import six

NETWORK_KERNEL = 'network_kernel'
NETWORK_DPDK = 'network_dpdk'
NETWORK_OTHER = 'network_other'
CRYPTO_KERNEL = 'crypto_kernel'
CRYPTO_DPDK = 'crypto_dpdk'
CRYPTO_OTHER = 'crypto_other'


LOG = logging.getLogger(__name__)


class DpdkBindHelperException(Exception):
    pass


class DpdkBindHelper(object):
    DPDK_STATUS_CMD = "{dpdk_nic_bind} --status"
    DPDK_BIND_CMD = "sudo {dpdk_nic_bind} {force} -b {driver} {vpci}"

    NIC_ROW_RE = re.compile("([^ ]+) '([^']+)' (?:if=([^ ]+) )?drv=([^ ]+) "
                            "unused=([^ ]*)(?: (\*Active\*))?")
    SKIP_RE = re.compile('(====|<none>|^$)')
    NIC_ROW_FIELDS = ['vpci', 'dev_type', 'iface', 'driver', 'unused', 'active']

    DPDK_DRIVER = "igb_uio"
    UIO_DRIVER = "uio"


    HEADER_DICT_PAIRS = [
        (re.compile('^Network.*DPDK.*$'), NETWORK_DPDK),
        (re.compile('^Network.*kernel.*$'), NETWORK_KERNEL),
        (re.compile('^Other network.*$'), NETWORK_OTHER),
        (re.compile('^Crypto.*DPDK.*$'), CRYPTO_DPDK),
        (re.compile('^Crypto.*kernel$'), CRYPTO_KERNEL),
        (re.compile('^Other crypto.*$'), CRYPTO_OTHER),
    ]

    def clean_status(self):
        self.dpdk_status = {
            NETWORK_KERNEL: [],
            NETWORK_DPDK: [],
            CRYPTO_KERNEL: [],
            CRYPTO_DPDK: [],
            NETWORK_OTHER: [],
            CRYPTO_OTHER: [],
        }

    def __init__(self, ssh_helper):
        self.dpdk_status = None
        self.status_nic_row_re = None
        self._dpdk_nic_bind_attr = None
        self._status_cmd_attr = None
        self.used_drivers = {}
        self.real_kernel_drivers = {}

        self.ssh_helper = ssh_helper
        self.clean_status()

    def _dpdk_execute(self, *args, **kwargs):
        res = self.ssh_helper.execute(*args, **kwargs)
        if res[0] != 0:
            raise DpdkBindHelperException('{} command failed with rc={}'.format(
                self._dpdk_nic_bind, res[0]))
        return res

    def load_dpdk_driver(self):
        self.ssh_helper.execute(
            "sudo modprobe {} && sudo modprobe {}".format(self.UIO_DRIVER, self.DPDK_DRIVER))

    def check_dpdk_driver(self):
        return self.ssh_helper.execute("lsmod | grep -i {}".format(self.DPDK_DRIVER))[0]

    @property
    def _dpdk_nic_bind(self):
        if self._dpdk_nic_bind_attr is None:
            self._dpdk_nic_bind_attr = self.ssh_helper.provision_tool(tool_file="dpdk-devbind.py")
        return self._dpdk_nic_bind_attr

    @property
    def _status_cmd(self):
        if self._status_cmd_attr is None:
            self._status_cmd_attr = self.DPDK_STATUS_CMD.format(dpdk_nic_bind=self._dpdk_nic_bind)
        return self._status_cmd_attr

    def _addline(self, active_list, line):
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

    def parse_dpdk_status_output(self, input):
        active_dict = None
        self.clean_status()
        for a_row in input.splitlines():
            if self.SKIP_RE.match(a_row):
                continue
            active_dict = self._switch_active_dict(a_row, active_dict)
            self._addline(active_dict, a_row)
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

    def bind(self, pci_addresses, driver, force=True):
        # accept single PCI or list of PCI
        if isinstance(pci_addresses, six.string_types):
            pci_addresses = [pci_addresses]
        cmd = self.DPDK_BIND_CMD.format(dpdk_nic_bind=self._dpdk_nic_bind,
                                        driver=driver,
                                        vpci=' '.join(list(pci_addresses)),
                                        force='--force' if force else '')
        LOG.debug(cmd)
        self._dpdk_execute(cmd)
        # update the inner status dict
        self.read_status()

    def save_used_drivers(self):
        # invert the map, so we can bind by driver type
        self.used_drivers = {}
        # sort for stabililty
        for vpci, driver in sorted(self.interface_driver_map.items()):
            self.used_drivers.setdefault(driver, []).append(vpci)

    def save_real_kernel_drivers(self):
        self.real_kernel_drivers = {}
        for pci in self.interface_driver_map:
            out = self.ssh_helper.execute('lspci -k -s %s' % pci)[1]
            real_driver = out.split('Kernel modules:').pop().strip()
            self.real_kernel_drivers.setdefault(real_driver, []).append(pci)

    def rebind_drivers(self, force=True):
        for driver, vpcis in self.used_drivers.items():
            self.bind(vpcis, driver, force)
