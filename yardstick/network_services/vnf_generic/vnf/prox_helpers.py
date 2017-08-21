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
import operator
import logging
import os
import re
import select
import socket
from collections import OrderedDict, namedtuple
import time
from contextlib import contextmanager
from itertools import repeat, chain

from six.moves import zip, StringIO

from yardstick.benchmark.scenarios.networking.vnf_generic import find_relative_file
from yardstick.common.utils import SocketTopology, ip_to_hex, join_non_strings
from yardstick.network_services.vnf_generic.vnf.iniparser import ConfigParser
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import DpdkVnfSetupEnvHelper

PROX_PORT = 8474

LOG = logging.getLogger(__name__)

TEN_GIGABIT = 1e10
BITS_PER_BYTE = 8
RETRY_SECONDS = 60
RETRY_INTERVAL = 1

CONFIGURATION_OPTIONS = (
    # dict key           section     key               default value
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


class CoreSocketTuple(namedtuple('CoreTuple', 'core_id, socket_id, hyperthread')):

    CORE_RE = re.compile(r"core\s+(\d+)(?:s(\d+))?(h)?")

    def __new__(cls, *args):
        try:
            matches = cls.CORE_RE.search(str(args[0]))
            if matches:
                args = matches.groups()

            return super(CoreSocketTuple, cls).__new__(cls, int(args[0]), int(args[1]),
                                                       'h' if args[2] else '')

        except (AttributeError, TypeError, IndexError, ValueError):
            raise ValueError('Invalid core spec {}'.format(args))

    def is_hyperthread(self):
        return self.hyperthread == 'h'

    @property
    def index(self):
        return int(self.is_hyperthread())

    def find_in_topology(self, cpu_topology):
        try:
            socket_core_match = cpu_topology[self.socket_id][self.core_id]
            sorted_match = sorted(socket_core_match.values())
            return sorted_match[self.index][0]
        except (KeyError, IndexError):
            template = "Core {}{} on socket {} does not exist"
            raise ValueError(template.format(self.core_id, self.hyperthread, self.socket_id))


class TotStatsTuple(namedtuple('TotStats', 'rx,tx,tsc,hz')):

    def __new__(cls, *args):
        try:
            assert args[0] is not str(args[0])
            args = tuple(args[0])
        except (AssertionError, IndexError, TypeError):
            pass

        return super(TotStatsTuple, cls).__new__(cls, *args)


class ProxTestDataTuple(namedtuple('ProxTestDataTuple', 'tolerated,tsc_hz,delta_rx,'
                                                        'delta_tx,delta_tsc,'
                                                        'latency,rx_total,tx_total,pps')):

    @property
    def pkt_loss(self):
        try:
            return 1e2 * self.drop_total / float(self.tx_total)
        except ZeroDivisionError:
            return 100.0

    @property
    def mpps(self):
        # calculate the effective throughput in Mpps
        return float(self.delta_tx) * self.tsc_hz / self.delta_tsc / 1e6

    @property
    def can_be_lost(self):
        return int(self.tx_total * self.tolerated / 1e2)

    @property
    def drop_total(self):
        return self.tx_total - self.rx_total

    @property
    def success(self):
        return self.drop_total <= self.can_be_lost

    def get_samples(self, pkt_size, pkt_loss=None):
        if pkt_loss is None:
            pkt_loss = self.pkt_loss

        latency_keys = [
            "LatencyMin",
            "LatencyMax",
            "LatencyAvg",
        ]

        samples = {
            "Throughput": self.mpps,
            "DropPackets": pkt_loss,
            "CurrentDropPackets": pkt_loss,
            "TxThroughput": self.pps / 1e6,
            "RxThroughput": self.mpps,
            "PktSize": pkt_size,
        }

        samples.update((key, value) for key, value in zip(latency_keys, self.latency))
        return samples

    def log_data(self, logger=None):
        if logger is None:
            logger = LOG

        template = "RX: %d; TX: %d; dropped: %d (tolerated: %d)"
        logger.debug(template, self.rx_total, self.tx_total, self.drop_total, self.can_be_lost)
        logger.debug("Mpps configured: %f; Mpps effective %f", self.pps / 1e6, self.mpps)


class PacketDump(object):

    @staticmethod
    def assert_func(func, value1, value2, template=None):
        assert func(value1, value2), template.format(value1, value2)

    def __init__(self, port_id, data_len, payload):
        template = "Packet dump has specified length {}, but payload is {} bytes long"
        self.assert_func(operator.eq, data_len, len(payload), template)
        self._port_id = port_id
        self._data_len = data_len
        self._payload = payload

    @property
    def port_id(self):
        """Get the port id of the packet dump"""
        return self._port_id

    @property
    def data_len(self):
        """Get the length of the data received"""
        return self._data_len

    def __str__(self):
        return '<PacketDump port: {} payload: {}>'.format(self._port_id, self._payload)

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
            end = self.data_len - 1

        # Bounds checking on offsets
        template = "Start offset must be non-negative"
        self.assert_func(operator.ge, start, 0, template)

        template = "End offset must be less than {1}"
        self.assert_func(operator.lt, end, self.data_len, template)

        # Adjust for splice operation: end offset must be 1 more than the offset
        # of the last desired character.
        end += 1

        return self._payload[start:end]


class ProxSocketHelper(object):

    def __init__(self, sock=None):
        """ creates new prox instance """
        super(ProxSocketHelper, self).__init__()

        if sock is None:
            sock = socket.socket()

        self._sock = sock
        self._pkt_dumps = []

    def connect(self, ip, port):
        """Connect to the prox instance on the remote system"""
        self._sock.connect((ip, port))

    def get_socket(self):
        """ get the socket connected to the remote instance """
        return self._sock

    def _parse_socket_data(self, decoded_data, pkt_dump_only):
        def get_newline_index():
            return decoded_data.find('\n', index)

        ret_str = ''
        index = 0
        for newline_index in iter(get_newline_index, -1):
            ret_str = decoded_data[index:newline_index]

            try:
                mode, port_id, data_len = ret_str.split(',', 2)
            except ValueError:
                mode, port_id, data_len = None, None, None

            if mode != 'pktdump':
                # Regular 1-line message. Stop reading from the socket.
                LOG.debug("Regular response read")
                return ret_str

            LOG.debug("Packet dump header read: [%s]", ret_str)

            # The line is a packet dump header. Parse it, read the
            # packet payload, store the dump for later retrieval.
            # Skip over the packet dump and continue processing: a
            # 1-line response may follow the packet dump.

            data_len = int(data_len)
            data_start = newline_index + 1  # + 1 to skip over \n
            data_end = data_start + data_len
            sub_data = decoded_data[data_start:data_end]
            pkt_payload = array.array('B', (ord(v) for v in sub_data))
            pkt_dump = PacketDump(int(port_id), data_len, pkt_payload)
            self._pkt_dumps.append(pkt_dump)

            if pkt_dump_only:
                # Return boolean instead of string to signal
                # successful reception of the packet dump.
                LOG.debug("Packet dump stored, returning")
                return True

            index = data_end + 1

        return ret_str

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

        def is_ready():
            # recv() is blocking, so avoid calling it when no data is waiting.
            ready = select.select([self._sock], [], [], timeout)
            return bool(ready[0])

        status = False
        ret_str = ""
        for status in iter(is_ready, False):
            LOG.debug("Reading from socket")
            decoded_data = self._sock.recv(256).decode('utf-8')
            ret_str = self._parse_socket_data(decoded_data, pkt_dump_only)

        LOG.debug("Received data from socket: [%s]", ret_str)
        return ret_str if status else ''

    def put_command(self, to_send):
        """ send data to the remote instance """
        LOG.debug("Sending data to socket: [%s]", to_send.rstrip('\n'))
        self._sock.sendall(to_send.encode('utf-8'))

    def get_packet_dump(self):
        """ get the next packet dump """
        if self._pkt_dumps:
            return self._pkt_dumps.pop(0)
        return None

    def stop_all_reset(self):
        """ stop the remote instance and reset stats """
        LOG.debug("Stop all and reset stats")
        self.stop_all()
        self.reset_stats()

    def stop_all(self):
        """ stop all cores on the remote instance """
        LOG.debug("Stop all")
        self.put_command("stop all\n")
        time.sleep(3)

    def stop(self, cores, task=''):
        """ stop specific cores on the remote instance """
        LOG.debug("Stopping cores %s", cores)
        self.put_command("stop {} {}\n".format(join_non_strings(',', cores), task))
        time.sleep(3)

    def start_all(self):
        """ start all cores on the remote instance """
        LOG.debug("Start all")
        self.put_command("start all\n")

    def start(self, cores):
        """ start specific cores on the remote instance """
        LOG.debug("Starting cores %s", cores)
        self.put_command("start {}\n".format(join_non_strings(',', cores)))
        time.sleep(3)

    def reset_stats(self):
        """ reset the statistics on the remote instance """
        LOG.debug("Reset stats")
        self.put_command("reset stats\n")
        time.sleep(1)

    def _run_template_over_cores(self, template, cores, *args):
        for core in cores:
            self.put_command(template.format(core, *args))

    def set_pkt_size(self, cores, pkt_size):
        """ set the packet size to generate on the remote instance """
        LOG.debug("Set packet size for core(s) %s to %d", cores, pkt_size)
        pkt_size -= 4
        self._run_template_over_cores("pkt_size {} 0 {}\n", cores, pkt_size)
        time.sleep(1)

    def set_value(self, cores, offset, value, length):
        """ set value on the remote instance """
        msg = "Set value for core(s) %s to '%s' (length %d), offset %d"
        LOG.debug(msg, cores, value, length, offset)
        template = "set value {} 0 {} {} {}\n"
        self._run_template_over_cores(template, cores, offset, value, length)

    def reset_values(self, cores):
        """ reset values on the remote instance """
        LOG.debug("Set value for core(s) %s", cores)
        self._run_template_over_cores("reset values {} 0\n", cores)

    def set_speed(self, cores, speed):
        """ set speed on the remote instance """
        LOG.debug("Set speed for core(s) %s to %g", cores, speed)
        self._run_template_over_cores("speed {} 0 {}\n", cores, speed)

    def slope_speed(self, cores_speed, duration, n_steps=0):
        """will start to increase speed from 0 to N where N is taken from
        a['speed'] for each a in cores_speed"""
        # by default, each step will take 0.5 sec
        if n_steps == 0:
            n_steps = duration * 2

        private_core_data = []
        step_duration = float(duration) / n_steps
        for core_data in cores_speed:
            target = float(core_data['speed'])
            private_core_data.append({
                'cores': core_data['cores'],
                'zero': 0,
                'delta': target / n_steps,
                'current': 0,
                'speed': target,
            })

        deltas_keys_iter = repeat(('current', 'delta'), n_steps - 1)
        for key1, key2 in chain(deltas_keys_iter, [('zero', 'speed')]):
            time.sleep(step_duration)
            for core_data in private_core_data:
                core_data['current'] = core_data[key1] + core_data[key2]
                self.set_speed(core_data['cores'], core_data['current'])

    def set_pps(self, cores, pps, pkt_size):
        """ set packets per second for specific cores on the remote instance """
        msg = "Set packets per sec for core(s) %s to %g%% of line rate (packet size: %d)"
        LOG.debug(msg, cores, pps, pkt_size)

        # speed in percent of line-rate
        speed = float(pps) * (pkt_size + 20) / TEN_GIGABIT / BITS_PER_BYTE
        self._run_template_over_cores("speed {} 0 {}\n", cores, speed)

    def lat_stats(self, cores, task=0):
        """Get the latency statistics from the remote system"""
        # 1-based index, if max core is 4, then 0, 1, 2, 3, 4  len = 5
        lat_min = {}
        lat_max = {}
        lat_avg = {}
        for core in cores:
            self.put_command("lat stats {} {} \n".format(core, task))
            ret = self.get_data()

            try:
                lat_min[core], lat_max[core], lat_avg[core] = \
                    tuple(int(n) for n in ret.split(",")[:3])

            except (AttributeError, ValueError, TypeError):
                pass

        return lat_min, lat_max, lat_avg

    def get_all_tot_stats(self):
        self.put_command("tot stats\n")
        all_stats = TotStatsTuple(int(v) for v in self.get_data().split(","))
        return all_stats

    def hz(self):
        return self.get_all_tot_stats().hz

    # Deprecated
    # TODO: remove
    def rx_stats(self, cores, task=0):
        return self.core_stats(cores, task)

    def core_stats(self, cores, task=0):
        """Get the receive statistics from the remote system"""
        rx = tx = drop = tsc = 0
        for core in cores:
            self.put_command("core stats {} {}\n".format(core, task))
            ret = self.get_data().split(",")
            rx += int(ret[0])
            tx += int(ret[1])
            drop += int(ret[2])
            tsc = int(ret[3])
        return rx, tx, drop, tsc

    def port_stats(self, ports):
        """get counter values from a specific port"""
        tot_result = list(repeat(0, 12))
        for port in ports:
            self.put_command("port_stats {}\n".format(port))
            for index, n in enumerate(self.get_data().split(',')):
                tot_result[index] += int(n)
        return tot_result

    @contextmanager
    def measure_tot_stats(self):
        start = self.get_all_tot_stats()
        container = {'start_tot': start}
        try:
            yield container
        finally:
            container['end_tot'] = end = self.get_all_tot_stats()

        container['delta'] = TotStatsTuple(end - start for start, end in zip(start, end))

    def tot_stats(self):
        """Get the total statistics from the remote system"""
        stats = self.get_all_tot_stats()
        return stats[:3]

    def tot_ierrors(self):
        """Get the total ierrors from the remote system"""
        self.put_command("tot ierrors tot\n")
        recv = self.get_data().split(',')
        tot_ierrors = int(recv[0])
        tsc = int(recv[0])
        return tot_ierrors, tsc

    def set_count(self, count, cores):
        """Set the number of packets to send on the specified core"""
        self._run_template_over_cores("count {} 0 {}\n", cores, count)

    def dump_rx(self, core_id, task_id=0, count=1):
        """Activate dump on rx on the specified core"""
        LOG.debug("Activating dump on RX for core %d, task %d, count %d", core_id, task_id, count)
        self.put_command("dump_rx {} {} {}\n".format(core_id, task_id, count))
        time.sleep(1.5)     # Give PROX time to set up packet dumping

    def quit(self):
        self.stop_all()
        self._quit()
        self.force_quit()

    def _quit(self):
        """ stop all cores on the remote instance """
        LOG.debug("Quit prox")
        self.put_command("quit\n")
        time.sleep(3)

    def force_quit(self):
        """ stop all cores on the remote instance """
        LOG.debug("Force Quit prox")
        self.put_command("quit_force\n")
        time.sleep(3)


class ProxDpdkVnfSetupEnvHelper(DpdkVnfSetupEnvHelper):

    def __init__(self, vnfd_helper, ssh_helper, scenario_helper):
        super(ProxDpdkVnfSetupEnvHelper, self).__init__(vnfd_helper, ssh_helper, scenario_helper)
        self.dpdk_root = "/root/dpdk-17.02"

    def setup_vnf_environment(self):
        super(ProxDpdkVnfSetupEnvHelper, self).setup_vnf_environment()

        # debug dump after binding
        self.ssh_helper.execute("sudo {} -s".format(self.dpdk_nic_bind))

    def rebind_drivers(self, force=True):
        if force:
            force = '--force '
        else:
            force = ''
        cmd_template = "{} {}-b {} {}"
        if not self.used_drivers:
            self._find_used_drivers()
        for vpci, (_, driver) in self.used_drivers.items():
            self.ssh_helper.execute(cmd_template.format(self.dpdk_nic_bind, force, driver, vpci))

    def _setup_dpdk(self):
        self._setup_hugepages()

        self.ssh_helper.execute("pkill prox")
        self.ssh_helper.execute("sudo modprobe uio")

        # for baremetal
        self.ssh_helper.execute("sudo modprobe msr")

        # why remove?, just keep it loaded
        # self.connection.execute("sudo rmmod igb_uio")

        igb_uio_path = os.path.join(self.dpdk_root, "x86_64-native-linuxapp-gcc/kmod/igb_uio.ko")
        self.ssh_helper.execute("sudo insmod {}".format(igb_uio_path))

        # quick hack to allow non-root copy
        self.ssh_helper.execute("sudo chmod 0777 {}".format(self.ssh_helper.bin_path))


class ProxResourceHelper(ClientResourceHelper):

    PROX_CORE_GEN_MODE = "gen"
    PROX_CORE_LAT_MODE = "lat"

    PROX_MODE = ""

    LUA_PARAMETER_NAME = ""
    LUA_PARAMETER_PEER = {
        "gen": "sut",
        "sut": "gen",
    }

    WAIT_TIME = 3

    @staticmethod
    def _replace_quoted_with_value(quoted, value, count=1):
        new_string = re.sub('"[^"]*"', '"{}"'.format(value), quoted, count)
        return new_string

    @staticmethod
    def _get_tx_port(section, sections):
        iface_port = [-1]
        for item in sections[section]:
            if item[0] == "tx port":
                iface_port = re.findall(r'\d+', item[1])
                # do we want the last one?
                #   if yes, then can we reverse?
        return int(iface_port[0])

    @staticmethod
    def line_rate_to_pps(pkt_size, n_ports):
        # FIXME Don't hardcode 10Gb/s
        return n_ports * TEN_GIGABIT / BITS_PER_BYTE / (pkt_size + 20)

    @staticmethod
    def find_pci(pci, bound_pci):
        # we have to substring match PCI bus address from the end
        return any(b.endswith(pci) for b in bound_pci)

    @staticmethod
    def write_prox_config(prox_config):
        """
        Write an .ini-format config file for PROX
        PROX does not allow a space before/after the =, so we need
        a custom method
        """
        out = []
        for section_name, section_value in prox_config.items():
            out.append("[{}]".format(section_name))
            for key, value in section_value:
                if key == "__name__":
                    continue
                if value is not None:
                    key = "=".join((key, str(value).replace('\n', '\n\t')))
                out.append(key)
        return os.linesep.join(out)

    def __init__(self, setup_helper):
        super(ProxResourceHelper, self).__init__(setup_helper)
        self.mgmt_interface = self.vnfd_helper.mgmt_interface
        self._user = self.mgmt_interface["user"]
        self._ip = self.mgmt_interface["ip"]

        self.done = False
        self._cpu_topology = None
        self._vpci_to_if_name_map = None
        self.additional_file = False
        self.remote_prox_file_name = None
        self.prox_config_dict = None
        self.lower = None
        self.upper = None
        self._test_cores = None
        self._latency_cores = None

    @property
    def sut(self):
        if not self.client:
            self.client = ProxSocketHelper()
        return self.client

    @property
    def cpu_topology(self):
        if not self._cpu_topology:
            stdout = self.ssh_helper.execute("cat /proc/cpuinfo")[1]
            self._cpu_topology = SocketTopology.parse_cpuinfo(stdout)
        return self._cpu_topology

    @property
    def vpci_to_if_name_map(self):
        if self._vpci_to_if_name_map is None:
            self._vpci_to_if_name_map = {
                interface["virtual-interface"]["vpci"]: interface["name"]
                for interface in self.vnfd_helper.interfaces
            }
        return self._vpci_to_if_name_map

    @property
    def test_cores(self):
        if not self._test_cores:
            self._test_cores = self.get_cores(self.PROX_CORE_GEN_MODE)
        return self._test_cores

    @property
    def latency_cores(self):
        if not self._latency_cores:
            self._latency_cores = self.get_cores(self.PROX_CORE_LAT_MODE)
        return self._latency_cores

    def run_traffic(self, traffic_profile):
        self.lower = 0.0
        self.upper = 100.0

        traffic_profile.init(self._queue)
        # this frees up the run_traffic loop
        self.client_started.value = 1

        while not self._terminated.value:
            # move it all to traffic_profile
            self._run_traffic_once(traffic_profile)

    def _run_traffic_once(self, traffic_profile):
        traffic_profile.execute(self)
        if traffic_profile.done:
            self._queue.put({'done': True})
            LOG.debug("tg_prox done")
            self._terminated.value = 1

    def start_collect(self):
        pass

    def terminate(self):
        super(ProxResourceHelper, self).terminate()
        self.ssh_helper.execute('sudo pkill prox')
        self.setup_helper.rebind_drivers()

    def get_process_args(self):
        task_path = self.scenario_helper.task_path
        options = self.scenario_helper.options

        prox_args = options['prox_args']
        prox_path = options['prox_path']
        config_path = options['prox_config']

        config_file = os.path.basename(config_path)
        config_path = find_relative_file(config_path, task_path)

        try:
            prox_file_config_path = options['prox_files']
            prox_file_file = os.path.basename(prox_file_config_path)
            prox_file_config_path = find_relative_file(prox_file_config_path, task_path)
            self.remote_prox_file_name = self.copy_to_target(prox_file_config_path, prox_file_file)
            self.additional_file = True
        except:
            self.additional_file = False

        self.prox_config_dict = self.generate_prox_config_file(config_path)

        remote_path = self.upload_prox_config(config_file, self.prox_config_dict)
        return prox_args, prox_path, remote_path

    def up_post(self):
        return self.sut  # force connection

    def execute(self, cmd, *args, **kwargs):
        func = getattr(self.sut, cmd, None)
        if func:
            return func(*args, **kwargs)

    def copy_to_target(self, config_file_path, prox_file):
        remote_path = os.path.join("/tmp", prox_file)
        self.ssh_helper.put(config_file_path, remote_path)
        return remote_path

    def upload_prox_config(self, config_file, prox_config_dict):
        # prox can't handle spaces around ' = ' so use custom method
        out = StringIO(self.write_prox_config(prox_config_dict))
        out.seek(0)
        remote_path = os.path.join("/tmp", config_file)
        self.ssh_helper.put_file_obj(out, remote_path)

        return remote_path

    @contextmanager
    def traffic_context(self, pkt_size, value):
        self.sut.stop_all()
        self.sut.reset_stats()
        self.sut.set_pkt_size(self.test_cores, pkt_size)
        self.sut.set_speed(self.test_cores, value)
        self.sut.start_all()
        try:
            yield
        finally:
            self.sut.stop_all()

    def run_test(self, pkt_size, duration, value, tolerated_loss=0.0):
        # do this assert in init?  unless we expect interface count to
        # change from one run to another run...
        interfaces = self.vnfd_helper.interfaces
        interface_count = len(interfaces)
        assert interface_count in {2, 4}, \
            "Invalid no of ports, 2 or 4 ports only supported at this time"

        with self.traffic_context(pkt_size, value):
            # Getting statistics to calculate PPS at right speed....
            tsc_hz = float(self.sut.hz())
            time.sleep(2)
            with self.sut.measure_tot_stats() as data:
                time.sleep(duration)

            # Get stats before stopping the cores. Stopping cores takes some time
            # and might skew results otherwise.
            latency = self.get_latency()

        deltas = data['delta']
        rx_total, tx_total = self.sut.port_stats(range(interface_count))[6:8]
        pps = value / 100.0 * self.line_rate_to_pps(pkt_size, interface_count)

        result = ProxTestDataTuple(tolerated_loss, tsc_hz, deltas.rx, deltas.tx,
                                   deltas.tsc, latency, rx_total, tx_total, pps)

        result.log_data()
        return result

    def get_cores(self, mode):
        cores = []
        for section_name, section_data in self.prox_config_dict.items():
            if section_name.startswith("core"):
                for index, item in enumerate(section_data):
                    if item[0] == "mode" and item[1] == mode:
                        core = CoreSocketTuple(section_name).find_in_topology(self.cpu_topology)
                        cores.append(core)
        return cores

    def upload_prox_lua(self, config_dir, prox_config_dict):
        # we could have multiple lua directives
        lau_dict = prox_config_dict.get('lua', {})
        find_iter = (re.findall('\("([^"]+)"\)', k) for k in lau_dict)
        lua_file = next((found[0] for found in find_iter if found), None)
        if not lua_file:
            return ""

        out = self.generate_prox_lua_file()
        remote_path = os.path.join(config_dir, lua_file)
        return self.put_string_to_file(out, remote_path)

    def put_string_to_file(self, s, remote_path):
        self.ssh_helper.run("cat > '{}'".format(remote_path), stdin=s)
        return remote_path

    def generate_prox_lua_file(self):
        p = OrderedDict()
        ext_intf = self.vnfd_helper.interfaces
        lua_param = self.LUA_PARAMETER_NAME
        for intf in ext_intf:
            peer = self.LUA_PARAMETER_PEER[lua_param]
            port_num = intf["virtual-interface"]["dpdk_port_num"]
            local_ip = intf["local_ip"]
            dst_ip = intf["dst_ip"]
            local_ip_hex = ip_to_hex(local_ip, separator=' ')
            dst_ip_hex = ip_to_hex(dst_ip, separator=' ')
            p.update([
                ("{}_hex_ip_port_{}".format(lua_param, port_num), local_ip_hex),
                ("{}_ip_port_{}".format(lua_param, port_num), local_ip),
                ("{}_hex_ip_port_{}".format(peer, port_num), dst_ip_hex),
                ("{}_ip_port_{}".format(peer, port_num), dst_ip),
            ])
        lua = os.linesep.join(('{}:"{}"'.format(k, v) for k, v in p.items()))
        return lua

    def generate_prox_config_file(self, config_path):
        sections = {}
        prox_config = ConfigParser(config_path, sections)
        prox_config.parse()

        # Ensure MAC is set "hardware"
        ext_intf = self.vnfd_helper.interfaces
        for intf in ext_intf:
            port_num = intf["virtual-interface"]["dpdk_port_num"]
            section_name = "port {}".format(port_num)
            for index, section_data in enumerate(sections.get(section_name, [])):
                if section_data[0] == "mac":
                    sections[section_name][index][1] = "hardware"

        # search for dest mac
        for section_name, section_data in sections.items():
            for index, section_attr in enumerate(section_data):
                if section_attr[0] != "dst mac":
                    continue

                tx_port_no = self._get_tx_port(section_name, sections)
                if tx_port_no == -1:
                    raise Exception("Failed ..destination MAC undefined")

                dst_mac = ext_intf[tx_port_no]["virtual-interface"]["dst_mac"]
                section_attr[1] = dst_mac

        # if addition file specified in prox config
        if self.additional_file:
            remote_name = self.remote_prox_file_name
            for section_data in sections.values():
                for index, section_attr in enumerate(section_data):
                    try:
                        if section_attr[1].startswith("dofile"):
                            new_string = self._replace_quoted_with_value(section_attr[1],
                                                                         remote_name)
                            section_attr[1] = new_string
                    except:
                        pass

        return sections

    def get_latency(self):
        """
        :return: return lat_min, lat_max, lat_avg
        :rtype: list
        """
        if self._latency_cores:
            return self.sut.lat_stats(self._latency_cores)
        return []

    def _get_logical_if_name(self, vpci):
        return self._vpci_to_if_name_map[vpci]

    def _connect(self, client=None):
        """Run and connect to prox on the remote system """
        # De-allocating a large amount of hugepages takes some time. If a new
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
        if client is None:
            client = ProxSocketHelper()

        # try connecting to Prox for 60s
        for _ in range(RETRY_SECONDS):
            time.sleep(RETRY_INTERVAL)
            try:
                client.connect(self._ip, PROX_PORT)
            except (socket.gaierror, socket.error):
                continue
            else:
                return client

        msg = "Failed to connect to prox, please check if system {} accepts connections on port {}"
        raise Exception(msg.format(self._ip, PROX_PORT))
