# Copyright (c) 2018 Viosoft Corporation
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

import binascii
import ipaddress
import json
import logging
import os
import re
import tempfile
import time
from collections import OrderedDict

from yardstick.common import constants
from yardstick.common import exceptions
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

    def vpp_create_ipsec_tunnels(self, if1_ip_addr, if2_ip_addr, if_name,
                                 n_tunnels, n_connections, crypto_alg,
                                 crypto_key, integ_alg, integ_key, addrs_ip,
                                 spi_1=10000, spi_2=20000):
        mask_length = 32
        if n_connections <= n_tunnels:
            count = 1
        else:
            count = int(n_connections / n_tunnels)
        addr_ip_i = int(ipaddress.ip_address(str(addrs_ip)))
        dst_start_ip = addr_ip_i

        tmp_fd, tmp_path = tempfile.mkstemp()

        vpp_ifname = self.get_value_by_interface_key(if_name, 'vpp_name')
        ckey = binascii.hexlify(crypto_key.encode())
        ikey = binascii.hexlify(integ_key.encode())

        integ = ''
        if crypto_alg.alg_name != 'aes-gcm-128':
            integ = 'integ_alg {integ_alg} ' \
                    'local_integ_key {local_integ_key} ' \
                    'remote_integ_key {remote_integ_key} ' \
                .format(integ_alg=integ_alg.alg_name,
                        local_integ_key=ikey,
                        remote_integ_key=ikey)
        create_tunnels_cmds = 'ipsec_tunnel_if_add_del ' \
                              'local_spi {local_spi} ' \
                              'remote_spi {remote_spi} ' \
                              'crypto_alg {crypto_alg} ' \
                              'local_crypto_key {local_crypto_key} ' \
                              'remote_crypto_key {remote_crypto_key} ' \
                              '{integ} ' \
                              'local_ip {local_ip} ' \
                              'remote_ip {remote_ip}\n'
        start_tunnels_cmds = 'ip_add_del_route {raddr}/{mask} via {addr} ipsec{i}\n' \
                             'exec set interface unnumbered ipsec{i} use {uifc}\n' \
                             'sw_interface_set_flags ipsec{i} admin-up\n'

        with os.fdopen(tmp_fd, 'w') as tmp_file:
            for i in range(0, n_tunnels):
                create_tunnel = create_tunnels_cmds.format(local_spi=spi_1 + i,
                                                           remote_spi=spi_2 + i,
                                                           crypto_alg=crypto_alg.alg_name,
                                                           local_crypto_key=ckey,
                                                           remote_crypto_key=ckey,
                                                           integ=integ,
                                                           local_ip=if1_ip_addr,
                                                           remote_ip=if2_ip_addr)
                tmp_file.write(create_tunnel)
        self.execute_script(tmp_path, json_out=False, copy_on_execute=True)
        os.remove(tmp_path)

        tmp_fd, tmp_path = tempfile.mkstemp()

        with os.fdopen(tmp_fd, 'w') as tmp_file:
            for i in range(0, n_tunnels):
                if count > 1:
                    dst_start_ip = addr_ip_i + i * count
                    dst_end_ip = ipaddress.ip_address(dst_start_ip + count - 1)
                    ips = [ipaddress.ip_address(ip) for ip in
                           [str(ipaddress.ip_address(dst_start_ip)),
                            str(dst_end_ip)]]
                    lowest_ip, highest_ip = min(ips), max(ips)
                    mask_length = self.get_prefix_length(int(lowest_ip),
                                                         int(highest_ip),
                                                         lowest_ip.max_prefixlen)
                    # TODO check duplicate route for some IPs
                elif count == 1:
                    dst_start_ip = addr_ip_i + i
                start_tunnel = start_tunnels_cmds.format(
                    raddr=str(ipaddress.ip_address(dst_start_ip)),
                    mask=mask_length,
                    addr=if2_ip_addr,
                    i=i, count=count,
                    uifc=vpp_ifname)
                tmp_file.write(start_tunnel)
            # TODO add route for remain IPs

        self.execute_script(tmp_path, json_out=False, copy_on_execute=True)
        os.remove(tmp_path)

    def apply_config(self, vpp_cfg, restart_vpp=True):
        vpp_config = vpp_cfg.dump_config()
        ret, _, _ = \
            self.ssh_helper.execute('echo "{config}" | sudo tee {filename}'.
                                    format(config=vpp_config,
                                           filename=self.CFG_CONFIG))
        if ret != 0:
            raise RuntimeError('Writing config file failed')
        if restart_vpp:
            self.start_vpp_service()

    def vpp_route_add(self, network, prefix_len, gateway=None, interface=None,
                      use_sw_index=True, resolve_attempts=10,
                      count=1, vrf=None, lookup_vrf=None, multipath=False,
                      weight=None, local=False):
        if interface:
            if use_sw_index:
                int_cmd = ('sw_if_index {}'.format(
                    self.get_value_by_interface_key(interface,
                                                    'vpp_sw_index')))
            else:
                int_cmd = interface
        else:
            int_cmd = ''

        rap = 'resolve-attempts {}'.format(resolve_attempts) \
            if resolve_attempts else ''

        via = 'via {}'.format(gateway) if gateway else ''

        cnt = 'count {}'.format(count) \
            if count else ''

        vrf = 'vrf {}'.format(vrf) if vrf else ''

        lookup_vrf = 'lookup-in-vrf {}'.format(
            lookup_vrf) if lookup_vrf else ''

        multipath = 'multipath' if multipath else ''

        weight = 'weight {}'.format(weight) if weight else ''

        local = 'local' if local else ''

        with VatTerminal(self.ssh_helper, json_param=False) as vat:
            vat.vat_terminal_exec_cmd_from_template('add_route.vat',
                                                    network=network,
                                                    prefix_length=prefix_len,
                                                    via=via,
                                                    vrf=vrf,
                                                    interface=int_cmd,
                                                    resolve_attempts=rap,
                                                    count=cnt,
                                                    lookup_vrf=lookup_vrf,
                                                    multipath=multipath,
                                                    weight=weight,
                                                    local=local)

    def add_arp_on_dut(self, iface_key, ip_address, mac_address):
        with VatTerminal(self.ssh_helper) as vat:
            return vat.vat_terminal_exec_cmd_from_template(
                'add_ip_neighbor.vat',
                sw_if_index=self.get_value_by_interface_key(iface_key,
                                                            'vpp_sw_index'),
                ip_address=ip_address, mac_address=mac_address)

    def set_ip(self, interface, address, prefix_length):
        with VatTerminal(self.ssh_helper) as vat:
            return vat.vat_terminal_exec_cmd_from_template(
                'add_ip_address.vat',
                sw_if_index=self.get_value_by_interface_key(interface,
                                                            'vpp_sw_index'),
                address=address, prefix_length=prefix_length)

    def set_interface_state(self, interface, state):
        sw_if_index = self.get_value_by_interface_key(interface,
                                                      'vpp_sw_index')

        if state == 'up':
            state = 'admin-up link-up'
        elif state == 'down':
            state = 'admin-down link-down'
        else:
            raise ValueError('Unexpected interface state: {}'.format(state))
        with VatTerminal(self.ssh_helper) as vat:
            return vat.vat_terminal_exec_cmd_from_template(
                'set_if_state.vat', sw_if_index=sw_if_index, state=state)

    def vpp_set_interface_mtu(self, interface, mtu=9200):
        sw_if_index = self.get_value_by_interface_key(interface,
                                                      'vpp_sw_index')
        if sw_if_index:
            with VatTerminal(self.ssh_helper, json_param=False) as vat:
                vat.vat_terminal_exec_cmd_from_template(
                    "hw_interface_set_mtu.vat", sw_if_index=sw_if_index,
                    mtu=mtu)

    def vpp_interfaces_ready_wait(self, timeout=30):
        if_ready = False
        not_ready = []
        start = time.time()
        while not if_ready:
            out = self.vpp_get_interface_data()
            if time.time() - start > timeout:
                for interface in out:
                    if interface.get('admin_up_down') == 1:
                        if interface.get('link_up_down') != 1:
                            LOG.debug('%s link-down',
                                      interface.get('interface_name'))
                raise RuntimeError('timeout, not up {0}'.format(not_ready))
            not_ready = []
            for interface in out:
                if interface.get('admin_up_down') == 1:
                    if interface.get('link_up_down') != 1:
                        not_ready.append(interface.get('interface_name'))
            if not not_ready:
                if_ready = True
            else:
                LOG.debug('Interfaces still in link-down state: %s, '
                          'waiting...', not_ready)
                time.sleep(1)

    def vpp_get_interface_data(self, interface=None):
        with VatTerminal(self.ssh_helper) as vat:
            response = vat.vat_terminal_exec_cmd_from_template(
                "interface_dump.vat")
        data = response[0]
        if interface is not None:
            if isinstance(interface, str):
                param = "interface_name"
            elif isinstance(interface, int):
                param = "sw_if_index"
            else:
                raise TypeError
            for data_if in data:
                if data_if[param] == interface:
                    return data_if
            return dict()
        return data

    def update_vpp_interface_data(self):
        data = {}
        interface_dump_json = self.execute_script_json_out(
            "dump_interfaces.vat")
        interface_list = json.loads(interface_dump_json)
        for interface in self.vnfd_helper.interfaces:
            if_mac = interface['virtual-interface']['local_mac']
            interface_dict = VppSetupEnvHelper.get_vpp_interface_by_mac(
                interface_list, if_mac)
            if not interface_dict:
                LOG.debug('Interface %s not found by MAC %s', interface,
                          if_mac)
                continue
            data[interface['virtual-interface']['ifname']] = {
                'vpp_name': interface_dict["interface_name"],
                'vpp_sw_index': interface_dict["sw_if_index"]
            }
        for iface_key, updated_vnfd in data.items():
            self._update_vnfd_helper(updated_vnfd, iface_key)

    def iface_update_numa(self):
        iface_numa = {}
        for interface in self.vnfd_helper.interfaces:
            cmd = "cat /sys/bus/pci/devices/{}/numa_node".format(
                interface["virtual-interface"]["vpci"])
            ret, out, _ = self.ssh_helper.execute(cmd)
            if ret == 0:
                try:
                    numa_node = int(out)
                    if numa_node < 0:
                        if self.vnfd_helper["cpuinfo"][-1][3] + 1 == 1:
                            iface_numa[
                                interface['virtual-interface']['ifname']] = {
                                'numa_node': 0
                            }
                        else:
                            raise ValueError
                    else:
                        iface_numa[
                            interface['virtual-interface']['ifname']] = {
                            'numa_node': numa_node
                        }
                except ValueError:
                    LOG.debug(
                        'Reading numa location failed for: %s',
                        interface["virtual-interface"]["vpci"])
        for iface_key, updated_vnfd in iface_numa.items():
            self._update_vnfd_helper(updated_vnfd, iface_key)

    def execute_script(self, vat_name, json_out=True, copy_on_execute=False):
        if copy_on_execute:
            self.ssh_helper.put_file(vat_name, vat_name)
            remote_file_path = vat_name
        else:
            vat_path = self.ssh_helper.join_bin_path("vpp", "templates")
            remote_file_path = '{0}/{1}'.format(vat_path, vat_name)

        cmd = "{vat_bin} {json} in {vat_path} script".format(
            vat_bin=self.VAT_BIN_NAME,
            json="json" if json_out is True else "",
            vat_path=remote_file_path)

        try:
            return self.ssh_helper.execute(cmd=cmd)
        except Exception:
            raise RuntimeError("VAT script execution failed: {0}".format(cmd))

    def execute_script_json_out(self, vat_name):
        vat_path = self.ssh_helper.join_bin_path("vpp", "templates")
        remote_file_path = '{0}/{1}'.format(vat_path, vat_name)

        _, stdout, _ = self.execute_script(vat_name, json_out=True)
        return self.cleanup_vat_json_output(stdout, vat_file=remote_file_path)

    @staticmethod
    def cleanup_vat_json_output(json_output, vat_file=None):
        retval = json_output
        clutter = ['vat#', 'dump_interface_table error: Misc',
                   'dump_interface_table:6019: JSON output supported only ' \
                   'for VPE API calls and dump_stats_table']
        if vat_file:
            clutter.append("{0}(2):".format(vat_file))
        for garbage in clutter:
            retval = retval.replace(garbage, '')
        return retval.strip()

    @staticmethod
    def _convert_mac_to_number_list(mac_address):
        list_mac = []
        for num in mac_address.split(":"):
            list_mac.append(int(num, 16))
        return list_mac

    @staticmethod
    def get_vpp_interface_by_mac(interfaces_list, mac_address):
        interface_dict = {}
        list_mac_address = VppSetupEnvHelper._convert_mac_to_number_list(
            mac_address)
        LOG.debug("MAC address %s converted to list %s.", mac_address,
                  list_mac_address)
        for interface in interfaces_list:
            # TODO: create vat json integrity checking and move there
            if "l2_address" not in interface:
                raise KeyError(
                    "key l2_address not found in interface dict."
                    "Probably input list is not parsed from correct VAT "
                    "json output.")
            if "l2_address_length" not in interface:
                raise KeyError(
                    "key l2_address_length not found in interface "
                    "dict. Probably input list is not parsed from correct "
                    "VAT json output.")
            mac_from_json = interface["l2_address"][:6]
            if mac_from_json == list_mac_address:
                if interface["l2_address_length"] != 6:
                    raise ValueError("l2_address_length value is not 6.")
                interface_dict = interface
                break
        return interface_dict

    @staticmethod
    def get_prefix_length(number1, number2, bits):
        for i in range(bits):
            if number1 >> i == number2 >> i:
                return bits - i
        return 0


