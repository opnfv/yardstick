# Copyright 2016-2017 Red Hat Inc & Xena Networks.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This is a port of code by Xena and Flavios ported to python 3 compatibility.
# Credit given to Xena and Flavio for providing most of the logic of this code.
# The code has changes for PEP 8 and python 3 conversion. Added Stat classes
# for better scaling of future requirements. Also added calculation functions
# for line rate to align within VSPerf project.
# Flavios xena libraries available at https://github.com/fleitner/XenaPythonLib

# Contributors:
#   Flavio Leitner, Red Hat Inc.
#   Dan Amzulescu, Xena Networks
#   Christian Trautman, Red Hat Inc.

"""
Xena Socket API Driver module for communicating directly with Xena system
through socket commands and returning different statistics.
"""
import locale
import logging
import socket
import struct
import sys
import threading
import time
# pylint: disable=too-many-lines
# Xena Socket Commands
CMD_CLEAR_RX_STATS = 'pr_clear'
CMD_CLEAR_TX_STATS = 'pt_clear'
CMD_COMMENT = ';'
CMD_CREATE_STREAM = 'ps_create'
CMD_DELETE_STREAM = 'ps_delete'
CMD_GET_PORT_SPEED = 'p_speed ?'
CMD_GET_PORT_SPEED_REDUCTION = 'p_speedreduction ?'
CMD_GET_RX_STATS_PER_TID = 'pr_tpldtraffic'
CMD_GET_STREAM_DATA = 'pt_stream'
CMD_GET_STREAMS_PER_PORT = 'ps_indices'
CMD_GET_TID_PER_STREAM = 'ps_tpldid'
CMD_GET_TX_STATS_PER_STREAM = 'pt_stream'
CMD_GET_RX_STATS = 'pr_all ?'
CMD_GET_TX_STATS = 'pt_all ?'
CMD_INTERFRAME_GAP = 'p_interframegap'
CMD_LOGIN = 'c_logon'
CMD_LOGOFF = 'c_logoff'
CMD_OWNER = 'c_owner'
CMD_PORT = ';Port:'
CMD_PORT_IP = 'p_ipaddress'
CMD_PORT_LEARNING = 'p_autotrain'
CMD_RESERVE = 'p_reservation reserve'
CMD_RELEASE = 'p_reservation release'
CMD_RELINQUISH = 'p_reservation relinquish'
CMD_RESET = 'p_reset'
CMD_SET_PORT_ARP_REPLY = 'p_arpreply'
CMD_SET_PORT_ARP_V6_REPLY = 'p_arpv6reply'
CMD_SET_PORT_PING_REPLY = 'p_pingreply'
CMD_SET_PORT_PING_V6_REPLY = 'p_pingv6reply'
CMD_SET_PORT_TIME_LIMIT = 'p_txtimelimit'
CMD_SET_STREAM_HEADER_PROTOCOL = 'ps_headerprotocol'
CMD_SET_STREAM_ON_OFF = 'ps_enable'
CMD_SET_STREAM_PACKET_HEADER = 'ps_packetheader'
CMD_SET_STREAM_PACKET_LENGTH = 'ps_packetlength'
CMD_SET_STREAM_PACKET_LIMIT = 'ps_packetlimit'
CMD_SET_STREAM_PACKET_PAYLOAD = 'ps_payload'
CMD_SET_STREAM_RATE_FRACTION = 'ps_ratefraction'
CMD_SET_STREAM_TEST_PAYLOAD_ID = 'ps_tpldid'
CMD_SET_TPLD_MODE = 'p_tpldmode'
CMD_START_TRAFFIC = 'p_traffic on'
CMD_STOP_TRAFFIC = 'p_traffic off'
CMD_STREAM_MODIFIER = 'ps_modifier'
CMD_STREAM_MODIFIER_COUNT = 'ps_modifiercount'
CMD_STREAM_MODIFIER_RANGE = 'ps_modifierrange'
CMD_VERSION = 'c_versionno ?'

_LOCALE = locale.getlocale()[1]
_LOGGER = logging.getLogger(__name__)


