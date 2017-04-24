# Copyright (c) 2017 Intel Corporation
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

import array
import errno
import ipaddress
import logging
import multiprocessing
import os
import re
import select
import socket
from collections import OrderedDict
import time

from six.moves import map, zip

from yardstick import ssh
from yardstick.common.utils import parse_cpuinfo
from yardstick.network_services.utils import provision_tool
from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper
from yardstick.network_services.vnf_generic.vnf.iniparser import ConfigParser
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF

PROX_PORT = 8474

LOG = logging.getLogger(__name__)


def find_relative_file(path, task_path):
    # fixme: create schema to validate all fields have been provided
    try:
        with open(path):
            pass
        return path
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        else:
            rel_path = os.path.join(task_path, path)
            with open(rel_path):
                pass
            return rel_path


def calc_line_rate(arr, n_ports=1):
    ret = []
    for a in arr:
        ret.append(float(1250000000 * n_ports) / (a + 20) / 1000000)
    return ret


def line_rate_to_pps(pkt_size, n_ports):
    # FIXME Don't hardcode 10Gb/s
    return n_ports * float(10000000000 / 8) / (pkt_size + 20)


configurationOptions = (
    # dict key          section     key          Default value
    ('pktSizes', 'general', 'pkt_sizes', '64,128,256,512,1024,1280,1518'),
    ('testDuration', 'general', 'test_duration', 5.0),
    ('testPrecision', 'general', 'test_precision', 1.0),
    ('tests', 'general', 'tests', None),
    ('toleratedLoss', 'general', 'tolerated_loss', 0.0),

    ('logFile', 'logging', 'file', 'dats.log'),
    ('logDateFormat', 'logging', 'datefmt', None),
    ('logLevel', 'logging', 'level', 'INFO'),
    ('logOverwrite', 'logging', 'overwrite', 1),

    ('testerIp', 'tester', 'ip', None),
    ('testerUser', 'tester', 'user', 'root'),
    ('testerDpdkDir', 'tester', 'rte_sdk', '/root/dpdk'),
    ('testerDpdkTgt', 'tester', 'rte_target', 'x86_64-native-linuxapp-gcc'),
    ('testerProxDir', 'tester', 'prox_dir', '/root/prox'),
    ('testerSocketId', 'tester', 'socket_id', 0),

    ('sutIp', 'sut', 'ip', None),
    ('sutUser', 'sut', 'user', 'root'),
    ('sutDpdkDir', 'sut', 'rte_sdk', '/root/dpdk'),
    ('sutDpdkTgt', 'sut', 'rte_target', 'x86_64-native-linuxapp-gcc'),
    ('sutProxDir', 'sut', 'prox_dir', '/root/prox'),
    ('sutSocketId', 'sut', 'socket_id', 0),
)


