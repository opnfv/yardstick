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

import mock
from trex_stl_lib import trex_stl_client
from trex_stl_lib import trex_stl_packet_builder_scapy
from trex_stl_lib import trex_stl_streams

from yardstick.common import constants
from yardstick.network_services.helpers.vpp_helpers.multiple_loss_ratio_search import \
    MultipleLossRatioSearch
from yardstick.network_services.helpers.vpp_helpers.ndr_pdr_result import \
    NdrPdrResult
from yardstick.network_services.helpers.vpp_helpers.receive_rate_interval import \
    ReceiveRateInterval
from yardstick.network_services.helpers.vpp_helpers.receive_rate_measurement import \
    ReceiveRateMeasurement
from yardstick.network_services.traffic_profile import base as tp_base
from yardstick.network_services.traffic_profile import rfc2544, vpp_rfc2544
from yardstick.network_services.traffic_profile.rfc2544 import PortPgIDMap
from yardstick.tests.unit import base


class TestVppRFC2544Profile(base.BaseUnitTestCase):
    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "duration": 30,
            "enable_latency": True,
            "frame_rate": 100,
            "intermediate_phases": 2,
            "lower_bound": 1.0,
            "step_interval": 0.5,
            "test_precision": 0.1,
            "upper_bound": 100.0}}

    TRAFFIC_PROFILE_MAX_RATE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "duration": 30,
            "enable_latency": True,
            "frame_rate": 10000,
            "intermediate_phases": 2,
            "lower_bound": 1.0,
            "step_interval": 0.5,
            "test_precision": 0.1,
            "upper_bound": 100.0}}

    PROFILE = {
        "description": "Traffic profile to run RFC2544 latency",
        "downlink_0": {
            "ipv4": {
                "id": 2,
                "outer_l2": {
                    "framesize": {
                        "1024B": "0",
                        "1280B": "0",
                        "128B": "0",
                        "1400B": "0",
                        "1500B": "0",
                        "1518B": "0",
                        "256B": "0",
                        "373b": "0",
                        "512B": "0",
                        "570B": "0",
                        "64B": "100"
                    }
                },
                "outer_l3v4": {
                    "count": "1",
                    "dstip4": "10.0.0.0-10.0.0.100",
                    "proto": 61,
                    "srcip4": "20.0.0.0-20.0.0.100"
                }
            }
        },
        "name": "rfc2544",
        "schema": "nsb:traffic_profile:0.1",
        "traffic_profile": {
            "duration": 30,
            "enable_latency": True,
            "frame_rate": 100,
            "intermediate_phases": 2,
            "lower_bound": 1.0,
            "step_interval": 0.5,
            "test_precision": 0.1,
            "traffic_type": "VppRFC2544Profile",
            "upper_bound": 100.0
        },
        "uplink": {
            "ipv4": {
                "id": 1,
                "outer_l2": {
                    "framesize": {
                        "1024B": "0",
                        "1280B": "0",
                        "128B": "0",
                        "1400B": "0",
                        "1500B": "0",
                        "1518B": "0",
                        "256B": "0",
                        "373B": "0",
                        "512B": "0",
                        "570B": "0",
                        "64B": "100"
                    }
                },
                "outer_l3v4": {
                    "count": "10",
                    "dstip4": "20.0.0.0-20.0.0.100",
                    "proto": 61,
                    "srcip4": "10.0.0.0-10.0.0.100"
                }
            }
        }
    }

    def test___init__(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        self.assertEqual(vpp_rfc2544_profile.max_rate,
                         vpp_rfc2544_profile.rate)
        self.assertEqual(0, vpp_rfc2544_profile.min_rate)
        self.assertEqual(2, vpp_rfc2544_profile.number_of_intermediate_phases)
        self.assertEqual(30, vpp_rfc2544_profile.duration)
        self.assertEqual(0.1, vpp_rfc2544_profile.precision)
        self.assertEqual(1.0, vpp_rfc2544_profile.lower_bound)
        self.assertEqual(100.0, vpp_rfc2544_profile.upper_bound)
        self.assertEqual(0.5, vpp_rfc2544_profile.step_interval)
        self.assertEqual(True, vpp_rfc2544_profile.enable_latency)

    def test_init_traffic_params(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        mock_generator = mock.MagicMock()
        mock_generator.rfc2544_helper.latency = True
        mock_generator.rfc2544_helper.tolerance_low = 0.0
        mock_generator.rfc2544_helper.tolerance_high = 0.005
        mock_generator.scenario_helper.all_options = {
            "vpp_config": {
                "max_rate": 14880000
            }
        }
        vpp_rfc2544_profile.init_traffic_params(mock_generator)
        self.assertEqual(0.0, vpp_rfc2544_profile.tolerance_low)
        self.assertEqual(0.005, vpp_rfc2544_profile.tolerance_high)
        self.assertEqual(14880000, vpp_rfc2544_profile.max_rate)
        self.assertEqual(True, vpp_rfc2544_profile.enable_latency)

    def test_calculate_frame_size(self):
        imix = {'40B': 7, '576B': 4, '1500B': 1}
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        self.assertEqual((4084 / 12, 12),
                         vpp_rfc2544_profile.calculate_frame_size(imix))

    def test_calculate_frame_size_empty(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        self.assertEqual((64, 100),
                         vpp_rfc2544_profile.calculate_frame_size(None))

    def test_calculate_frame_size_error(self):
        imix = {'40B': -7, '576B': 4, '1500B': 1}
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        self.assertEqual((64, 100),
                         vpp_rfc2544_profile.calculate_frame_size(imix))

    def test__gen_payload(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        self.assertIsNotNone(vpp_rfc2544_profile._gen_payload(4))

    def test_register_generator(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        mock_generator = mock.MagicMock()
        mock_generator.rfc2544_helper.latency = True
        mock_generator.rfc2544_helper.tolerance_low = 0.0
        mock_generator.rfc2544_helper.tolerance_high = 0.005
        mock_generator.scenario_helper.all_options = {
            "vpp_config": {
                "max_rate": 14880000
            }
        }
        vpp_rfc2544_profile.register_generator(mock_generator)
        self.assertEqual(0.0, vpp_rfc2544_profile.tolerance_low)
        self.assertEqual(0.005, vpp_rfc2544_profile.tolerance_high)
        self.assertEqual(14880000, vpp_rfc2544_profile.max_rate)
        self.assertEqual(True, vpp_rfc2544_profile.enable_latency)

    def test_stop_traffic(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        mock_generator = mock.Mock()
        vpp_rfc2544_profile.stop_traffic(traffic_generator=mock_generator)
        mock_generator.client.stop.assert_called_once()
        mock_generator.client.reset.assert_called_once()
        mock_generator.client.remove_all_streams.assert_called_once()

    def test_execute_traffic(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        vpp_rfc2544_profile.init_queue(mock.MagicMock())
        vpp_rfc2544_profile.params = {
            'downlink_0': 'profile1',
            'uplink_0': 'profile2'}
        mock_generator = mock.MagicMock()
        mock_generator.networks = {
            'downlink_0': ['xe0', 'xe1'],
            'uplink_0': ['xe2', 'xe3'],
            'uplink_1': ['xe2', 'xe3']}
        mock_generator.port_num.side_effect = [10, 20, 30, 40]
        mock_generator.rfc2544_helper.correlated_traffic = False

        with mock.patch.object(vpp_rfc2544_profile, 'create_profile') as \
                mock_create_profile:
            vpp_rfc2544_profile.execute_traffic(
                traffic_generator=mock_generator)
        mock_create_profile.assert_has_calls([
            mock.call('profile1', 10),
            mock.call('profile1', 20),
            mock.call('profile2', 30),
            mock.call('profile2', 40)])
        mock_generator.client.add_streams.assert_has_calls([
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[30]),
            mock.call(mock.ANY, ports=[40])])

    def test_execute_traffic_correlated_traffic(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        vpp_rfc2544_profile.init_queue(mock.MagicMock())
        vpp_rfc2544_profile.params = {
            'downlink_0': 'profile1',
            'uplink_0': 'profile2'}
        mock_generator = mock.MagicMock()
        mock_generator.networks = {
            'downlink_0': ['xe0', 'xe1'],
            'uplink_0': ['xe2', 'xe3']}
        mock_generator.port_num.side_effect = [10, 20, 30, 40]
        mock_generator.rfc2544_helper.correlated_traffic = True

        with mock.patch.object(vpp_rfc2544_profile, 'create_profile') as \
                mock_create_profile:
            vpp_rfc2544_profile.execute_traffic(
                traffic_generator=mock_generator)
        mock_create_profile.assert_has_calls([
            mock.call('profile2', 10),
            mock.call('profile2', 20)])
        mock_generator.client.add_streams.assert_has_calls([
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20])])

    def test_execute_traffic_max_rate(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE_MAX_RATE)
        vpp_rfc2544_profile.init_queue(mock.MagicMock())
        vpp_rfc2544_profile.pkt_size = 64
        vpp_rfc2544_profile.params = {
            'downlink_0': 'profile1',
            'uplink_0': 'profile2'}
        mock_generator = mock.MagicMock()
        mock_generator.networks = {
            'downlink_0': ['xe0', 'xe1'],
            'uplink_0': ['xe2', 'xe3']}
        mock_generator.port_num.side_effect = [10, 20, 30, 40]
        mock_generator.rfc2544_helper.correlated_traffic = False

        with mock.patch.object(vpp_rfc2544_profile, 'create_profile') as \
                mock_create_profile:
            vpp_rfc2544_profile.execute_traffic(
                traffic_generator=mock_generator)
        mock_create_profile.assert_has_calls([
            mock.call('profile1', 10),
            mock.call('profile1', 20),
            mock.call('profile2', 30),
            mock.call('profile2', 40)])
        mock_generator.client.add_streams.assert_has_calls([
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[30]),
            mock.call(mock.ANY, ports=[40])])

    @mock.patch.object(trex_stl_streams, 'STLProfile')
    def test_create_profile(self, mock_stl_profile):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        port = mock.ANY
        profile_data = {'packetid_1': {'outer_l2': {'framesize': 'imix_info'}}}
        with mock.patch.object(vpp_rfc2544_profile, 'calculate_frame_size') as \
                mock_calculate_frame_size, \
                mock.patch.object(vpp_rfc2544_profile, '_create_imix_data') as \
                        mock_create_imix, \
                mock.patch.object(vpp_rfc2544_profile, '_create_vm') as \
                        mock_create_vm, \
                mock.patch.object(vpp_rfc2544_profile,
                                  '_create_single_stream') as \
                        mock_create_single_stream:
            mock_calculate_frame_size.return_value = 64, 100
            mock_create_imix.return_value = 'imix_data'
            mock_create_single_stream.return_value = ['stream1']
            vpp_rfc2544_profile.create_profile(profile_data, port)

        mock_create_imix.assert_called_once_with('imix_info')
        mock_create_vm.assert_called_once_with(
            {'outer_l2': {'framesize': 'imix_info'}})
        mock_create_single_stream.assert_called_once_with(port, 'imix_data',
                                                          100)
        mock_stl_profile.assert_called_once_with(['stream1'])

    @mock.patch.object(trex_stl_streams, 'STLProfile')
    def test_create_profile_max_rate(self, mock_stl_profile):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE_MAX_RATE)
        port = mock.ANY
        profile_data = {'packetid_1': {'outer_l2': {'framesize': 'imix_info'}}}
        with mock.patch.object(vpp_rfc2544_profile, 'calculate_frame_size') as \
                mock_calculate_frame_size, \
                mock.patch.object(vpp_rfc2544_profile, '_create_imix_data') as \
                        mock_create_imix, \
                mock.patch.object(vpp_rfc2544_profile, '_create_vm') as \
                        mock_create_vm, \
                mock.patch.object(vpp_rfc2544_profile,
                                  '_create_single_stream') as \
                        mock_create_single_stream:
            mock_calculate_frame_size.return_value = 64, 100
            mock_create_imix.return_value = 'imix_data'
            mock_create_single_stream.return_value = ['stream1']
            vpp_rfc2544_profile.create_profile(profile_data, port)

        mock_create_imix.assert_called_once_with('imix_info', 'mode_DIP')
        mock_create_vm.assert_called_once_with(
            {'outer_l2': {'framesize': 'imix_info'}})
        mock_create_single_stream.assert_called_once_with(port, 'imix_data',
                                                          100)
        mock_stl_profile.assert_called_once_with(['stream1'])

    def test__create_imix_data_mode_DIP(self):
        rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(self.TRAFFIC_PROFILE)
        data = {'64B': 50, '128B': 50}
        self.assertEqual(
            {'64': 50.0, '128': 50.0},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_PACKETS))
        data = {'64B': 1, '128b': 3}
        self.assertEqual(
            {'64': 25.0, '128': 75.0},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_PACKETS))
        data = {}
        self.assertEqual(
            {},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_PACKETS))

    def test__create_imix_data_mode_DIB(self):
        rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(self.TRAFFIC_PROFILE)
        data = {'64B': 25, '128B': 25, '512B': 25, '1518B': 25}
        byte_total = 64 * 25 + 128 * 25 + 512 * 25 + 1518 * 25
        self.assertEqual(
            {'64': 64 * 25.0 * 100 / byte_total,
             '128': 128 * 25.0 * 100 / byte_total,
             '512': 512 * 25.0 * 100 / byte_total,
             '1518': 1518 * 25.0 * 100 / byte_total},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_BYTES))
        data = {}
        self.assertEqual(
            {},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_BYTES))
        data = {'64B': 100}
        self.assertEqual(
            {'64': 100.0},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_BYTES))

    def test__create_vm(self):
        packet = {'outer_l2': 'l2_definition'}
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        with mock.patch.object(vpp_rfc2544_profile, '_set_outer_l2_fields') as \
                mock_l2_fileds:
            vpp_rfc2544_profile._create_vm(packet)
        mock_l2_fileds.assert_called_once_with('l2_definition')

    @mock.patch.object(trex_stl_packet_builder_scapy, 'STLPktBuilder',
                       return_value='packet')
    def test__create_single_packet(self, mock_pktbuilder):
        size = 128
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        vpp_rfc2544_profile.ether_packet = mock.MagicMock()
        vpp_rfc2544_profile.ip_packet = mock.MagicMock()
        vpp_rfc2544_profile.udp_packet = mock.MagicMock()
        vpp_rfc2544_profile.trex_vm = 'trex_vm'
        # base_pkt = (
        #        vpp_rfc2544_profile.ether_packet / vpp_rfc2544_profile.ip_packet /
        #        vpp_rfc2544_profile.udp_packet)
        # pad = (size - len(base_pkt)) * 'x'
        output = vpp_rfc2544_profile._create_single_packet(size=size)
        self.assertEqual(mock_pktbuilder.call_count, 2)
        # mock_pktbuilder.assert_called_once_with(pkt=base_pkt / pad,
        #                                        vm='trex_vm')
        self.assertEqual(output, ('packet', 'packet'))

    def test__set_outer_l3v4_fields(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        outer_l3v4 = self.PROFILE[
            tp_base.TrafficProfile.UPLINK]['ipv4']['outer_l3v4']
        outer_l3v4['proto'] = 'tcp'
        self.assertIsNone(
            vpp_rfc2544_profile._set_outer_l3v4_fields(outer_l3v4))

    @mock.patch.object(trex_stl_streams, 'STLFlowLatencyStats')
    @mock.patch.object(trex_stl_streams, 'STLTXCont')
    @mock.patch.object(trex_stl_client, 'STLStream')
    def test__create_single_stream(self, mock_stream, mock_txcont,
                                   mock_latency):
        imix_data = {'64': 25, '512': 75}
        mock_stream.side_effect = ['stream1', 'stream2', 'stream3', 'stream4']
        mock_txcont.side_effect = ['txcont1', 'txcont2', 'txcont3', 'txcont4']
        mock_latency.side_effect = ['latency1', 'latency2']
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        vpp_rfc2544_profile.port_pg_id = rfc2544.PortPgIDMap()
        vpp_rfc2544_profile.port_pg_id.add_port(10)
        with mock.patch.object(vpp_rfc2544_profile, '_create_single_packet') as \
                mock_create_single_packet:
            mock_create_single_packet.return_value = 64, 100
            output = vpp_rfc2544_profile._create_single_stream(10, imix_data,
                                                               100, 0.0)
        self.assertEqual(['stream1', 'stream2', 'stream3', 'stream4'], output)
        mock_latency.assert_has_calls([
            mock.call(pg_id=1), mock.call(pg_id=2)])
        mock_txcont.assert_has_calls([
            mock.call(percentage=25 * 100 / 100),
            mock.call(percentage=75 * 100 / 100)], any_order=True)

    @mock.patch.object(trex_stl_streams, 'STLFlowLatencyStats')
    @mock.patch.object(trex_stl_streams, 'STLTXCont')
    @mock.patch.object(trex_stl_client, 'STLStream')
    def test__create_single_stream_max_rate(self, mock_stream, mock_txcont,
                                            mock_latency):
        imix_data = {'64': 25, '512': 75}
        mock_stream.side_effect = ['stream1', 'stream2', 'stream3', 'stream4']
        mock_txcont.side_effect = ['txcont1', 'txcont2', 'txcont3', 'txcont4']
        mock_latency.side_effect = ['latency1', 'latency2']
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE_MAX_RATE)
        vpp_rfc2544_profile.pkt_size = 64
        vpp_rfc2544_profile.port_pg_id = rfc2544.PortPgIDMap()
        vpp_rfc2544_profile.port_pg_id.add_port(1)
        with mock.patch.object(vpp_rfc2544_profile, '_create_single_packet') as \
                mock_create_single_packet:
            mock_create_single_packet.return_value = 64, 100
            output = vpp_rfc2544_profile._create_single_stream(1, imix_data,
                                                               100, 0.0)
        self.assertEqual(['stream1', 'stream2', 'stream3', 'stream4'], output)
        mock_latency.assert_has_calls([
            mock.call(pg_id=1), mock.call(pg_id=2)])
        mock_txcont.assert_has_calls([
            mock.call(pps=int(25 * 100 / 100)),
            mock.call(pps=int(75 * 100 / 100))], any_order=True)

    @mock.patch.object(trex_stl_streams, 'STLFlowLatencyStats')
    @mock.patch.object(trex_stl_streams, 'STLTXCont')
    @mock.patch.object(trex_stl_client, 'STLStream')
    def test__create_single_stream_mlr_search(self, mock_stream, mock_txcont,
                                              mock_latency):
        imix_data = {'64': 25, '512': 75}
        mock_stream.side_effect = ['stream1', 'stream2', 'stream3', 'stream4']
        mock_txcont.side_effect = ['txcont1', 'txcont2', 'txcont3', 'txcont4']
        mock_latency.side_effect = ['latency1', 'latency2']
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        vpp_rfc2544_profile.max_rate = 14880000
        vpp_rfc2544_profile.port_pg_id = rfc2544.PortPgIDMap()
        vpp_rfc2544_profile.port_pg_id.add_port(10)
        with mock.patch.object(vpp_rfc2544_profile, '_create_single_packet') as \
                mock_create_single_packet:
            mock_create_single_packet.return_value = 64, 100
            output = vpp_rfc2544_profile._create_single_stream(10, imix_data,
                                                               100, 0.0)
        self.assertEqual(['stream1', 'stream2', 'stream3', 'stream4'], output)
        mock_latency.assert_has_calls([
            mock.call(pg_id=1), mock.call(pg_id=2)])
        mock_txcont.assert_has_calls([
            mock.call(pps=25 * 100 / 100),
            mock.call(pps=75 * 100 / 100)], any_order=True)

    def test_binary_search_with_optimized(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        vpp_rfc2544_profile.pkt_size = 64
        vpp_rfc2544_profile.init_queue(mock.MagicMock())
        mock_generator = mock.MagicMock()
        mock_generator.vnfd_helper.interfaces = [
            {"name": "xe0"}, {"name": "xe0"}
        ]

        vpp_rfc2544_profile.ports = [0, 1]
        vpp_rfc2544_profile.port_pg_id = PortPgIDMap()
        vpp_rfc2544_profile.port_pg_id.add_port(0)
        vpp_rfc2544_profile.port_pg_id.add_port(1)
        vpp_rfc2544_profile.profiles = mock.MagicMock()
        vpp_rfc2544_profile.test_data = mock.MagicMock()
        vpp_rfc2544_profile.queue = mock.MagicMock()

        with mock.patch.object(MultipleLossRatioSearch, 'measure') as \
                mock_measure, \
                mock.patch.object(MultipleLossRatioSearch, 'ndrpdr') as \
                        mock_ndrpdr:
            measured_low = ReceiveRateMeasurement(1, 14880000, 14879927, 0)
            measured_high = ReceiveRateMeasurement(1, 14880000, 14879927, 0)
            measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            starting_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
            starting_result = NdrPdrResult(starting_interval,
                                           starting_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock_ndrpdr.return_value = MultipleLossRatioSearch.ProgressState(
                starting_result, 2, 30, 0.005, 0.0,
                4857361, 4977343)

            result_samples = vpp_rfc2544_profile.binary_search_with_optimized(
                traffic_generator=mock_generator, duration=30,
                timeout=720,
                test_data={})

        expected = {'Result_NDR_LOWER': {'bandwidth_total_Gbps': 9.999310944,
                                         'rate_total_pps': 14879927.0},
                    'Result_NDR_UPPER': {'bandwidth_total_Gbps': 9.999310944,
                                         'rate_total_pps': 14879927.0},
                    'Result_NDR_packets_lost': {'packet_loss_ratio': 0.0,
                                                'packets_lost': 0.0},
                    'Result_PDR_LOWER': {'bandwidth_total_Gbps': 9.999310944,
                                         'rate_total_pps': 14879927.0},
                    'Result_PDR_UPPER': {'bandwidth_total_Gbps': 9.999310944,
                                         'rate_total_pps': 14879927.0},
                    'Result_PDR_packets_lost': {'packet_loss_ratio': 0.0,
                                                'packets_lost': 0.0},
                    'Result_stream0_NDR_LOWER': {'avg_latency': 3081.0,
                                                 'max_latency': 3962.0,
                                                 'min_latency': 1000.0},
                    'Result_stream0_PDR_LOWER': {'avg_latency': 3081.0,
                                                 'max_latency': 3962.0,
                                                 'min_latency': 1000.0},
                    'Result_stream1_NDR_LOWER': {'avg_latency': 3149.0,
                                                 'max_latency': 3730.0,
                                                 'min_latency': 500.0},
                    'Result_stream1_PDR_LOWER': {'avg_latency': 3149.0,
                                                 'max_latency': 3730.0,
                                                 'min_latency': 500.0}}
        self.assertEqual(expected, result_samples)

    def test_binary_search(self):
        vpp_rfc2544_profile = vpp_rfc2544.VppRFC2544Profile(
            self.TRAFFIC_PROFILE)
        vpp_rfc2544_profile.pkt_size = 64
        vpp_rfc2544_profile.init_queue(mock.MagicMock())
        mock_generator = mock.MagicMock()
        mock_generator.vnfd_helper.interfaces = [
            {"name": "xe0"}, {"name": "xe1"}
        ]
        stats = {
            "0": {
                "ibytes": 55549120,
                "ierrors": 0,
                "ipackets": 867955,
                "obytes": 55549696,
                "oerrors": 0,
                "opackets": 867964,
                "rx_bps": 104339032.0,
                "rx_bps_L1": 136944984.0,
                "rx_pps": 203787.2,
                "rx_util": 1.36944984,
                "tx_bps": 134126008.0,
                "tx_bps_L1": 176040392.0,
                "tx_pps": 261964.9,
                "tx_util": 1.7604039200000001
            },
            "1": {
                "ibytes": 55549696,
                "ierrors": 0,
                "ipackets": 867964,
                "obytes": 55549120,
                "oerrors": 0,
                "opackets": 867955,
                "rx_bps": 134119648.0,
                "rx_bps_L1": 176032032.0,
                "rx_pps": 261952.4,
                "rx_util": 1.76032032,
                "tx_bps": 104338192.0,
                "tx_bps_L1": 136943872.0,
                "tx_pps": 203785.5,
                "tx_util": 1.36943872
            },
            "flow_stats": {
                "1": {
                    "rx_bps": {
                        "0": 0,
                        "1": 0,
                        "total": 0
                    },
                    "rx_bps_l1": {
                        "0": 0.0,
                        "1": 0.0,
                        "total": 0.0
                    },
                    "rx_bytes": {
                        "0": 6400,
                        "1": 0,
                        "total": 6400
                    },
                    "rx_pkts": {
                        "0": 100,
                        "1": 0,
                        "total": 100
                    },
                    "rx_pps": {
                        "0": 0,
                        "1": 0,
                        "total": 0
                    },
                    "tx_bps": {
                        "0": 0,
                        "1": 0,
                        "total": 0
                    },
                    "tx_bps_l1": {
                        "0": 0.0,
                        "1": 0.0,
                        "total": 0.0
                    },
                    "tx_bytes": {
                        "0": 0,
                        "1": 6400,
                        "total": 6400
                    },
                    "tx_pkts": {
                        "0": 0,
                        "1": 100,
                        "total": 100
                    },
                    "tx_pps": {
                        "0": 0,
                        "1": 0,
                        "total": 0
                    }
                },
                "2": {
                    "rx_bps": {
                        "0": 0,
                        "1": 0,
                        "total": 0
                    },
                    "rx_bps_l1": {
                        "0": 0.0,
                        "1": 0.0,
                        "total": 0.0
                    },
                    "rx_bytes": {
                        "0": 0,
                        "1": 6464,
                        "total": 6464
                    },
                    "rx_pkts": {
                        "0": 0,
                        "1": 101,
                        "total": 101
                    },
                    "rx_pps": {
                        "0": 0,
                        "1": 0,
                        "total": 0
                    },
                    "tx_bps": {
                        "0": 0,
                        "1": 0,
                        "total": 0
                    },
                    "tx_bps_l1": {
                        "0": 0.0,
                        "1": 0.0,
                        "total": 0.0
                    },
                    "tx_bytes": {
                        "0": 6464,
                        "1": 0,
                        "total": 6464
                    },
                    "tx_pkts": {
                        "0": 101,
                        "1": 0,
                        "total": 101
                    },
                    "tx_pps": {
                        "0": 0,
                        "1": 0,
                        "total": 0
                    }
                },
                "global": {
                    "rx_err": {
                        "0": 0,
                        "1": 0
                    },
                    "tx_err": {
                        "0": 0,
                        "1": 0
                    }
                }
            },
            "global": {
                "bw_per_core": 45.6,
                "cpu_util": 0.1494,
                "queue_full": 0,
                "rx_bps": 238458672.0,
                "rx_cpu_util": 4.751e-05,
                "rx_drop_bps": 0.0,
                "rx_pps": 465739.6,
                "tx_bps": 238464208.0,
                "tx_pps": 465750.4
            },
            "latency": {
                "1": {
                    "err_cntrs": {
                        "dropped": 0,
                        "dup": 0,
                        "out_of_order": 0,
                        "seq_too_high": 0,
                        "seq_too_low": 0
                    },
                    "latency": {
                        "average": 63.375,
                        "histogram": {
                            "20": 1,
                            "30": 18,
                            "40": 12,
                            "50": 10,
                            "60": 12,
                            "70": 11,
                            "80": 6,
                            "90": 10,
                            "100": 20
                        },
                        "jitter": 23,
                        "last_max": 122,
                        "total_max": 123,
                        "total_min": 20
                    }
                },
                "2": {
                    "err_cntrs": {
                        "dropped": 0,
                        "dup": 0,
                        "out_of_order": 0,
                        "seq_too_high": 0,
                        "seq_too_low": 0
                    },
                    "latency": {
                        "average": 74,
                        "histogram": {
                            "60": 20,
                            "70": 10,
                            "80": 3,
                            "90": 4,
                            "100": 64
                        },
                        "jitter": 6,
                        "last_max": 83,
                        "total_max": 135,
                        "total_min": 60
                    }
                },
                "global": {
                    "bad_hdr": 0,
                    "old_flow": 0
                }
            },
            "total": {
                "ibytes": 111098816,
                "ierrors": 0,
                "ipackets": 1735919,
                "obytes": 111098816,
                "oerrors": 0,
                "opackets": 1735919,
                "rx_bps": 238458680.0,
                "rx_bps_L1": 312977016.0,
                "rx_pps": 465739.6,
                "rx_util": 3.1297701599999996,
                "tx_bps": 238464200.0,
                "tx_bps_L1": 312984264.0,
                "tx_pps": 465750.4,
                "tx_util": 3.12984264
            }
        }
        samples = {
            "xe0": {
                "in_packets": 867955,
                "latency": {
                    "2": {
                        "avg_latency": 74.0,
                        "max_latency": 135.0,
                        "min_latency": 60.0
                    }
                },
                "out_packets": 867964,
                "rx_throughput_bps": 104339032.0,
                "rx_throughput_fps": 203787.2,
                "tx_throughput_bps": 134126008.0,
                "tx_throughput_fps": 261964.9
            },
            "xe1": {
                "in_packets": 867964,
                "latency": {
                    "1": {
                        "avg_latency": 63.375,
                        "max_latency": 123.0,
                        "min_latency": 20.0
                    }
                },
                "out_packets": 867955,
                "rx_throughput_bps": 134119648.0,
                "rx_throughput_fps": 261952.4,
                "tx_throughput_bps": 104338192.0,
                "tx_throughput_fps": 203785.5
            }
        }

        mock_generator.loss = 0
        mock_generator.sent = 2169700
        mock_generator.send_traffic_on_tg = mock.Mock(return_value=stats)
        mock_generator.generate_samples = mock.Mock(return_value=samples)

        result_samples = vpp_rfc2544_profile.binary_search(
            traffic_generator=mock_generator, duration=30,
            tolerance_value=0.005,
            test_data={})

        expected = {'Result_theor_max_throughput': 134126008.0,
                    'xe0': {'Result_Actual_throughput': 104339032.0},
                    'xe1': {'Result_Actual_throughput': 134119648.0}}
        self.assertEqual(expected, result_samples)