class SimpleSocket(object):
    """
    Socket class
    """
    def __init__(self, hostname, port=5025, timeout=1):
        """Constructor
        :param hostname: hostname or ip as string
        :param port: port number to use for socket as int
        :param timeout: socket timeout as int
        :return: SimpleSocket object
        """
        self.hostname = hostname
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect((hostname, port))
        except socket.error as msg:
            _LOGGER.error(
                "Cannot connect to Xena Socket at %s", hostname)
            _LOGGER.error("Exception : %s", msg)
            sys.exit(1)

    def __del__(self):
        """Deconstructor
        :return:
        """
        self.sock.close()

    def ask(self, cmd):
        """ Send the command over the socket
        :param cmd: cmd as string
        :return: byte utf encoded return value from socket
        """
        cmd += '\n'
        try:
            self.sock.send(cmd.encode('utf-8'))
            return self.sock.recv(1024)
        except OSError:
            return ''

    def read_reply(self):
        """ Get the response from the socket
        :return: Return the reply
        """
        reply = self.sock.recv(1024)
        if reply.find("---^".encode('utf-8')) != -1:
            # read again the syntax error msg
            reply = self.sock.recv(1024)
        return reply

    def send_command(self, cmd):
        """ Send the command specified over the socket
        :param cmd: Command to send as string
        :return: None
        """
        cmd += '\n'
        self.sock.send(cmd.encode('utf-8'))

    def set_keep_alive(self):
        """ Set the keep alive for the socket
        :return: None
        """
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)


class KeepAliveThread(threading.Thread):
    """
    Keep alive socket class
    """
    message = ''

    def __init__(self, connection, interval=10):
        """ Constructor
        :param connection: Socket for keep alive
        :param interval: interval in seconds to send keep alive
        :return: KeepAliveThread object
        """
        threading.Thread.__init__(self)
        self.connection = connection
        self.interval = interval
        self.finished = threading.Event()
        self.setDaemon(True)
        _LOGGER.debug(
            'Xena Socket keep alive thread initiated, interval ' +
            '{} seconds'.format(self.interval))

    def stop(self):
        """ Thread stop. See python thread docs for more info
        :return: None
        """
        self.finished.set()
        self.join()

    def run(self):
        """ Thread start. See python thread docs for more info
        :return: None
        """
        while not self.finished.isSet():
            self.finished.wait(self.interval)
            self.connection.ask(self.message)


class XenaSocketDriver(SimpleSocket):
    """
    Xena socket class
    """
    reply_ok = '<OK>'

    def __init__(self, hostname, port=22611):
        """ Constructor
        :param hostname: Hostname or ip as string
        :param port: port to use as int
        :return: XenaSocketDriver object
        """
        SimpleSocket.__init__(self, hostname=hostname, port=port)
        SimpleSocket.set_keep_alive(self)
        self.access_semaphor = threading.Semaphore(1)

    def ask(self, cmd):
        """ Send the command over the socket in a thread safe manner
        :param cmd: Command to send
        :return: reply from socket
        """
        self.access_semaphor.acquire()
        reply = SimpleSocket.ask(self, cmd)
        self.access_semaphor.release()
        return reply

    def ask_verify(self, cmd):
        """ Send the command over the socket in a thread safe manner and
        verify the response is good.
        :param cmd: Command to send
        :return: Boolean True if command response is good, False otherwise
        """
        resp = self.ask(cmd).decode(_LOCALE).strip('\n')
        _LOGGER.info('[ask_verify] %s', resp)
        if resp == self.reply_ok:
            return True
        return False

    def disconnect(self):
        """
        Close the socket connection
        :return: None
        """
        self.sock.close()

    def send_command(self, cmd):
        """ Send the command over the socket with no return
        :param cmd: Command to send
        :return: None
        """
        self.access_semaphor.acquire()
        SimpleSocket.send_command(self, cmd)
        self.access_semaphor.release()

    def send_query_replies(self, cmd):
        """ Send the command over the socket and wait for all replies and return
        the lines as a list
        :param cmd: Command to send
        :return: Response from command as list
        """
        # send the command followed by cmd SYNC to find out
        # when the last reply arrives.
        self.send_command(cmd.strip('\n'))
        self.send_command('SYNC')
        replies = []
        self.access_semaphor.acquire()
        msg = SimpleSocket.read_reply(self).decode(_LOCALE)
        msgleft = ''
        while True:
            if '\n' in msg:
                (reply, msgleft) = msg.split('\n', 1)
                # check for syntax problems
                if reply.rfind('Syntax') != -1:
                    self.access_semaphor.release()
                    return []

                if reply.rfind('<SYNC>') == 0:

                    self.access_semaphor.release()
                    return replies

                replies.append(reply + '\n')
                msg = msgleft
            else:
                # more bytes to come
                msgnew = SimpleSocket.read_reply(self).decode(_LOCALE)
                msg = msgleft + msgnew