class ProxBase(SampleVNF):

    PROX_MODE = ""

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        super(ProxBase, self).__init__(name, vnfd, setup_env_helper_type, resource_helper_type)
        self.additional_file = False
        self.mgmt_interface = self.vnfd_helper.mgmt_interface
        self._user = self.mgmt_interface["user"]
        self._ip = self.mgmt_interface["ip"]
        self.connection = ssh.SSH.from_node(self.mgmt_interface)
        self.connection.wait()

    @staticmethod
    def _split_mac_address_into_list(mac):
        return ["0x{}".format(o) for o in mac.split(':')]

    def _run_prox(self, filewrapper, mgmt_interface, config_path, prox_path,
                  prox_args):
        # This runs in a different process and should not share state
        # with the rest of the object
        connection = ssh.SSH.from_node(mgmt_interface)
        connection.wait()

        time.sleep(self.WAIT_TIME)

        args = " ".join(
            "{} {}".format(k, v if v else "") for k, v in prox_args.items())

        prox_cmd = "sudo bash -c 'cd {}; {} -o cli {} -f {} '".format(
            os.path.dirname(prox_path), prox_path, args, config_path)

        LOG.debug(prox_cmd)
        connection.run(prox_cmd, stdin=filewrapper, stdout=filewrapper,
                       keep_stdin_open=True, pty=False)

    def terminate(self):
        # try to quit with socket commands
        tester = self._get_socket()
        tester.stop_all()
        tester.quit()
        tester.force_quit()

    def rebind_drivers(self):
        for vpci, driver in self.used_drivers.items():
            self.connection.execute(
                "{dpdk_nic_bind} --force  -b {driver}"
                " {vpci}".format(vpci=vpci, driver=driver,
                                 dpdk_nic_bind=self.dpdk_nic_bind))

    @classmethod
    def setup_hugepages(cls, connection):
        hugepages = \
            connection.execute(
                "awk '/Hugepagesize/ { print $2$3 }' < /proc/meminfo")[1]
        hugepages = hugepages.rstrip()

        memory_path = \
            '/sys/kernel/mm/hugepages/hugepages-%s/nr_hugepages' % hugepages
        connection.execute("awk -F: '{ print $1 }' < %s" % memory_path)

        pages = 16384 if hugepages.rstrip() == "2048kB" else 16
        connection.execute("echo %s | sudo tee %s" % (pages, memory_path))

    def instantiate(self, scenario_cfg, context_cfg):
        LOG.info("printing .........prox instanciate ")
        self._terminated = multiprocessing.Value('i', 0)
        self._queue = multiprocessing.Value('i', 0)
        self.done = False

        if not self.connection:
            self.connection = ssh.SSH.from_node(self.mgmt_interface)
        self.connection.wait()
        self.cpu_topology = self.get_cpu_topology()
        # this won't work we need 1GB hugepages at boot
        self.setup_hugepages(self.connection)
        self._tester_cpu_map = self.get_cpu_topology()

        self.connection.execute("pkill prox")
        self.connection.execute("sudo modprobe uio")
        # for baremetal
        self.connection.execute("sudo modprobe msr")
        # why remove?, just keep it loaded
        # self.connection.execute("sudo rmmod igb_uio")
        self.dpdk_root = "/root/dpdk-17.02"
        igb_uio_path = os.path.join(
            self.dpdk_root, "x86_64-native-linuxapp-gcc/kmod/igb_uio.ko")
        self.connection.execute("sudo insmod {}".format(igb_uio_path))
        # quick hack to allow non-root copy
        self.connection.execute("sudo chmod 0777 {}".format(self.connection.bin_path))
        self.dpdk_nic_bind = \
            provision_tool(self.connection,
                           os.path.join(self.connection.bin_path, "dpdk-devbind.py"))
        self.interfaces = self.vnfd_helper.interfaces
        bound_pci = [v['virtual-interface']["vpci"] for v in self.interfaces]
        rc, dpdk_status, _ = self.connection.execute(
            "sudo {dpdk_nic_bind} -s".format(dpdk_nic_bind=self.dpdk_nic_bind))
        self.used_drivers = self.find_used_drivers(bound_pci, dpdk_status)
        for vpci in bound_pci:
            self.connection.execute(
                "sudo {dpdk_nic_bind} --force -b igb_uio"
                " {vpci}".format(vpci=vpci, dpdk_nic_bind=self.dpdk_nic_bind))
            time.sleep(self.WAIT_TIME)

        # debug dump after binding
        self.connection.execute(
            "sudo {dpdk_nic_bind} -s".format(dpdk_nic_bind=self.dpdk_nic_bind))
        # self.connection.run("cat /proc/cpuinfo")
        prox_args = scenario_cfg['vnf_options'][self.name]['prox_args']
        prox_path = scenario_cfg['vnf_options'][self.name]['prox_path']

        config_path = scenario_cfg['vnf_options'][self.name]['prox_config']
        config_file = os.path.basename(config_path)
        config_path = find_relative_file(config_path,
                                         scenario_cfg['task_path'])

        try:
            proxfile_config_path = scenario_cfg['vnf_options'][self.name]['prox_files']
            proxfile_file = os.path.basename(proxfile_config_path)
            proxfile_config_path = find_relative_file(proxfile_config_path,
                                                      scenario_cfg['task_path'])
            self.remote_proxfile_name = self.copy_to_target(proxfile_config_path, proxfile_file)
            self.additional_file = True
        except:
            self.additional_file = False

        self.prox_config_dict = self.generate_prox_config_file(config_path)

        remote_path = self.upload_prox_config(config_file, self.prox_config_dict)

        self.q_in = multiprocessing.Queue()
        self.q_out = multiprocessing.Queue()
        self.queue_wrapper = QueueFileWrapper(self.q_in, self.q_out, "PROX started")
        self._vnf_process = multiprocessing.Process(target=self._run_prox,
                                                    args=(
                                                        self.queue_wrapper,
                                                        self.mgmt_interface,
                                                        remote_path,
                                                        prox_path,
                                                        prox_args,
                                                    ))
        self._vnf_process.start()

    def wait_for_instantiate(self):
        buf = []
        while True:
            if not self._vnf_process.is_alive():
                raise RuntimeError(
                    "PROX {} process died.".format(self.PROX_MODE))
            while self.q_out.qsize() > 0:
                buf.append(self.q_out.get())
                message = ''.join(buf)
                if "PROX started" in message:
                    LOG.info("PROX %s is up and running.", self.PROX_MODE)
                    self.queue_wrapper.clear()
                    self._sut = self._get_socket()
                    self.resource_helper.start_collect()
                    return self._vnf_process.exitcode
                if "PANIC" in message:
                    raise RuntimeError("Error starting PROX.")
            LOG.info("Waiting for PROX %s to start.. ", self.PROX_MODE)
            time.sleep(self.WAIT_TIME)

    DPDK_STATUS_DRIVER_RE = re.compile(r"(\d{2}:\d{2}\.\d).*drv=(\w+)")

    @staticmethod
    def find_pci(pci, bound_pci):
        # we have to substring match PCI bus address from the end
        return any(b.endswith(pci) for b in bound_pci)

    def find_used_drivers(self, bound_pci, dpdk_status):
        used_drivers = {m[0]: m[1] for m in
                        self.DPDK_STATUS_DRIVER_RE.findall(dpdk_status) if
                        self.find_pci(m[0], bound_pci)}
        return used_drivers

    @staticmethod
    def prox_ip_to_hex(ipaddr):
        return "{0[0]:02x} {0[1]:02x} {0[2]:02x} {0[3]:02x}".format(
            ipaddress.IPv4Address(ipaddr).packed)

    @staticmethod
    def write_prox_config(prox_config):
        """
        Write an .ini-format config file for PROX
        PROX does not allow a space before/after the =, so we need
        a custom method
        """
        out = []
        for section in prox_config:
            out.append("[{}]".format(section))
            for index, item in enumerate(prox_config[section]):
                key, value = item
                if key == "__name__":
                    continue
                if value is not None:
                    key = "=".join((key, str(value).replace('\n', '\n\t')))
                out.append(key)
        return os.linesep.join(out)

    def copy_to_target(self, config_file_path, prox_file):
        remote_path = os.path.join("/tmp", prox_file)
        self.connection.put(config_file_path, remote_path)
        return remote_path

    def upload_prox_config(self, config_file, prox_config_dict):
        # prox can't handle spaces around ' = ' so use custom method
        out = self.write_prox_config(prox_config_dict)
        remote_path = os.path.join("/tmp", config_file)
        self.connection.run("cat > '{}'".format(remote_path), stdin=out)

        return remote_path

    def upload_prox_lua(self, config_dir, prox_config_dict):
        # we could have multiple lua directives
        lua_values = list(prox_config_dict.get('lua', {}).keys())
        if lua_values:
            lua_file = re.findall('\("([^"]+)"\)', lua_values[0])
            out = self.generate_prox_lua_file()
            remote_path = os.path.join(config_dir, lua_file)
            return self.put_string_to_file(out, remote_path)
        return ""

    def put_string_to_file(self, s, remote_path):
        self.connection.run("cat > '{}'".format(remote_path), stdin=s)
        return remote_path

    LUA_PARAMETER_PEER = {
        "gen": "sut",
        "sut": "gen",
    }
    LUA_PARAMETER_NAME = ""

    def generate_prox_lua_file(self):
        p = OrderedDict()
        ext_intf = self.vnfd_helper.interfaces
        lua_param = self.LUA_PARAMETER_NAME
        for intf in ext_intf:
            port_num = intf["virtual-interface"]["dpdk_port_num"]
            peer = self.LUA_PARAMETER_PEER[lua_param]
            p.update({
                "{}_hex_ip_port_{}".format(lua_param, port_num):
                    self.prox_ip_to_hex(intf["local_ip"]),
                "{}_ip_port_{}".format(lua_param, port_num):
                    intf["local_ip"],
                "{}_hex_ip_port_{}".format(peer, port_num):
                    self.prox_ip_to_hex(intf["dst_ip"]),
                "{}_ip_port_{}".format(peer, port_num):
                    intf["dst_ip"],
            })
        lua = os.linesep.join(('{}:"{}"'.format(k, v) for k, v in p.items()))
        return lua

    def generate_prox_config_file(self, config_path):
        sections = {}
        tx_port_no = -1
        prox_config = ConfigParser(config_path, sections)
        prox_config.parse()

        # Ensure MAC is set "hardware"
        ext_intf = self.vnfd_helper.interfaces
        for intf in ext_intf:
            port_num = intf["virtual-interface"]["dpdk_port_num"]
            section = "port {}".format(port_num)
            if section in sections:
                for index, item in enumerate(sections[section]):
                    if item[0] == "mac":
                        sections[section][index][1] = "hardware"

        # search for dest mac
        for section in sections:
            for index, item in enumerate(sections[section]):
                if item[0] == "dst mac":
                    tx_port_no = self._get_tx_port(section, sections)
                    if tx_port_no == -1:
                        raise Exception(
                            "Failed ..destination MAC undefined")
                    else:
                        sections[section][index][1] = \
                            self.vnfd_helper.interfaces[tx_port_no]["virtual-interface"]["dst_mac"]

        # if addition file specified in prox config
        if self.additional_file:
            for section in sections:
                for index, item in enumerate(sections[section]):
                    try:
                        if item[1].startswith("dofile"):
                            new_string = self._replace_filename_with_newname(
                                item[1], self.remote_proxfile_name)
                            sections[section][index][1] = new_string
                    except:
                        pass
        return sections

    def _replace_filename_with_newname(self, old_string, new_filename):
        first_char = old_string.index('"')
        secnd_char = old_string.index('"', first_char + 1)
        new_string = old_string[:first_char + 1] + new_filename + old_string[secnd_char:]
        return new_string

    def _get_tx_port(self, section, sections):
        iface_port = ["-1"]
        for index, item in enumerate(sections[section]):
            if item[0] == "tx port":
                iface = item[1]
                iface_port = re.findall(r'\d+', iface)
        return int(iface_port[0])

    def _get_vpci_to_if_name_map(self):
        return {interface["virtual-interface"]["vpci"]: interface["name"]
                for interface in self.vnfd_helper.interfaces}

    def _get_logical_if_name(self, vpci):
        try:
            return self._vpci_to_if_name_map[vpci]
        except AttributeError:
            self._vpci_to_if_name_map = self._get_vpci_to_if_name_map()
            return self._vpci_to_if_name_map[vpci]

    @staticmethod
    def connect_prox(ip, port):
        """Connect to the prox instance on the remote system"""
        sock = socket.socket()
        sock.connect((ip, port))
        return Prox(sock)

    def _get_socket(self):
        """Run and connect to prox on the remote system """
        # Deallocating a large amout of hugepages takes some time. If a new
        # PROX instance is started immediately after killing the previous one,
        # it might not be able to allocate hugepages, because they are still
        # being freed. Hence the -w switch.
        # self.connection.execute("sudo killall -w Prox 2>/dev/null")
        # prox_cmd = "export TERM=xterm; cd "+ self.bin_path +"; ./Prox -t
        # -f ./handle_none-4.cfg"
        # prox_cmd = "export TERM=xterm; export RTE_SDK=" + self._dpdk_dir +
        #  "; " \
        #    + "export RTE_TARGET=" + self._dpdk_target + ";" \
        #    + " cd " + self._prox_dir + "; make HW_DIRECT_STATS=y -j50;
        # sudo " \
        #    + "./build/Prox " + prox_args
        # log.debug("Starting PROX with command [%s]", prox_cmd)
        # thread.start_new_thread(self.ssh_check_quit, (self, self._user,
        # self._ip, prox_cmd))
        prox_instance = None

        # try connecting to Prox for 60s
        connection_timeout = 60
        while prox_instance is None:
            time.sleep(1)
            connection_timeout -= 1
            try:
                prox_instance = self.connect_prox(self._ip, PROX_PORT)
            except (socket.gaierror, socket.error):
                pass
            if connection_timeout == 0:
                raise Exception(
                    "Failed to connect to prox, please check if system {} "
                    "accepts connections on port {}".format(
                        self._ip, PROX_PORT))
        return prox_instance

    @staticmethod
    def get_cpu_id(cpu_map, core_id, socket_id, is_hyperthread):
        try:
            if is_hyperthread:
                return sorted(cpu_map[socket_id][core_id].values())[1][0]
            else:
                return sorted(cpu_map[socket_id][core_id].values())[0][0]
        except:
            raise Exception(
                "Core {}{} on socket {} does not exist".format(
                    core_id, "h" if is_hyperthread else "", socket_id))

    def get_cpu_topology(self):
        if not self.connection:
            self.connection = ssh.SSH.from_node(self.mgmt_interface)
        self.connection.wait()

        rc, stdout, stderr = self.connection.execute("cat /proc/cpuinfo")
        # { socket: { core: {proc: (socket, core, proc), proc: (socket, core, proc}}
        return parse_cpuinfo(stdout)

    def _resource_collect_start(self):
        pass


