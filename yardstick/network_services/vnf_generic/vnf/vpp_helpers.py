# Copyright (c) 2019 Viosoft Corporation
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
from collections import OrderedDict

from yardstick.network_services.vnf_generic.vnf.sample_vnf import \
    DpdkVnfSetupEnvHelper

LOG = logging.getLogger(__name__)


class VppConfigGenerator(object):
    VPP_LOG_FILE = '/tmp/vpe.log'

    def __init__(self):
        self._nodeconfig = {}
        self._vpp_config = ''

    def add_config_item(self, config, value, path):
        if len(path) == 1:
            config[path[0]] = value
            return
        if path[0] not in config:
            config[path[0]] = {}
        elif isinstance(config[path[0]], str):
            config[path[0]] = {} if config[path[0]] == '' \
                else {config[path[0]]: ''}
        self.add_config_item(config[path[0]], value, path[1:])

    def add_unix_log(self, value=None):
        path = ['unix', 'log']
        if value is None:
            value = self.VPP_LOG_FILE
        self.add_config_item(self._nodeconfig, value, path)

    def add_unix_cli_listen(self, value='/run/vpp/cli.sock'):
        path = ['unix', 'cli-listen']
        self.add_config_item(self._nodeconfig, value, path)

    def add_unix_nodaemon(self):
        path = ['unix', 'nodaemon']
        self.add_config_item(self._nodeconfig, '', path)

    def add_unix_coredump(self):
        path = ['unix', 'full-coredump']
        self.add_config_item(self._nodeconfig, '', path)

    def add_dpdk_dev(self, *devices):
        for device in devices:
            if VppConfigGenerator.pci_dev_check(device):
                path = ['dpdk', 'dev {0}'.format(device)]
                self.add_config_item(self._nodeconfig, '', path)

    def add_dpdk_cryptodev(self, count, cryptodev):
        for i in range(count):
            cryptodev_config = 'dev {0}'.format(
                re.sub(r'\d.\d$', '1.' + str(i), cryptodev))
            path = ['dpdk', cryptodev_config]
            self.add_config_item(self._nodeconfig, '', path)
        self.add_dpdk_uio_driver('igb_uio')

    def add_dpdk_sw_cryptodev(self, sw_pmd_type, socket_id, count):
        for _ in range(count):
            cryptodev_config = 'vdev cryptodev_{0}_pmd,socket_id={1}'. \
                format(sw_pmd_type, str(socket_id))
            path = ['dpdk', cryptodev_config]
            self.add_config_item(self._nodeconfig, '', path)

    def add_dpdk_dev_default_rxq(self, value):
        path = ['dpdk', 'dev default', 'num-rx-queues']
        self.add_config_item(self._nodeconfig, value, path)

    def add_dpdk_dev_default_rxd(self, value):
        path = ['dpdk', 'dev default', 'num-rx-desc']
        self.add_config_item(self._nodeconfig, value, path)

    def add_dpdk_dev_default_txd(self, value):
        path = ['dpdk', 'dev default', 'num-tx-desc']
        self.add_config_item(self._nodeconfig, value, path)

    def add_dpdk_log_level(self, value):
        path = ['dpdk', 'log-level']
        self.add_config_item(self._nodeconfig, value, path)

    def add_dpdk_socketmem(self, value):
        path = ['dpdk', 'socket-mem']
        self.add_config_item(self._nodeconfig, value, path)

    def add_dpdk_num_mbufs(self, value):
        path = ['dpdk', 'num-mbufs']
        self.add_config_item(self._nodeconfig, value, path)

    def add_dpdk_uio_driver(self, value=None):
        if value is None:
            pass
        path = ['dpdk', 'uio-driver']
        self.add_config_item(self._nodeconfig, value, path)

    def add_cpu_main_core(self, value):
        path = ['cpu', 'main-core']
        self.add_config_item(self._nodeconfig, value, path)

    def add_cpu_corelist_workers(self, value):
        path = ['cpu', 'corelist-workers']
        self.add_config_item(self._nodeconfig, value, path)

    def add_heapsize(self, value):
        path = ['heapsize']
        self.add_config_item(self._nodeconfig, value, path)

    def add_ip6_hash_buckets(self, value):
        path = ['ip6', 'hash-buckets']
        self.add_config_item(self._nodeconfig, value, path)

    def add_ip6_heap_size(self, value):
        path = ['ip6', 'heap-size']
        self.add_config_item(self._nodeconfig, value, path)

    def add_ip_heap_size(self, value):
        path = ['ip', 'heap-size']
        self.add_config_item(self._nodeconfig, value, path)

    def add_statseg_size(self, value):
        path = ['statseg', 'size']
        self.add_config_item(self._nodeconfig, value, path)

    def add_plugin(self, state, *plugins):
        for plugin in plugins:
            path = ['plugins', 'plugin {0}'.format(plugin), state]
            self.add_config_item(self._nodeconfig, ' ', path)

    def add_dpdk_no_multi_seg(self):
        path = ['dpdk', 'no-multi-seg']
        self.add_config_item(self._nodeconfig, '', path)

    def add_dpdk_no_tx_checksum_offload(self):
        path = ['dpdk', 'no-tx-checksum-offload']
        self.add_config_item(self._nodeconfig, '', path)

    def dump_config(self, obj=None, level=-1):
        if obj is None:
            obj = self._nodeconfig
        obj = OrderedDict(sorted(obj.items()))

        indent = '  '
        if level >= 0:
            self._vpp_config += '{}{{\n'.format(level * indent)
        if isinstance(obj, dict):
            for key, val in obj.items():
                if hasattr(val, '__iter__') and not isinstance(val, str):
                    self._vpp_config += '{}{}\n'.format((level + 1) * indent,
                                                        key)
                    self.dump_config(val, level + 1)
                else:
                    self._vpp_config += '{}{} {}\n'.format(
                        (level + 1) * indent,
                        key, val)
        # else:
        #    for val in obj:
        #        self._vpp_config += '{}{}\n'.format((level + 1) * indent, val)
        if level >= 0:
            self._vpp_config += '{}}}\n'.format(level * indent)

        return self._vpp_config

    @staticmethod
    def pci_dev_check(pci_dev):
        pattern = re.compile("^[0-9A-Fa-f]{4}:[0-9A-Fa-f]{2}:"
                             "[0-9A-Fa-f]{2}\\.[0-9A-Fa-f]$")
        if not pattern.match(pci_dev):
            raise ValueError('PCI address {addr} is not in valid format '
                             'xxxx:xx:xx.x'.format(addr=pci_dev))
        return True