class XenaManager(object):
    """
    Manager class for port and socket functions
    """
    def __init__(self, socketDriver, user='', password='xena'):
        """Constructor

        Establish a connection to Xena using a ``driver`` with the ``password``
        supplied.

        Attributes:
        :param socketDriver: XenaSocketDriver connection object
        :param password: Password to the Xena traffic generator
        :returns: XenaManager object
        """
        self.driver = socketDriver
        self.ports = list()
        self.keep_alive_thread = KeepAliveThread(self.driver)

        if self.logon(password):
            _LOGGER.info('Connected to Xena at %s', self.driver.hostname)
        else:
            _LOGGER.error('Failed to logon to Xena at %s', self.driver.hostname)
            return

        self.set_owner(user)

    def disconnect(self):
        """ Release ports and disconnect from chassis.
        """
        for module_port in self.ports:
            module_port.release_port()
        self.ports = []
        self.logoff()
        self.keep_alive_thread.stop()

    def add_module_port(self, module, port):
        """Factory for Xena Ports

        :param module: String or int of module
        :param port: String or int of port
        :return: XenaPort object if success, None if port already added
        """
        xenaport = XenaPort(self, module, port)
        if xenaport in self.ports:
            return None
        else:
            self.ports.append(xenaport)
            return xenaport

    def get_module_port(self, module, port):
        """Return the Xena Port object if available
        :param module: module number as int or str
        :param port: port number as int or str
        :return: XenaPort object or None if not found
        """
        for por in self.ports:
            if por.port == str(port) and por.module == str(module):
                return por
        return None

    def get_version(self):
        """
        Get the version from the chassis
        :return: versions of server and driver as string
        """
        res = self.driver.ask(make_manager_command(
            CMD_VERSION, '')).decode(_LOCALE)
        res = res.rstrip('\n').split()
        return "Server: {} Driver: {}".format(res[1], res[2])

    def logoff(self):
        """
        Logoff from the Xena chassis
        :return: Boolean True if response OK, False if error.
        """
        return self.driver.ask_verify(make_manager_command(CMD_LOGOFF))

    def logon(self, password):
        """Login to the Xena traffic generator using the ``password`` supplied.

        :param password: string of password
        :return: Boolean True if response OK, False if error.
        """
        self.keep_alive_thread.start()
        return self.driver.ask_verify(make_manager_command(CMD_LOGIN, password))

    def set_owner(self, username):
        """Set the ports owner.
        :return: Boolean True if response OK, False if error.
        """
        return self.driver.ask_verify(make_manager_command(CMD_OWNER, username))

