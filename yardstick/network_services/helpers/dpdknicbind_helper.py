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
import re
import itertools

KERNEL = 'kernel'
DPDK = 'dpdk'


class DpdkBindHelper(object):
    DPDK_STATUS_CMD = "{dpdk_nic_bind} --status"
    DPDK_BIND_CMD = "sudo {dpdk_nic_bind} {force} -b {driver} {vpci}"

    NIC_ROW_RE = re.compile("([^ ]+) '([^']+)' (?:if=([^ ]+) )?drv=([^ ]+) "
                            "unused=([^ ]*)(?: (\*Active\*))?")

    def clean_status(self):
        self.dpdk_status = {
            KERNEL: [],
            DPDK: [],
            'other': [],
        }

    def __init__(self, ssh_helper):
        self.ssh_helper = ssh_helper
        self.clean_status()
        self.status_nic_row_re = None
        self._dpdk_nic_bind_attr = None
        self._status_cmd_attr = None

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
        if res is not None:
            vpci, dev_type, iface, driver, unused, active = res.groups()
            self.dpdk_status[active_list].append({
                'vpci': vpci,
                'dev_type': dev_type,
                'iface': iface,
                'driver': driver,
                'unused': unused,
                'active': active is not None,
            })

    def parse_dpdk_status_output(self, input):

        active_dict = None

        self.clean_status()

        for a_row in input.splitlines():
            if '====' in a_row or '<none>' in a_row:
                continue
            if a_row == '':
                active_dict = None
                continue

            if 'devices using' in a_row:
                if 'kernel' in a_row:
                    active_dict = KERNEL
                elif 'DPDK' in a_row:
                    active_dict = DPDK
            elif 'Other network devices' in a_row:
                active_dict = 'other'
            else:
                self._addline(active_dict, a_row)

        return self.dpdk_status

    def _get_bound_pci_addresses(self, active_dict):
        return [iface['vpci'] for iface in self.dpdk_status[active_dict]]

    @property
    def dpdk_bound_pci_addresses(self):
        return self._get_bound_pci_addresses(DPDK)

    @property
    def kernel_bound_pci_addresses(self):
        return self._get_bound_pci_addresses(KERNEL)

    @property
    def interface_driver_map(self):
        return {interface['vpci']: interface['driver']
                for interface in itertools.chain(*self.dpdk_status.values())}

    def read_status(self):
        rc, stdout, _ = self.ssh_helper.execute(self._status_cmd)
        return self.parse_dpdk_status_output(stdout)

    def bind(self, pci, driver, force=True):
        cmd = self.DPDK_BIND_CMD.format(dpdk_nic_bind=self._dpdk_nic_bind,
                                        driver=driver,
                                        vpci=' '.join(list(pci)),
                                        force='--force' if force else '')
        rc, _, _ = self.ssh_helper.execute(cmd)
        # update the inner status dict
        self.read_status()
        return rc

    def save_used_drivers(self):
        self.used_drivers = self.interface_driver_map

    def rebind_drivers(self, force=True):
        for vpci, driver in self.used_drivers.iteritems():
            self.bind(vpci, driver, force)