class VatTerminal(object):

    __VAT_PROMPT = ("vat# ",)
    __LINUX_PROMPT = (":~# ", ":~$ ", "~]$ ", "~]# ")


    def __init__(self, ssh_helper, json_param=True):
        json_text = ' json' if json_param else ''
        self.json = json_param
        self.ssh_helper = ssh_helper
        EXEC_RETRY = 3

        try:
            self._tty = self.ssh_helper.interactive_terminal_open()
        except Exception:
            raise RuntimeError("Cannot open interactive terminal")

        for _ in range(EXEC_RETRY):
            try:
                self.ssh_helper.interactive_terminal_exec_command(
                    self._tty,
                    'sudo -S {0}{1}'.format(VppSetupEnvHelper.VAT_BIN_NAME,
                                            json_text),
                    self.__VAT_PROMPT)
            except exceptions.SSHTimeout:
                continue
            else:
                break

        self._exec_failure = False
        self.vat_stdout = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.vat_terminal_close()

    def vat_terminal_exec_cmd(self, cmd):
        try:
            out = self.ssh_helper.interactive_terminal_exec_command(self._tty,
                                                                    cmd,
                                                                    self.__VAT_PROMPT)
            self.vat_stdout = out
        except exceptions.SSHTimeout:
            self._exec_failure = True
            raise RuntimeError(
                "VPP is not running on node. VAT command {0} execution failed".
                    format(cmd))
        if self.json:
            obj_start = out.find('{')
            obj_end = out.rfind('}')
            array_start = out.find('[')
            array_end = out.rfind(']')

            if obj_start == -1 and array_start == -1:
                raise RuntimeError(
                    "VAT command {0}: no JSON data.".format(cmd))

            if obj_start < array_start or array_start == -1:
                start = obj_start
                end = obj_end + 1
            else:
                start = array_start
                end = array_end + 1
            out = out[start:end]
            json_out = json.loads(out)
            return json_out
        else:
            return None

    def vat_terminal_close(self):
        if not self._exec_failure:
            try:
                self.ssh_helper.interactive_terminal_exec_command(self._tty,
                                                                  'quit',
                                                                  self.__LINUX_PROMPT)
            except exceptions.SSHTimeout:
                raise RuntimeError("Failed to close VAT console")
        try:
            self.ssh_helper.interactive_terminal_close(self._tty)
        except Exception:
            raise RuntimeError("Cannot close interactive terminal")

    def vat_terminal_exec_cmd_from_template(self, vat_template_file, **args):
        file_path = os.path.join(constants.YARDSTICK_ROOT_PATH,
                                 'yardstick/resources/templates/',
                                 vat_template_file)
        with open(file_path, 'r') as template_file:
            cmd_template = template_file.readlines()
        ret = []
        for line_tmpl in cmd_template:
            vat_cmd = line_tmpl.format(**args)
            ret.append(self.vat_terminal_exec_cmd(vat_cmd.replace('\n', '')))
        return ret