# pylint: disable=too-many-public-methods
class XenaPort(object):
    """
    Xena Port emulator class
    """
    def __init__(self, manager, module, port):
        """Constructor

        :param manager: XenaManager object
        :param module: Module as string or int of module to use
        :param port: Port as string or int of port to use
        :return: XenaPort object
        """
        self._manager = manager
        self._module = str(module)
        self._port = str(port)
        self._streams = list()

    @property
    def manager(self):
        """Property for manager attribute
        :return: manager object
        """
        return self._manager

    @property
    def module(self):
        """Property for module attribute
        :return: module value as string
        """
        return self._module

    @property
    def port(self):
        """Property for port attribute
        :return: port value as string
        """
        return self._port

    def port_string(self):
        """String builder with attributes
        :return: String of module port for command sequence
        """
        stringify = "{}/{}".format(self._module, self._port)
        return stringify

    def add_stream(self):
        """Add a stream to the port.
        :return: XenaStream object, None if failure
        """
        identifier = len(self._streams)
        stream = XenaStream(self, identifier)
        if self._manager.driver.ask_verify(make_stream_command(
                CMD_CREATE_STREAM, '', stream)):
            self._streams.append(stream)
            return stream
        else:
            _LOGGER.error("Error during stream creation")
            return None

    def clear_stats(self, rx_clear=True, tx_clear=True):
        """Clear the port stats

        :param rx_clear: Boolean if rx stats are to be cleared
        :param tx_clear: Boolean if tx stats are to be cleared
        :return: Boolean True if response OK, False if error.
        """
        command = make_port_command(CMD_CLEAR_RX_STATS, self)
        res1 = self._manager.driver.ask_verify(command) if rx_clear else True
        command = make_port_command(CMD_CLEAR_TX_STATS, self)
        res2 = self._manager.driver.ask_verify(command) if tx_clear else True
        return all([res1, res2])

    def get_effective_speed(self):
        """
        Get the effective speed on the port
        :return: effective speed as float
        """
        port_speed = self.get_port_speed()
        reduction = self.get_port_speed_reduction()
        effective_speed = port_speed * (1.0 - reduction / 1000000.0)
        return effective_speed

    def get_inter_frame_gap(self):
        """
        Get the interframe gap and return it as string
        :return: integer of interframe gap
        """
        command = make_port_command(CMD_INTERFRAME_GAP + '?', self)
        res = self._manager.driver.ask(command).decode(_LOCALE)
        res = int(res.rstrip('\n').split(' ')[-1])
        return res

    def get_port_speed(self):
        """
        Get the port speed as bits from port and return it as a int.
        :return: Int of port speed
        """
        command = make_port_command(CMD_GET_PORT_SPEED, self)
        res = self._manager.driver.ask(command).decode(_LOCALE)
        port_speed = res.split(' ')[-1].rstrip('\n')
        return int(port_speed) * 1000000

    def get_port_speed_reduction(self):
        """
        Get the port speed reduction value as int
        :return: Integer of port speed reduction value
        """
        command = make_port_command(CMD_GET_PORT_SPEED_REDUCTION, self)
        res = self._manager.driver.ask(command).decode(_LOCALE)
        res = int(res.rstrip('\n').split(' ')[-1])
        return res

    def get_rx_stats(self):
        """Get the rx stats and return the data as a dict.
        :return: Receive stats as dictionary
        """
        command = make_port_command(CMD_GET_RX_STATS, self)
        rx_data = self._manager.driver.send_query_replies(command)
        data = XenaRXStats(rx_data, time.time())
        return data

    def get_tx_stats(self):
        """Get the tx stats and return the data as a dict.
        :return: Receive stats as dictionary
        """
        command = make_port_command(CMD_GET_TX_STATS, self)
        tx_data = self._manager.driver.send_query_replies(command)
        data = XenaTXStats(tx_data, time.time())
        return data

    def micro_tpld_disable(self):
        """Disable micro TPLD and return to standard payload size
        :return: Boolean if response OK, False if error
        """
        command = make_port_command(CMD_SET_TPLD_MODE + ' normal', self)
        return self._manager.driver.ask_verify(command)

    def micro_tpld_enable(self):
        """Enable micro TPLD 6 byte payloads.
        :Return Boolean if response OK, False if error
        """
        command = make_port_command(CMD_SET_TPLD_MODE + ' micro', self)
        return self._manager.driver.ask_verify(command)

    def release_port(self):
        """Release the port
        :return: Boolean True if response OK, False if error.
        """
        command = make_port_command(CMD_RELEASE, self)
        return self._manager.driver.ask_verify(command)

    def reserve_port(self):
        """Reserve the port
        :return: Boolean True if response OK, False if error.
        """
        command = make_port_command(CMD_RESERVE, self)
        return self._manager.driver.ask_verify(command)

    def reset_port(self):
        """Reset the port
        :return: Boolean True if response OK, False if error.
        """
        command = make_port_command(CMD_RESET, self)
        return self._manager.driver.ask_verify(command)

    def set_port_arp_reply(self, is_on=True, ipv6=False):
        """
        Set the port arpreply value
        :param on: Enable or disable the arp reply on the port
        :param v6: set the value on the ip v6, disabled will set at ip v4
        :return: Boolean True if response OK, False if error
        """
        command = make_port_command('{} {}'.format(
            CMD_SET_PORT_ARP_V6_REPLY if ipv6 else CMD_SET_PORT_ARP_REPLY,
            "on" if is_on else "off"), self)
        return self._manager.driver.ask_verify(command)

    def set_port_ping_reply(self, is_on=True, ipv6=False):
        """
        Set the port ping reply value
        :param on: Enable or disable the ping reply on the port
        :param v6: set the value on the ip v6, disabled will set at ip v4
        :return: Boolean True if response OK, False if error
        """
        command = make_port_command('{} {}'.format(
            CMD_SET_PORT_PING_V6_REPLY if ipv6 else CMD_SET_PORT_PING_REPLY,
            "on" if is_on else "off"), self)
        return self._manager.driver.ask_verify(command)

    def set_port_learning(self, interval):
        """Start port learning with the interval in seconds specified. 0 disables port learning
        :param: interval as int
        :return: Boolean True if response OK, False if error.
        """
        command = make_port_command('{} {}'.format(CMD_PORT_LEARNING, interval), self)
        return self._manager.driver.ask_verify(command)

    def set_port_ip(self, ip_addr, cidr, gateway, wild='255'):
        """
        Set the port ip address of the specific port
        :param ip_addr: IP address to set to port
        :param cidr: cidr number for the subnet
        :param gateway: Gateway ip for port
        :param wild: wildcard used for ARP and PING replies
        :return: Boolean True if response OK, False if error
        """
        # convert the cidr to a dot notation subnet address
        subnet = socket.inet_ntoa(
            struct.pack(">I", (0xffffffff << (32 - cidr)) & 0xffffffff))

        command = make_port_command('{} {} {} {} 0.0.0.{}'.format(
            CMD_PORT_IP, ip_addr, subnet, gateway, wild), self)
        return self._manager.driver.ask_verify(command)

    def set_port_time_limit(self, micro_seconds):
        """Set the port time limit in ms
        :param micro_seconds: ms for port time limit
        :return: Boolean True if response OK, False if error.
        """
        command = make_port_command('{} {}'.format(
            CMD_SET_PORT_TIME_LIMIT, micro_seconds), self)
        return self._manager.driver.ask_verify(command)

    def traffic_off(self):
        """Start traffic
        :return: Boolean True if response OK, False if error.
        """
        command = make_port_command(CMD_STOP_TRAFFIC, self)
        return self._manager.driver.ask_verify(command)

    def traffic_on(self):
        """Stop traffic
        :return: Boolean True if response OK, False if error.
        """
        command = make_port_command(CMD_START_TRAFFIC, self)
        return self._manager.driver.ask_verify(command)