class Prox(object):

    def __init__(self, prox_socket):
        """ creates new prox instance """
        self._sock = prox_socket
        # sleep(1)
        # self.put_data("tot ierrors tot\n")
        # recv = self.get_data()
        self._pkt_dumps = []

    def get_socket(self):
        """ get the socket connected to the remote instance """
        return self._sock

    def get_data(self, pkt_dump_only=False, timeout=1):
        """ read data from the socket """
        # This method behaves slightly differently depending on whether it is
        # called to read the response to a command (pkt_dump_only = 0) or if
        # it is called specifically to read a packet dump (pkt_dump_only = 1).
        #
        # Packet dumps look like:
        #   pktdump,<port_id>,<data_len>\n
        #   <packet contents as byte array>\n
        # This means the total packet dump message consists of 2 lines instead
        # of 1 line.
        #
        # - Response for a command (pkt_dump_only = 0):
        #   1) Read response from the socket until \n (end of message)
        #   2a) If the response is a packet dump header (starts with "pktdump,"):
        #     - Read the packet payload and store the packet dump for later
        #       retrieval.
        #     - Reset the state and restart from 1). Eventually state 2b) will
        #       be reached and the function will return.
        #   2b) If the response is not a packet dump:
        #     - Return the received message as a string
        #
        # - Explicit request to read a packet dump (pkt_dump_only = 1):
        #   - Read the dump header and payload
        #   - Store the packet dump for later retrieval
        #   - Return True to signify a packet dump was successfully read
        ret_str = ""
        dat = ""
        done = 0
        while done == 0:
            # recv() is blocking, so avoid calling it when no data is waiting.
            ready = select.select([self._sock], [], [], timeout)
            if ready[0]:
                LOG.debug("Reading from socket")
                dat = self._sock.recv(256).decode('utf-8')
                ret_str = ""
            else:
                LOG.debug("No data waiting on socket")
                done = 1

            i = 0
            while i < len(dat) and (done == 0):
                if dat[i] == '\n':
                    # Terminating \n for a string reply encountered.
                    if ret_str.startswith('pktdump,'):
                        LOG.debug("Packet dump header read: [%s]", ret_str)
                        # The line is a packet dump header. Parse it, read the
                        # packet payload, store the dump for later retrieval.
                        # Skip over the packet dump and continue processing: a
                        # 1-line response may follow the packet dump.
                        _, port_id, data_len = ret_str.split(',', 2)
                        port_id, data_len = int(port_id), int(data_len)

                        data_start = i + 1      # + 1 to skip over \n
                        data_end = data_start + data_len
                        pkt_payload = array.array('B', list(
                            map(ord, dat[data_start:data_end])))
                        pkt_dump = PacketDump(port_id, data_len, pkt_payload)
                        self._pkt_dumps.append(pkt_dump)

                        # Reset state. Increment i with payload length and add
                        # 1 for the trailing \n.
                        ret_str = ""
                        i += data_len + 1

                        if pkt_dump_only:
                            # Return boolean instead of string to signal
                            # successful reception of the packet dump.
                            LOG.debug("Packet dump stored, returning")
                            ret_str = True
                            done = 1
                    else:
                        # Regular 1-line message. Stop reading from the socket.
                        LOG.debug("Regular response read")
                        done = 1
                else:
                    ret_str += dat[i]

                i = i + 1

        LOG.debug("Received data from socket: [%s]", ret_str)
        return ret_str

    def put_data(self, to_send):
        """ send data to the remote intance """
        LOG.debug("Sending data to socket: [%s]", to_send.rstrip('\n'))
        self._sock.sendall(to_send.encode('utf-8'))

    def get_packet_dump(self):
        """ get the next packet dump """
        if len(self._pkt_dumps):
            return self._pkt_dumps.pop(0)
        else:
            return None

    def stop_all_reset(self):
        """ stop the remote instance and reset stats """
        LOG.debug("Stop all and reset stats")
        self.stop_all()
        self.reset_stats()

    def stop_all(self):
        """ stop all cores on the remote instance """
        LOG.debug("Stop all")
        self.put_data("stop all\n")
        time.sleep(3)

    def stop(self, cores, task=-1):
        """ stop specific cores on the remote instace """
        LOG.debug("Stopping cores %s", cores)
        task_string = "" if task == -1 else " {}".format(task)
        self.put_data("stop " + str(cores)[1:-1].replace(" ", "") + task_string + "\n")
        time.sleep(3)

    def start_all(self):
        """ start all cores on the remote instance """
        LOG.debug("Start all")
        self.put_data("start all\n")

    def start(self, cores):
        """ start specific cores on the remote instance """
        LOG.debug("Starting cores %s", cores)
        self.put_data("start " + str(cores)[1:-1].replace(" ", "") + "\n")
        time.sleep(3)

    def reset_stats(self):
        """ reset the statistics on the remote instance """
        LOG.debug("Reset stats")
        self.put_data("reset stats\n")
        time.sleep(1)

    def set_pkt_size(self, cores, pkt_size):
        """ set the packet size to generate on the remote instance """
        LOG.debug("Set packet size for core(s) %s to %d", cores, pkt_size)
        for core in cores:
            self.put_data("pkt_size {} 0 {}\n".format(core, pkt_size - 4))
        time.sleep(1)

    def set_value(self, cores, offset, value, length):
        """ set value on the remote instance """
        LOG.debug(
            "Set value for core(s) %s to '%s' (length %d), offset %d", cores,
            value, length, offset)
        for core in cores:
            self.put_data(
                "set value {} 0 {} {} {}\n".format(core, offset, value,
                                                   length))

    def reset_values(self, cores):
        """ reset values on the remote instance """
        LOG.debug("Set value for core(s) %s", cores)
        for core in cores:
            self.put_data("reset values {} 0\n".format(core))

    def set_speed(self, cores, speed):
        """ set speed on the remote instance """
        LOG.debug("Set speed for core(s) %s to %g", cores, speed)
        for core in cores:
            self.put_data("speed {} 0 {}\n".format(core, speed))

    def slope_speed(self, cores_speed, duration, n_steps=0):
        """will start to increase speed from 0 to N where N is taken from
        a['speed'] for each a in cores_speed"""
        cur_speed = []
        speed_delta = []
        # by default, each step will take 0.5 sec
        if n_steps == 0:
            n_steps = duration * 2

        step_duration = float(duration) / n_steps
        for a in cores_speed:
            speed_delta.append(float(a['speed']) / n_steps)
            cur_speed.append(0)

        cur_step = 0
        while cur_step < n_steps:
            time.sleep(step_duration)
            idx = 0
            for a in cores_speed:
                # for last step to avoid any rounding issues from
                # interpolatin, set speed directly
                if cur_step + 1 == n_steps:
                    cur_speed[idx] = a['speed']
                else:
                    cur_speed[idx] = cur_speed[idx] + speed_delta[idx]

                self.set_speed(a['cores'], cur_speed[idx])
                idx = idx + 1
            cur_step = cur_step + 1

    def set_pps(self, cores, pps, pkt_size):
        """ set packets per second for specific cores on the remote instance """
        LOG.debug(
            "Set packets per sec for core(s) %s to %g%% of line rate (packet size: %d)",
            cores, pps, pkt_size)
        # speed in percent of line-rate
        speed = float(pps) / (1250000000 / (pkt_size + 20))
        for core in cores:
            self.put_data("speed {} 0 {}\n".format(core, speed))

    def lat_stats(self, cores, task=0):
        """Get the latency statistics from the remote system"""
        # 1-based index, if max core is 4, then 0, 1, 2, 3, 4  len = 5
        lat_min = {}
        lat_max = {}
        lat_avg = {}
        for core in cores:
            self.put_data("lat stats {} {} \n".format(core, task))
            ret = self.get_data()
            if ret:
                ret = ret.split(",")
                if len(ret) >= 3:
                    lat_min[core] = int(ret[0])
                    lat_max[core] = int(ret[1])
                    lat_avg[core] = int(ret[2])
        return lat_min, lat_max, lat_avg

    def hz(self):
        self.put_data("tot stats\n")
        recv = self.get_data()
        hz = int(recv.split(",")[3])
        return hz

    # Deprecated
    def rx_stats(self, cores, task=0):
        return self.core_stats(cores, task)

    def core_stats(self, cores, task=0):
        """Get the receive statistics from the remote system"""
        rx = tx = drop = tsc = 0
        for core in cores:
            self.put_data("core stats {} {}\n".format(core, task))
            ret = self.get_data().split(",")
            rx += int(ret[0])
            tx += int(ret[1])
            drop += int(ret[2])
            tsc = int(ret[3])
        return rx, tx, drop, tsc

    def port_stats(self, ports):
        """get counter values from a specific port"""
        tot_result = [0] * 12
        for port in ports:
            self.put_data("port_stats {}\n".format(port))
            ret = list(map(int, self.get_data().split(",")))
            tot_result = list(map(sum, list(zip(tot_result, ret))))
        return tot_result

    def tot_stats(self):
        """Get the total statistics from the remote system"""
        self.put_data("tot stats\n")
        # tot_rx, tot_tx, tsc, hz
        ints = [int(x) for x in self.get_data().split(",")]
        return ints[:3]

    def tot_ierrors(self):
        """Get the total ierrors from the remote system"""
        self.put_data("tot ierrors tot\n")
        recv = self.get_data()
        tot_ierrors = int(recv.split(",")[0])
        tsc = int(recv.split(",")[0])
        return tot_ierrors, tsc

    def set_count(self, count, cores):
        """Set the number of packets to send on the specified core"""
        for core in cores:
            self.put_data("count {} 0 {}\n".format(core, count))

    def dump_rx(self, core_id, task_id=0, count=1):
        """Activate dump on rx on the specified core"""
        LOG.debug("Activating dump on RX for core %d, task %d, count %d", core_id, task_id, count)
        self.put_data("dump_rx {} {} {}\n".format(core_id, task_id, count))
        time.sleep(1.5)     # Give PROX time to set up packet dumping

    def quit(self):
        """ stop all cores on the remote instance """
        LOG.debug("Quit prox")
        self.put_data("quit\n")
        time.sleep(3)

    def force_quit(self):
        """ stop all cores on the remote instance """
        LOG.debug("Force Quit prox")
        self.put_data("quit_force\n")
        time.sleep(3)


