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

# Contributors:
#   Dan Amzulescu, Xena Networks
#   Christian Trautman, Red Hat Inc.
#
# Usage can be seen below in unit test. This implementation is designed for one
# module two port Xena chassis runs only.

"""
Xena JSON module
"""

from collections import OrderedDict
import locale
import logging
import os

import scapy.layers.inet as inet

from yardstick.traffic_generator.tools.pkt_gen.xena.json import json_utilities

_LOGGER = logging.getLogger(__name__)
_LOCALE = locale.getlocale()[1]

_CURR_DIR = os.path.dirname(os.path.realpath(__file__))


class XenaJSON(object):
    """
    Parent Class to modify and read Xena JSON configuration files.
    """
    def __init__(self,
                 json_path=os.path.join(
                     _CURR_DIR, '../profiles/baseconfig.x2544')):
        """
        Constructor
        :param json_path: path to JSON file to read. Expected files must have
         two module ports with each port having its own stream config profile.
        :return: XenaJSON object
        """
        self.json_data = json_utilities.read_json_file(json_path)

        self.packet_data = OrderedDict()
        self.packet_data['layer2'] = None
        self.packet_data['vlan'] = None
        self.packet_data['layer3'] = None
        self.packet_data['layer4'] = None

    def _add_multistream_layer(self, entity, seg_uuid, stop_value, layer):
        """
        Add the multi stream layers to the json file based on the layer provided
        :param entity: Entity to append the segment to in entity list
        :param seg_uuid: The UUID to attach the multistream layer to
        :param stop_value: The number of flows to configure
        :param layer: the layer that the multistream will be attached to
        :return: None
        """
        field_name = {
            2: ('Dst MAC addr', 'Src MAC addr'),
            3: ('Dest IP Addr', 'Src IP Addr'),
            4: ('Dest Port', 'Src Port')
        }
        segments = [
            {
                "Offset": 0,
                "Mask": "//8=",  # mask of 255/255
                "Action": "INC",
                "StartValue": 0,
                "StopValue": stop_value,
                "StepValue": 1,
                "RepeatCount": 1,
                "SegmentId": seg_uuid,
                "FieldName": field_name[int(layer)][0]
            },
            {
                "Offset": 0,
                "Mask": "//8=",  # mask of 255/255
                "Action": "INC",
                "StartValue": 0,
                "StopValue": stop_value,
                "StepValue": 1,
                "RepeatCount": 1,
                "SegmentId": seg_uuid,
                "FieldName": field_name[int(layer)][1]
            }
        ]

        self.json_data['StreamProfileHandler']['EntityList'][entity][
            'StreamConfig']['HwModifiers'] = (segments)

    def _create_packet_header(self):
        """
        Create the scapy packet header based on what has been built in this
        instance using the set header methods. Return tuple of the two byte
        arrays, one for each port.
        :return: Scapy packet headers as bytearrays
        """
        if not self.packet_data['layer2']:
            _LOGGER.warning('Using dummy info for layer 2 in Xena JSON file')
            self.set_header_layer2()
        packet1, packet2 = (self.packet_data['layer2'][0],
                            self.packet_data['layer2'][1])
        for packet_header in list(self.packet_data.copy().values())[1:]:
            if packet_header:
                packet1 /= packet_header[0]
                packet2 /= packet_header[1]
        ret = (bytes(packet1), bytes(packet2))
        return ret

    def add_header_segments(self, flows=0, multistream_layer=None):
        """
        Build the header segments to write to the JSON file.
        :param flows: Number of flows to configure for multistream if enabled
        :param multistream_layer: layer to set multistream flows as string.
        Acceptable values are L2, L3 or L4
        :return: None
        """
        packet = self._create_packet_header()
        segment1 = list()
        segment2 = list()
        header_pos = 0
        if self.packet_data['layer2']:
            # slice out the layer 2 bytes from the packet header byte array
            layer2 = packet[0][header_pos: len(self.packet_data['layer2'][0])]
            seg = json_utilities.create_segment(
                "ETHERNET", json_utilities.encode_byte_array(layer2).decode(
                    _LOCALE))
            if multistream_layer == 'L2' and flows > 0:
                self._add_multistream_layer(entity=0, seg_uuid=seg['ItemID'],
                                            stop_value=flows, layer=2)
            segment1.append(seg)
            # now do the other port data with reversed src, dst info
            layer2 = packet[1][header_pos: len(self.packet_data['layer2'][1])]
            seg = json_utilities.create_segment(
                "ETHERNET", json_utilities.encode_byte_array(layer2).decode(
                    _LOCALE))
            segment2.append(seg)
            if multistream_layer == 'L2' and flows > 0:
                self._add_multistream_layer(entity=1, seg_uuid=seg['ItemID'],
                                            stop_value=flows, layer=2)
            header_pos = len(layer2)
        if self.packet_data['vlan']:
            # slice out the vlan bytes from the packet header byte array
            vlan = packet[0][header_pos: len(
                self.packet_data['vlan'][0]) + header_pos]
            segment1.append(json_utilities.create_segment(
                "VLAN", json_utilities.encode_byte_array(vlan).decode(_LOCALE)))
            segment2.append(json_utilities.create_segment(
                "VLAN", json_utilities.encode_byte_array(vlan).decode(_LOCALE)))
            header_pos += len(vlan)
        if self.packet_data['layer3']:
            # slice out the layer 3 bytes from the packet header byte array
            layer3 = packet[0][header_pos: len(
                self.packet_data['layer3'][0]) + header_pos]
            seg = json_utilities.create_segment(
                "IP", json_utilities.encode_byte_array(layer3).decode(_LOCALE))
            segment1.append(seg)
            if multistream_layer == 'L3' and flows > 0:
                self._add_multistream_layer(entity=0, seg_uuid=seg['ItemID'],
                                            stop_value=flows, layer=3)
            # now do the other port data with reversed src, dst info
            layer3 = packet[1][header_pos: len(
                self.packet_data['layer3'][1]) + header_pos]
            seg = json_utilities.create_segment(
                "IP", json_utilities.encode_byte_array(layer3).decode(_LOCALE))
            segment2.append(seg)
            if multistream_layer == 'L3' and flows > 0:
                self._add_multistream_layer(entity=1, seg_uuid=seg['ItemID'],
                                            stop_value=flows, layer=3)
            header_pos += len(layer3)
        if self.packet_data['layer4']:
            # slice out the layer 4 bytes from the packet header byte array
            layer4 = packet[0][header_pos: len(
                self.packet_data['layer4'][0]) + header_pos]
            seg = json_utilities.create_segment(
                "UDP", json_utilities.encode_byte_array(layer4).decode(_LOCALE))
            segment1.append(seg)
            if multistream_layer == 'L4' and flows > 0:
                self._add_multistream_layer(entity=0, seg_uuid=seg['ItemID'],
                                            stop_value=flows, layer=4)
            # now do the other port data with reversed src, dst info
            layer4 = packet[1][header_pos: len(
                self.packet_data['layer4'][1]) + header_pos]
            seg = json_utilities.create_segment(
                "UDP", json_utilities.encode_byte_array(layer4).decode(_LOCALE))
            segment2.append(seg)
            if multistream_layer == 'L4' and flows > 0:
                self._add_multistream_layer(entity=1, seg_uuid=seg['ItemID'],
                                            stop_value=flows, layer=4)
            header_pos += len(layer4)

        self.json_data['StreamProfileHandler']['EntityList'][0][
            'StreamConfig']['HeaderSegments'] = segment1
        self.json_data['StreamProfileHandler']['EntityList'][1][
            'StreamConfig']['HeaderSegments'] = segment2

    def disable_back2back_test(self):
        """
        Disable the rfc2544 back to back test
        :return: None
        """
        self.json_data['TestOptions']['TestTypeOptionMap']['Back2Back'][
            'Enabled'] = 'false'

    def disable_throughput_test(self):
        """
        Disable the rfc2544 throughput test
        :return: None
        """
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'Enabled'] = 'false'

    def enable_back2back_test(self):
        """
        Enable the rfc2544 back to back test
        :return: None
        """
        self.json_data['TestOptions']['TestTypeOptionMap']['Back2Back'][
            'Enabled'] = 'true'

    def enable_throughput_test(self):
        """
        Enable the rfc2544 throughput test
        :return: None
        """
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'Enabled'] = 'true'
    # pylint: disable=too-many-arguments
    def modify_2544_tput_options(self, initial_value, minimum_value,
                                 maximum_value, value_resolution,
                                 use_pass_threshhold, pass_threshhold):
        """
        modify_2544_tput_options
        """
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'RateIterationOptions']['InitialValue'] = initial_value
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'RateIterationOptions']['MinimumValue'] = minimum_value
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'RateIterationOptions']['MaximumValue'] = maximum_value
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'RateIterationOptions']['ValueResolution'] = value_resolution
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'RateIterationOptions']['UsePassThreshold'] = use_pass_threshhold
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'RateIterationOptions']['PassThreshold'] = pass_threshhold

    def set_chassis_info(self, hostname, pwd):
        """
        Set the chassis info
        :param hostname: hostname as string of ip
        :param pwd: password to chassis as string
        :return: None
        """
        self.json_data['ChassisManager']['ChassisList'][0][
            'HostName'] = hostname
        self.json_data['ChassisManager']['ChassisList'][0][
            'Password'] = pwd

    def set_header_layer2(self, dst_mac='cc:cc:cc:cc:cc:cc',
                          src_mac='bb:bb:bb:bb:bb:bb', **kwargs):
        """
        Build a scapy Ethernet L2 objects inside instance packet_data structure
        :param dst_mac: destination mac as string. Example "aa:aa:aa:aa:aa:aa"
        :param src_mac: source mac as string. Example "bb:bb:bb:bb:bb:bb"
        :param kwargs: Extra params per scapy usage.
        :return: None
        """
        self.packet_data['layer2'] = [
            inet.Ether(dst=dst_mac, src=src_mac, **kwargs),
            inet.Ether(dst=src_mac, src=dst_mac, **kwargs)]

    def set_header_layer3(self, src_ip='192.168.0.2', dst_ip='192.168.0.3',
                          protocol='UDP', **kwargs):
        """
        Build scapy IPV4 L3 objects inside instance packet_data structure
        :param src_ip: source IP as string in dot notation format
        :param dst_ip: destination IP as string in dot notation format
        :param protocol: protocol for l4
        :param kwargs: Extra params per scapy usage
        :return: None
        """
        self.packet_data['layer3'] = [
            inet.IP(src=src_ip, dst=dst_ip, proto=protocol.lower(), **kwargs),
            inet.IP(src=dst_ip, dst=src_ip, proto=protocol.lower(), **kwargs)]

    def set_header_layer4_udp(self, source_port, destination_port, **kwargs):
        """
        Build scapy UDP L4 objects inside instance packet_data structure
        :param source_port: Source port as int
        :param destination_port: Destination port as int
        :param kwargs: Extra params per scapy usage
        :return: None
        """
        self.packet_data['layer4'] = [
            inet.UDP(sport=source_port, dport=destination_port, **kwargs),
            inet.UDP(sport=source_port, dport=destination_port, **kwargs)]

    def set_header_vlan(self, vlan_id=1, **kwargs):
        """
        Build a Dot1Q scapy object inside instance packet_data structure
        :param vlan_id: The VLAN ID
        :param kwargs: Extra params per scapy usage
        :return: None
        """
        self.packet_data['vlan'] = [
            inet.Dot1Q(vlan=vlan_id, **kwargs),
            inet.Dot1Q(vlan=vlan_id, **kwargs)]

    def set_port(self, index, module, port):
        """
        Set the module and port for the 0 index port to use with the test
        :param index: Index of port to set, 0 = port1, 1=port2, etc..
        :param module: module location as int
        :param port: port location in module as int
        :return: None
        """
        self.json_data['PortHandler']['EntityList'][index]['PortRef'][
            'ModuleIndex'] = module
        self.json_data['PortHandler']['EntityList'][index]['PortRef'][
            'PortIndex'] = port

    def set_port_ip_v4(self, port, ip_addr, netmask, gateway):
        """
        Set the port IP info
        :param port: port number as int of port to set ip info
        :param ip_addr: ip address in dot notation format as string
        :param netmask: cidr number for netmask (ie 24/16/8) as int
        :param gateway: gateway address in dot notation format
        :return: None
        """
        available_ports = range(len(
            self.json_data['PortHandler']['EntityList']))
        if port not in available_ports:
            raise ValueError("{}{}{}".format(
                'Port assignment must be an available port ',
                'number in baseconfig file. Port=', port))
        self.json_data['PortHandler']['EntityList'][
            port]["IpV4Address"] = ip_addr
        self.json_data['PortHandler']['EntityList'][
            port]["IpV4Gateway"] = gateway
        self.json_data['PortHandler']['EntityList'][
            port]["IpV4RoutingPrefix"] = int(netmask)

    def set_port_ip_v6(self, port, ip_addr, netmask, gateway):
        """
        Set the port IP info
        :param port: port number as int of port to set ip info
        :param ip_addr: ip address as 8 groups of 4 hexadecimal groups separated
         by a colon.
        :param netmask: cidr number for netmask (ie 24/16/8) as int
        :param gateway: gateway address as string in 8 group of 4 hexadecimal
                        groups separated by a colon.
        :return: None
        """
        available_ports = range(len(
            self.json_data['PortHandler']['EntityList']))
        if port not in available_ports:
            raise ValueError("{}{}{}".format(
                'Port assignment must be an available port ',
                'number in baseconfig file. Port=', port))
        self.json_data['PortHandler']['EntityList'][
            port]["IpV6Address"] = ip_addr
        self.json_data['PortHandler']['EntityList'][
            port]["IpV6Gateway"] = gateway
        self.json_data['PortHandler']['EntityList'][
            port]["IpV6RoutingPrefix"] = int(netmask)

    def set_test_options_tput(self, packet_sizes, duration, iterations,
                              loss_rate, micro_tpld=False):
        """
        Set the tput test options
        :param packet_sizes: List of packet sizes to test, single int entry is
         acceptable for one packet size testing
        :param duration: time for each test in seconds as int
        :param iterations: number of iterations of testing as int
        :param loss_rate: acceptable loss rate as float
        :param micro_tpld: boolean if micro_tpld should be enabled or disabled
        :return: None
        """
        if isinstance(packet_sizes, int):
            packet_sizes = [packet_sizes]
        self.json_data['TestOptions']['PacketSizes'][
            'CustomPacketSizes'] = packet_sizes
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'Duration'] = duration
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'RateIterationOptions']['AcceptableLoss'] = loss_rate
        self.json_data['TestOptions']['FlowCreationOptions'][
            'UseMicroTpldOnDemand'] = 'true' if micro_tpld else 'false'
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'Iterations'] = iterations

    def set_test_options_back2back(self, packet_sizes, duration,
                                   iterations, startvalue, endvalue,
                                   micro_tpld=False):
        """
        Set the back2back test options
        :param packet_sizes: List of packet sizes to test, single int entry is
         acceptable for one packet size testing
        :param duration: time for each test in seconds as int
        :param iterations: number of iterations of testing as int
        :param micro_tpld: boolean if micro_tpld should be enabled or disabled
        :param StartValue: start value
        :param EndValue: end value
        :return: None
        """
        if isinstance(packet_sizes, int):
            packet_sizes = [packet_sizes]
        self.json_data['TestOptions']['PacketSizes'][
            'CustomPacketSizes'] = packet_sizes
        self.json_data['TestOptions']['TestTypeOptionMap']['Back2Back'][
            'Duration'] = duration
        self.json_data['TestOptions']['FlowCreationOptions'][
            'UseMicroTpldOnDemand'] = 'true' if micro_tpld else 'false'
        self.json_data['TestOptions']['TestTypeOptionMap']['Back2Back'][
            'Iterations'] = iterations
        self.json_data['TestOptions']['TestTypeOptionMap']['Back2Back'][
            'RateSweepOptions']['StartValue'] = startvalue
        self.json_data['TestOptions']['TestTypeOptionMap']['Back2Back'][
            'RateSweepOptions']['EndValue'] = endvalue

    def write_config(self, path='./2bUsed.x2544'):
        """
        Write the config to out as file
        :param path: Output file to export the json data to
        :return: None
        """
        if not json_utilities.write_json_file(self.json_data, path):
            raise RuntimeError("Could not write out file, please check config")