class XenaStream(object):
    """
    Xena stream emulator class
    """
    def __init__(self, xenaPort, streamID):
        """Constructor

        :param xenaPort: XenaPort object
        :param streamID: Stream ID as int or string
        :return: XenaStream object
        """
        self._xena_port = xenaPort
        self._stream_id = str(streamID)
        self._manager = self._xena_port.manager
        self._header_protocol = None

    @property
    def xena_port(self):
        """Property for port attribute
        :return: XenaPort object
        """
        return self._xena_port

    @property
    def stream_id(self):
        """Property for streamID attribute
        :return: streamID value as string
        """
        return self._stream_id

    def enable_multistream(self, flows, layer):
        """
        Basic implementation of multi stream. Enable multi stream by setting
        modifiers on the stream
        :param flows: Numbers of flows or end range
        :param layer: layer to enable multi stream as str. Acceptable values
        are L2, L3, or L4
        :return: True if success False otherwise
        """
        if not self._header_protocol:
            raise RuntimeError(
                "Please set a protocol header before calling this method.")

        # byte offsets for setting the modifier
        offsets = {
            'L2': [0, 6],
            'L3': [32, 36] if 'VLAN' in self._header_protocol else [28, 32],
            'L4': [38, 40] if 'VLAN' in self._header_protocol else [34, 36]
        }

        responses = list()
        if layer in offsets.keys() and flows > 0:
            command = make_port_command(
                CMD_STREAM_MODIFIER_COUNT + ' [{}]'.format(self._stream_id) +
                ' 2', self._xena_port)
            responses.append(self._manager.driver.ask_verify(command))
            command = make_port_command(
                CMD_STREAM_MODIFIER + ' [{},0] {} 0xFFFF0000 INC 1'.format(
                    self._stream_id, offsets[layer][0]), self._xena_port)
            responses.append(self._manager.driver.ask_verify(command))
            command = make_port_command(
                CMD_STREAM_MODIFIER_RANGE + ' [{},0] 0 1 {}'.format(
                    self._stream_id, flows), self._xena_port)
            responses.append(self._manager.driver.ask_verify(command))
            command = make_port_command(
                CMD_STREAM_MODIFIER + ' [{},1] {} 0xFFFF0000 INC 1'.format(
                    self._stream_id, offsets[layer][1]), self._xena_port)
            responses.append(self._manager.driver.ask_verify(command))
            command = make_port_command(
                CMD_STREAM_MODIFIER_RANGE + ' [{},1] 0 1 {}'.format(
                    self._stream_id, flows), self._xena_port)
            responses.append(self._manager.driver.ask_verify(command))
            return all(responses)  # return True if they all worked
        elif flows < 1:
            _LOGGER.warning(
                'No flows specified in enable multistream. Bypassing...')
            return False
        else:
            raise NotImplementedError(
                "Non-implemented stream layer in method enable multistream ",
                "layer=", layer)

    def get_stream_data(self):
        """
        Get the response for stream data
        :return: String of response for stream data info
        """
        command = make_stream_command(CMD_GET_STREAM_DATA, '?', self)
        res = self._manager.driver.ask(command).decode(_LOCALE)
        return res

    def set_header_protocol(self, protocol_header):
        """Set the header info for the packet header hex.
        If the packet header contains just Ethernet and IP info then call this
        method with ETHERNET IP as the protocol header.

        :param protocol_header: protocol header argument
        :return: Boolean True if success, False if error
        """
        command = make_stream_command(
            CMD_SET_STREAM_HEADER_PROTOCOL,
            protocol_header, self)
        if self._manager.driver.ask_verify(command):
            self._header_protocol = protocol_header
            return True
        else:
            return False

    def set_off(self):
        """Set the stream to off
        :return: Boolean True if success, False if error
        """
        return self._manager.driver.ask_verify(make_stream_command(
            CMD_SET_STREAM_ON_OFF, 'off', self))

    def set_on(self):
        """Set the stream to on
        :return: Boolean True if success, False if error
        """
        return self._manager.driver.ask_verify(make_stream_command(
            CMD_SET_STREAM_ON_OFF, 'on', self))

    def set_packet_header(self, header):
        """Set the stream packet header

        :param header: packet header as hex bytes
        :return: Boolean True if success, False if error
        """
        return self._manager.driver.ask_verify(make_stream_command(
            CMD_SET_STREAM_PACKET_HEADER, header, self))

    def set_packet_length(self, pattern_type, minimum, maximum):
        """Set the pattern length with min and max values based on the pattern
        type supplied

        :param pattern_type: String of pattern type, valid entries [ fixed,
         butterfly, random, mix, incrementing ]
        :param minimum: integer of minimum byte value
        :param maximum: integer of maximum byte value
        :return: Boolean True if success, False if error
        """
        return self._manager.driver.ask_verify(make_stream_command(
            CMD_SET_STREAM_PACKET_LENGTH, '{} {} {}'.format(
                pattern_type, minimum, maximum), self))

    def set_packet_limit(self, limit):
        """Set the packet limit

        :param limit: number of packets that will be sent, use -1 to disable
        :return: Boolean True if success, False if error
        """
        return self._manager.driver.ask_verify(make_stream_command(
            CMD_SET_STREAM_PACKET_LIMIT, limit, self))

    def set_packet_payload(self, payload_type, hex_value):
        """Set the payload to the hex value based on the payload type

        :param payload_type: string of the payload type, valid entries [ pattern,
         incrementing, prbs ]
        :param hex_value: hex string of valid hex
        :return: Boolean True if success, False if error
        """
        return self._manager.driver.ask_verify(make_stream_command(
            CMD_SET_STREAM_PACKET_PAYLOAD, '{} {}'.format(
                payload_type, hex_value), self))

    def set_rate_fraction(self, fraction):
        """Set the rate fraction

        :param fraction: fraction for the stream
        :return: Boolean True if success, False if error
        """
        return self._manager.driver.ask_verify(make_stream_command(
            CMD_SET_STREAM_RATE_FRACTION, fraction, self))

    def set_payload_id(self, identifier):
        """ Set the test payload ID
        :param identifier: ID as int or string
        :return: Boolean True if success, False if error
        """
        return self._manager.driver.ask_verify(make_stream_command(
            CMD_SET_STREAM_TEST_PAYLOAD_ID, identifier, self))


