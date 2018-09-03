# Copyright (c) 2018 Intel Corporation
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

import copy
import unittest

from yardstick.network_services.traffic_profile import landslide_profile

TP_CONFIG = {
    'schema': "nsb:traffic_profile:0.1",
    'name': 'LandslideProfile',
    'description': 'Spirent Landslide traffic profile (Data Message Flow)',
    'traffic_profile': {
        'traffic_type': 'LandslideProfile'
    },
    'dmf_config': {
        'dmf': {
            'library': 'test',
            'name': 'Fireball UDP',
            'description': "Basic data flow using UDP/IP (Fireball DMF)",
            'keywords': 'UDP ',
            'dataProtocol': 'fb_udp',
            'burstCount': 1,
            'clientPort': {
                'clientPort': 2002,
                'isClientPortRange': 'false'
            },
            'serverPort': 2003,
            'connection': {
                'initiatingSide': 'Client',
                'disconnectSide': 'Client',
                'underlyingProtocol': 'none',
                'persistentConnection': 'false'
            },
            'protocolId': 0,
            'persistentConnection': 'false',
            'transactionRate': 8.0,
            'transactions': {
                'totalTransactions': 0,
                'retries': 0,
                'dataResponseTime': 60000,
                'packetSize': 64
            },
            'segment': {
                'segmentSize': 64000,
                'maxSegmentSize': 0
            },
            'size': {
                'sizeDistribution': 'Fixed',
                'sizeDeviation': 10
            },
            'interval': {
                'intervalDistribution': 'Fixed',
                'intervalDeviation': 10
            },
            'ipHeader': {
                'typeOfService': 0,
                'timeToLive': 64
            },
            'tcpConnection': {
                'force3Way': 'false',
                'fixedRetryTime': 0,
                'maxPacketsToForceAck': 0
            },
            'tcp': {
                'windowSize': 32768,
                'windowScaling': -1,
                'disableFinAckWait': 'false'
            },
            'disconnectType': 'FIN',
            'slowStart': 'false',
            'connectOnly': 'false',
            'vtag': {
                'VTagMask': '0x0',
                'VTagValue': '0x0'
            },
            'sctpPayloadProtocolId': 0,
            'billingIncludeSyn': 'true',
            'billingIncludeSubflow': 'true',
            'billingRecordPerTransaction': 'false',
            'tcpPush': 'false',
            'hostDataExpansionRatio': 1
        }
    }
}
DMF_OPTIONS = {
    'dmf': {
        'transactionRate': 5,
        'packetSize': 512,
        'burstCount': 1
    }
}


class TestLandslideProfile(unittest.TestCase):

    def test___init__(self):
        ls_traffic_profile = landslide_profile.LandslideProfile(TP_CONFIG)
        self.assertListEqual([TP_CONFIG["dmf_config"]],
                             ls_traffic_profile.dmf_config)

    def test___init__config_not_a_dict(self):
        _tp_config = copy.deepcopy(TP_CONFIG)
        _tp_config['dmf_config'] = [_tp_config['dmf_config']]
        ls_traffic_profile = landslide_profile.LandslideProfile(_tp_config)
        self.assertListEqual(_tp_config['dmf_config'],
                             ls_traffic_profile.dmf_config)

    def test_execute(self):
        ls_traffic_profile = landslide_profile.LandslideProfile(TP_CONFIG)
        self.assertIsNone(ls_traffic_profile.execute(None))

    def test_update_dmf_options_dict(self):
        ls_traffic_profile = landslide_profile.LandslideProfile(TP_CONFIG)
        ls_traffic_profile.update_dmf(DMF_OPTIONS)
        self.assertDictContainsSubset(DMF_OPTIONS['dmf'],
                                      ls_traffic_profile.dmf_config[0])

    def test_update_dmf_options_list(self):
        ls_traffic_profile = landslide_profile.LandslideProfile(TP_CONFIG)
        _dmf_options = copy.deepcopy(DMF_OPTIONS)
        _dmf_options['dmf'] = [_dmf_options['dmf']]
        ls_traffic_profile.update_dmf(_dmf_options)
        self.assertTrue(all([x in ls_traffic_profile.dmf_config[0]
                             for x in DMF_OPTIONS['dmf']]))