class VppSetupEnvHelper(DpdkVnfSetupEnvHelper):
    APP_NAME = "vpp"
    CFG_CONFIG = "/etc/vpp/startup.conf"
    CFG_SCRIPT = ""
    PIPELINE_COMMAND = ""
    VNF_TYPE = "IPSEC"
    VAT_BIN_NAME = 'vpp_api_test'

    def __init__(self, vnfd_helper, ssh_helper, scenario_helper):
        super(VppSetupEnvHelper, self).__init__(vnfd_helper, ssh_helper,
                                                scenario_helper)

    def kill_vnf(self):
        ret_code, _, _ = \
            self.ssh_helper.execute(
                'service {name} stop'.format(name=self.APP_NAME))
        if int(ret_code):
            raise RuntimeError(
                'Failed to stop service {name}'.format(name=self.APP_NAME))

    def tear_down(self):
        pass

    def start_vpp_service(self):
        ret_code, _, _ = \
            self.ssh_helper.execute(
                'service {name} restart'.format(name=self.APP_NAME))
        if int(ret_code):
            raise RuntimeError(
                'Failed to start service {name}'.format(name=self.APP_NAME))

    def _update_vnfd_helper(self, additional_data, iface_key=None):
        for k, v in additional_data.items():
            if iface_key is None:
                if isinstance(v, dict) and k in self.vnfd_helper:
                    self.vnfd_helper[k].update(v)
                else:
                    self.vnfd_helper[k] = v
            else:
                if isinstance(v,
                              dict) and k in self.vnfd_helper.find_virtual_interface(
                    ifname=iface_key):
                    self.vnfd_helper.find_virtual_interface(ifname=iface_key)[
                        k].update(v)
                else:
                    self.vnfd_helper.find_virtual_interface(ifname=iface_key)[
                        k] = v

    def get_value_by_interface_key(self, interface, key):
        try:
            return self.vnfd_helper.find_virtual_interface(
                ifname=interface).get(key)
        except (KeyError, ValueError):
            return None