class XenaRXStats(object):
    """
    Receive stat class
    """
    def __init__(self, stats, epoc):
        """ Constructor
        :param stats: Stats from pr all command as list
        :param epoc: Current time in epoc
        :return: XenaRXStats object
        """
        self._stats = stats
        self._time = epoc
        self.data = self.parse_stats()
        self.preamble = 8

    @staticmethod
    def _pack_stats(param, start, fields=None):
        """ Pack up the list of stats in a dictionary
        :param param: The list of params to process
        :param start: What element to start at
        :param fields: The field names to pack as keys
        :return: Dictionary of data where fields match up to the params
        """
        if not fields:
            fields = ['bps', 'pps', 'bytes', 'packets']
        data = {}
        i = 0
        for column in fields:
            data[column] = int(param[start + i])
            i += 1

        return data

    @staticmethod
    def _pack_tplds_stats(param, start):
        """ Pack up the tplds stats
        :param param: List of params to pack
        :param start: What element to start at
        :return: Dictionary of stats
        """
        data = {}
        i = 0
        for val in range(start, len(param) - start):
            data[i] = int(param[val])
            i += 1
        return data

    def _pack_rxextra_stats(self, param, start):
        """ Pack up the extra stats
        :param param: List of params to pack
        :param start: What element to start at
        :return: Dictionary of stats
        """
        fields = ['fcserrors', 'pauseframes', 'arprequests', 'arpreplies',
                  'pingrequests', 'pingreplies', 'gapcount', 'gapduration']
        return self._pack_stats(param, start, fields)

    def _pack_tplderrors_stats(self, param, start):
        """ Pack up tlpd errors
        :param param: List of params to pack
        :param start: What element to start at
        :return: Dictionary of stats
        """
        fields = ['dummy', 'seq', 'mis', 'pld']
        return self._pack_stats(param, start, fields)

    def _pack_tpldlatency_stats(self, param, start):
        """ Pack up the tpld latency stats
        :param param: List of params to pack
        :param start: What element to start at
        :return: Dictionary of stats
        """
        fields = ['min', 'avg', 'max', '1sec']
        return self._pack_stats(param, start, fields)

    def _pack_tpldjitter_stats(self, param, start):
        """ Pack up the tpld jitter stats
        :param param: List of params to pack
        :param start: What element to start at
        :return: Dictionary of stats
        """
        fields = ['min', 'avg', 'max', '1sec']
        return self._pack_stats(param, start, fields)

    @property
    def time(self):
        """
        :return: Time as String of epoc of when stats were collected
        """
        return self._time

    # pylint: disable=too-many-branches
    def parse_stats(self):
        """ Parse the stats from pr all command
        :return: Dictionary of all stats
        """
        statdict = {}
        for line in self._stats:
            param = line.split()
            if param[1] == 'PR_TOTAL':
                statdict['pr_total'] = self._pack_stats(param, 2)
            elif param[1] == 'PR_NOTPLD':
                statdict['pr_notpld'] = self._pack_stats(param, 2,)
            elif param[1] == 'PR_EXTRA':
                statdict['pr_extra'] = self._pack_rxextra_stats(param, 2)
            elif param[1] == 'PT_STREAM':
                entry_id = "pt_stream_%s" % param[2].strip('[]')
                statdict[entry_id] = self._pack_stats(param, 3)
            elif param[1] == 'PR_TPLDS':
                tid_list = self._pack_tplds_stats(param, 2)
                if len(tid_list):
                    statdict['pr_tplds'] = tid_list
            elif param[1] == 'PR_TPLDTRAFFIC':
                if 'pr_tpldstraffic' in statdict:
                    data = statdict['pr_tpldstraffic']
                else:
                    data = {}
                entry_id = param[2].strip('[]')
                data[entry_id] = self._pack_stats(param, 3)
                statdict['pr_tpldstraffic'] = data
            elif param[1] == 'PR_TPLDERRORS':
                if 'pr_tplderrors' in statdict:
                    data = statdict['pr_tplderrors']
                else:
                    data = {}
                entry_id = param[2].strip('[]')
                data[entry_id] = self._pack_tplderrors_stats(param, 3)
                statdict['pr_tplderrors'] = data
            elif param[1] == 'PR_TPLDLATENCY':
                if 'pr_tpldlatency' in statdict:
                    data = statdict['pr_tpldlatency']
                else:
                    data = {}
                entry_id = param[2].strip('[]')
                data[entry_id] = self._pack_tpldlatency_stats(param, 3)
                statdict['pr_tpldlatency'] = data
            elif param[1] == 'PR_TPLDJITTER':
                if 'pr_tpldjitter' in statdict:
                    data = statdict['pr_tpldjitter']
                else:
                    data = {}
                entry_id = param[2].strip('[]')
                data[entry_id] = self._pack_tpldjitter_stats(param, 3)
                statdict['pr_pldjitter'] = data
            elif param[1] == 'PR_FILTER':
                if 'pr_filter' in statdict:
                    data = statdict['pr_filter']
                else:
                    data = {}
                entry_id = param[2].strip('[]')
                data[entry_id] = self._pack_stats(param, 3)
                statdict['pr_filter'] = data
            elif param[1] == 'P_RECEIVESYNC':
                if param[2] == 'IN_SYNC':
                    statdict['p_receivesync'] = {'IN SYNC': 'True'}
                else:
                    statdict['p_receivesync'] = {'IN SYNC': 'False'}
            else:
                logging.warning("XenaPort: unknown stats: %s", param[1])

        mydict = statdict
        return mydict