class PacketDump(object):
    def __init__(self, port_id, data_len, payload):
        assert len(payload) == data_len, \
            "Packet dump has specified length {}, but payload is {} bytes long".format(
                data_len, len(payload))

        self._port_id = port_id
        self._data_len = data_len
        self._payload = payload

    def port_id(self):
        """Get the port id of the packet dump"""
        return self._port_id

    def data_len(self):
        """Get the length of the data received"""
        return self._data_len

    def payload(self, start=None, end=None):
        """Get part of the payload as a list of ordinals.

        Returns a list of byte values, matching the contents of the packet dump.
        Optional start and end parameters can be specified to retrieve only a
        part of the packet contents.

        The number of elements in the list is equal to end - start + 1, so end
        is the offset of the last character.

        Args:
            start (pos. int): the starting offset in the payload. If it is not
                specified or None, offset 0 is assumed.
            end (pos. int): the ending offset of the payload. If it is not
                specified or None, the contents until the end of the packet are
                returned.

        Returns:
            [int, int, ...]. Each int represents the ordinal value of a byte in
            the packet payload.
        """
        if start is None:
            start = 0

        if end is None:
            end = self._data_len - 1

        # Bounds checking on offsets
        assert start >= 0, "Start offset must be non-negative"
        assert end < self._data_len, "End offset must be less than {}".format(
            self._data_len)

        # Adjust for splice operation: end offset must be 1 more than the offset
        # of the last desired character.
        end += 1

        return self._payload[start:end]