class XenaTXStats(object):
    """
    Xena transmit stat class
    """
    def __init__(self, stats, epoc):
        """ Constructor
        :param stats: Stats from pt all command as list
        :param epoc: Current time in epoc
        :return: XenaTXStats object
        """
        self._stats = stats
        self._time = epoc
        self._ptstreamkeys = list()
        self.data = self.parse_stats()
        self.preamble = 8

    @staticmethod
    def _pack_stats(params, start, fields=None):
        """ Pack up the list of stats in a dictionary
        :param params: The list of params to process
        :param start: What element to start at
        :param fields: The field names to pack as keys
        :return: Dictionary of data where fields match up to the params
        """
        if not fields:
            fields = ['bps', 'pps', 'bytes', 'packets']
        data = {}
        i = 0
        for column in fields:
            data[column] = int(params[start + i])
            i += 1

        return data

    def _pack_txextra_stats(self, params, start):
        """ Pack up the tx extra stats
        :param params: List of params to pack
        :param start: What element to start at
        :return: Dictionary of stats
        """
        fields = ['arprequests', 'arpreplies', 'pingrequests', 'pingreplies',
                  'injectedfcs', 'injectedseq', 'injectedmis', 'injectedint',
                  'injectedtid', 'training']
        return self._pack_stats(params, start, fields)

    @property
    def pt_stream_keys(self):
        """
        :return: Return a list of pt_stream_x stream key ids
        """
        return self._ptstreamkeys

    @property
    def time(self):
        """
        :return: Time as String of epoc of when stats were collected
        """
        return self._time

    def parse_stats(self):
        """ Parse the stats from pr all command
        :return: Dictionary of all stats
        """
        statdict = {}
        for line in self._stats:
            param = line.split()
            if param[1] == 'PT_TOTAL':
                statdict['pt_total'] = self._pack_stats(param, 2)
            elif param[1] == 'PT_NOTPLD':
                statdict['pt_notpld'] = self._pack_stats(param, 2,)
            elif param[1] == 'PT_EXTRA':
                statdict['pt_extra'] = self._pack_txextra_stats(param, 2)
            elif param[1] == 'PT_STREAM':
                entry_id = "pt_stream_%s" % param[2].strip('[]')
                self._ptstreamkeys.append(entry_id)
                statdict[entry_id] = self._pack_stats(param, 3)
            else:
                logging.warning("XenaPort: unknown stats: %s", param[1])
        mydict = statdict
        return mydict

def aggregate_stats(stat1, stat2):
    """
    Judge whether stat1 and stat2 both have same key, if both have same key,
    call the aggregate fuction, else use the stat1's value
    """
    newstat = dict()
    for keys in stat1.keys():
        if keys in stat2 and isinstance(stat1[keys], dict):
            newstat[keys] = aggregate(stat1[keys], stat2[keys])
        else:
            newstat[keys] = stat1[keys]
    return newstat

def aggregate(stat1, stat2):
    """
    Recursive function to aggregate two sets of statistics. This is used when
    bi directional traffic is done and statistics need to be calculated based
    on two sets of statistics.
    :param stat1: One set of dictionary stats from RX or TX stats
    :param stat2: Second set of dictionary stats from RX or TX stats
    :return: stats for data entry in RX or TX Stats instance
    """
    newstat = dict()
    for (keys1, keys2) in zip(stat1.keys(), stat2.keys()):
        if isinstance(stat1[keys1], dict):
            newstat[keys1] = aggregate(stat1[keys1], stat2[keys2])
        else:
            if not isinstance(stat1[keys1], int) and not isinstance(
                    [keys1], float):
                # its some value we don't need to aggregate
                return stat1[keys1]
            # for latency stats do the appropriate calculation
            if keys1 == 'max':
                newstat[keys1] = max(stat1[keys1], stat2[keys2])
            elif keys1 == 'min':
                newstat[keys1] = min(stat1[keys1], stat2[keys2])
            elif keys1 == 'avg':
                newstat[keys1] = (stat1[keys1] + stat2[keys2]) / 2
            else:
                newstat[keys1] = (stat1[keys1] + stat2[keys2])
    return newstat


def line_percentage(port, stats, time_active, packet_size):
    """
    Calculate the line percentage rate from the duration, port object and stat
    object.
    :param port: XenaPort object
    :param stats: Xena RXStat or TXStat object
    :param time_active: time the stream was active in secs as int
    :param packet_size: packet size as int
    :return: line percentage as float
    """
    # this is ugly, but its prettier than calling the get method 3 times...
    try:
        packets = stats.data['pr_total']['packets']
    except KeyError:
        try:
            packets = stats.data['pt_total']['packets']
        except KeyError:
            _LOGGER.error(
                'Could not calculate line rate because packet stat not found.')
            return 0
    ifg = port.get_inter_frame_gap()
    pps = packets_per_second(packets, time_active)
    l2br = l2_bit_rate(packet_size, stats.preamble, pps)
    l1br = l1_bit_rate(l2br, pps, ifg, stats.preamble)
    return 100.0 * l1br / port.get_effective_speed()


def l2_bit_rate(packet_size, preamble, pps):
    """
    Return the l2 bit rate
    :param packet_size: packet size on the line in bytes
    :param preamble: preamble size of the packet header in bytes
    :param pps: packets per second
    :return: l2 bit rate as float
    """
    return (packet_size * preamble) * pps


def l1_bit_rate(l2br, pps, ifg, preamble):
    """
    Return the l1 bit rate
    :param l2br: l2 bit rate int bits per second
    :param pps: packets per second
    :param ifg: the inter frame gap
    :param preamble: preamble size of the packet header in bytes
    :return: l1 bit rate as float
    """
    return l2br + (pps * ifg * preamble)


def make_manager_command(cmd, argument=None):
    """ String builder for Xena socket commands

    :param cmd: Command to send
    :param argument: Arguments for command to send
    :return: String of command
    """
    command = '{} "{}"'.format(cmd, argument) if argument else cmd
    _LOGGER.info("[Command Sent] : %s", command)
    return command


def make_port_command(cmd, xena_port):
    """ String builder for Xena port commands

    :param cmd: Command to send
    :param xena_port: XenaPort object
    :return: String of command
    """
    command = "{} {}".format(xena_port.port_string(), cmd)
    _LOGGER.info("[Command Sent] : %s", command)
    return command


def make_stream_command(cmd, args, xena_stream):
    """ String builder for Xena port commands

    :param cmd: Command to send
    :param xena_stream: XenaStream object
    :return: String of command
    """
    command = "{} {} [{}] {}".format(xena_stream.xena_port.port_string(), cmd,
                                     xena_stream.stream_id, args)
    _LOGGER.info("[Command Sent] : %s", command)
    return command


def packets_per_second(packets, time_in_sec):
    """
    Return the pps as float
    :param packets: total packets
    :param time_in_sec: time in seconds
    :return: float of pps
    """
    return packets / time_in_sec
