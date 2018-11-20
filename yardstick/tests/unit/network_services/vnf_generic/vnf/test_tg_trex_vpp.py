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

import unittest
from multiprocessing import Process

import mock
from trex_stl_lib.trex_stl_exceptions import STLError

from yardstick.benchmark.contexts import base as ctx_base
from yardstick.network_services.traffic_profile import base as tp_base
from yardstick.network_services.traffic_profile import rfc2544
from yardstick.network_services.vnf_generic.vnf import base, sample_vnf, \
    tg_trex_vpp
from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import \
    mock_ssh


class TestTrexVppResourceHelper(unittest.TestCase):
    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,  # pps
            "flow_number": 10,
            "frame_size": 64
        },
    }

    def test_fmt_latency(self):
        mock_setup_helper = mock.Mock()
        vpp_rfc = tg_trex_vpp.TrexVppResourceHelper(mock_setup_helper)
        self.assertEqual('10/90/489', vpp_rfc.fmt_latency(10, 90, 489))

    def test_fmt_latency_error(self):
        mock_setup_helper = mock.Mock()
        vpp_rfc = tg_trex_vpp.TrexVppResourceHelper(mock_setup_helper)
        self.assertEqual('-1/-1/-1', vpp_rfc.fmt_latency('err', 'err', 'err'))

    def test_generate_samples(self):
        stats = {
            0: {
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
            1: {
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
                1: {
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
                2: {
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
                1: {
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
                2: {
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
        expected = {
            "xe0": {
                "in_packets": 867955,
                "latency": {
                    2: {
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
                    1: {
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
        mock_setup_helper = mock.Mock()
        vpp_rfc = tg_trex_vpp.TrexVppResourceHelper(mock_setup_helper)
        vpp_rfc.vnfd_helper = base.VnfdHelper(TestTrexTrafficGenVpp.VNFD_0)
        port_pg_id = rfc2544.PortPgIDMap()
        port_pg_id.add_port(1)
        port_pg_id.increase_pg_id()
        port_pg_id.add_port(0)
        port_pg_id.increase_pg_id()
        self.assertEqual(expected,
                         vpp_rfc.generate_samples(stats, [0, 1], port_pg_id,
                                                  True))

    def test_generate_samples_error(self):
        stats = {
            0: {
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
            1: {
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
                1: {
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
                2: {
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
                1: {
                    "err_cntrs": {
                        "dropped": 0,
                        "dup": 0,
                        "out_of_order": 0,
                        "seq_too_high": 0,
                        "seq_too_low": 0
                    },
                    "latency": {
                        "average": "err",
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
                        "total_max": "err",
                        "total_min": "err"
                    }
                },
                2: {
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
        expected = {'xe0': {'in_packets': 867955,
                            'latency': {2: {'avg_latency': 74.0,
                                            'max_latency': 135.0,
                                            'min_latency': 60.0}},
                            'out_packets': 867964,
                            'rx_throughput_bps': 104339032.0,
                            'rx_throughput_fps': 203787.2,
                            'tx_throughput_bps': 134126008.0,
                            'tx_throughput_fps': 261964.9},
                    'xe1': {'in_packets': 867964,
                            'latency': {1: {'avg_latency': -1.0,
                                            'max_latency': -1.0,
                                            'min_latency': -1.0}},
                            'out_packets': 867955,
                            'rx_throughput_bps': 134119648.0,
                            'rx_throughput_fps': 261952.4,
                            'tx_throughput_bps': 104338192.0,
                            'tx_throughput_fps': 203785.5}}
        mock_setup_helper = mock.Mock()
        vpp_rfc = tg_trex_vpp.TrexVppResourceHelper(mock_setup_helper)
        vpp_rfc.vnfd_helper = base.VnfdHelper(TestTrexTrafficGenVpp.VNFD_0)
        vpp_rfc.get_stats = mock.Mock()
        vpp_rfc.get_stats.return_value = stats
        port_pg_id = rfc2544.PortPgIDMap()
        port_pg_id.add_port(1)
        port_pg_id.increase_pg_id()
        port_pg_id.add_port(0)
        port_pg_id.increase_pg_id()
        self.assertEqual(expected,
                         vpp_rfc.generate_samples(stats=None, ports=[0, 1],
                                                  port_pg_id=port_pg_id,
                                                  latency=True))

    def test__run_traffic_once(self):
        mock_setup_helper = mock.Mock()
        mock_traffic_profile = mock.Mock()
        vpp_rfc = tg_trex_vpp.TrexVppResourceHelper(mock_setup_helper)
        vpp_rfc.TRANSIENT_PERIOD = 0
        vpp_rfc.rfc2544_helper = mock.Mock()

        self.assertTrue(vpp_rfc._run_traffic_once(mock_traffic_profile))
        mock_traffic_profile.execute_traffic.assert_called_once_with(vpp_rfc)

    def test_run_traffic(self):
        mock_traffic_profile = mock.Mock(autospec=tp_base.TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE
        mock_setup_helper = mock.Mock()
        vpp_rfc = tg_trex_vpp.TrexVppResourceHelper(mock_setup_helper)
        vpp_rfc.ssh_helper = mock.Mock()
        vpp_rfc.ssh_helper.run = mock.Mock()
        vpp_rfc._traffic_runner = mock.Mock(return_value=0)
        vpp_rfc._build_ports = mock.Mock()
        vpp_rfc._connect = mock.Mock()
        vpp_rfc.run_traffic(mock_traffic_profile)

    def test_send_traffic_on_tg(self):
        stats = {
            0: {
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
            1: {
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
                1: {
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
                2: {
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
                1: {
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
                2: {
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
        mock_setup_helper = mock.Mock()
        vpp_rfc = tg_trex_vpp.TrexVppResourceHelper(mock_setup_helper)
        vpp_rfc.vnfd_helper = base.VnfdHelper(TestTrexTrafficGenVpp.VNFD_0)
        vpp_rfc.client = mock.Mock()
        vpp_rfc.client.get_warnings.return_value = 'get_warnings'
        vpp_rfc.client.get_stats.return_value = stats
        port_pg_id = rfc2544.PortPgIDMap()
        port_pg_id.add_port(1)
        port_pg_id.increase_pg_id()
        port_pg_id.add_port(0)
        port_pg_id.increase_pg_id()
        self.assertEqual(stats,
                         vpp_rfc.send_traffic_on_tg([0, 1], port_pg_id, 30,
                                                    10000, True))

    def test_send_traffic_on_tg_error(self):
        mock_setup_helper = mock.Mock()
        vpp_rfc = tg_trex_vpp.TrexVppResourceHelper(mock_setup_helper)
        vpp_rfc.vnfd_helper = base.VnfdHelper(TestTrexTrafficGenVpp.VNFD_0)
        vpp_rfc.client = mock.Mock()
        vpp_rfc.client.get_warnings.return_value = 'get_warnings'
        vpp_rfc.client.get_stats.side_effect = STLError('get_stats')
        vpp_rfc.client.wait_on_traffic.side_effect = STLError(
            'wait_on_traffic')
        port_pg_id = rfc2544.PortPgIDMap()
        port_pg_id.add_port(1)
        port_pg_id.increase_pg_id()
        port_pg_id.add_port(0)
        port_pg_id.increase_pg_id()
        # with self.assertRaises(RuntimeError) as raised:
        vpp_rfc.send_traffic_on_tg([0, 1], port_pg_id, 30, 10000, True)
        # self.assertIn('TRex stateless runtime error', str(raised.exception))


class TestTrexTrafficGenVpp(unittest.TestCase):
    VNFD_0 = {
        "benchmark": {
            "kpi": [
                "rx_throughput_fps",
                "tx_throughput_fps",
                "tx_throughput_mbps",
                "rx_throughput_mbps",
                "in_packets",
                "out_packets",
                "min_latency",
                "max_latency",
                "avg_latency"
            ]
        },
        "description": "TRex stateless traffic verifier",
        "id": "TrexTrafficGenVpp",
        "mgmt-interface": {
            "ip": "10.10.10.10",
            "password": "r00t",
            "user": "root",
            "vdu-id": "trexgen-baremetal"
        },
        "name": "trexverifier",
        "short-name": "trexverifier",
        "vdu": [
            {
                "description": "TRex stateless traffic verifier",
                "external-interface": [
                    {
                        "name": "xe0",
                        "virtual-interface": {
                            "dpdk_port_num": 0,
                            "driver": "igb_uio",
                            "dst_ip": "192.168.100.2",
                            "dst_mac": "90:e2:ba:7c:41:a8",
                            "ifname": "xe0",
                            "local_ip": "192.168.100.1",
                            "local_mac": "90:e2:ba:7c:30:e8",
                            "netmask": "255.255.255.0",
                            "network": {},
                            "node_name": "tg__0",
                            "peer_ifname": "xe0",
                            "peer_intf": {
                                "driver": "igb_uio",
                                "dst_ip": "192.168.100.1",
                                "dst_mac": "90:e2:ba:7c:30:e8",
                                "ifname": "xe0",
                                "local_ip": "192.168.100.2",
                                "local_mac": "90:e2:ba:7c:41:a8",
                                "netmask": "255.255.255.0",
                                "network": {},
                                "node_name": "vnf__0",
                                "peer_ifname": "xe0",
                                "peer_name": "tg__0",
                                "vld_id": "uplink_0",
                                "vpci": "0000:ff:06.0"
                            },
                            "peer_name": "vnf__0",
                            "vld_id": "uplink_0",
                            "vpci": "0000:81:00.0"
                        },
                        "vnfd-connection-point-ref": "xe0"
                    },
                    {
                        "name": "xe1",
                        "virtual-interface": {
                            "dpdk_port_num": 1,
                            "driver": "igb_uio",
                            "dst_ip": "192.168.101.2",
                            "dst_mac": "90:e2:ba:7c:41:a9",
                            "ifname": "xe1",
                            "local_ip": "192.168.101.1",
                            "local_mac": "90:e2:ba:7c:30:e9",
                            "netmask": "255.255.255.0",
                            "network": {},
                            "node_name": "tg__0",
                            "peer_ifname": "xe0",
                            "peer_intf": {
                                "driver": "igb_uio",
                                "dst_ip": "192.168.101.1",
                                "dst_mac": "90:e2:ba:7c:30:e9",
                                "ifname": "xe0",
                                "local_ip": "192.168.101.2",
                                "local_mac": "90:e2:ba:7c:41:a9",
                                "netmask": "255.255.255.0",
                                "network": {},
                                "node_name": "vnf__1",
                                "peer_ifname": "xe1",
                                "peer_name": "tg__0",
                                "vld_id": "downlink_0",
                                "vpci": "0000:ff:06.0"
                            },
                            "peer_name": "vnf__1",
                            "vld_id": "downlink_0",
                            "vpci": "0000:81:00.1"
                        },
                        "vnfd-connection-point-ref": "xe1"
                    }
                ],
                "id": "trexgen-baremetal",
                "name": "trexgen-baremetal"
            }
        ]
    }

    VNFD = {
        'vnfd:vnfd-catalog': {
            'vnfd': [
                VNFD_0,
            ],
        },
    }

    def setUp(self):
        self._mock_ssh_helper = mock.patch.object(sample_vnf, 'VnfSshHelper')
        self.mock_ssh_helper = self._mock_ssh_helper.start()
        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_ssh_helper.stop()

    def test___init__(self):
        trex_traffic_gen = tg_trex_vpp.TrexTrafficGenVpp(
            'tg0', self.VNFD_0)
        self.assertIsNotNone(
            trex_traffic_gen.resource_helper._terminated.value)

    def test__check_status(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex_vpp.TrexTrafficGenVpp('tg0', vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper.execute.return_value = 0, '', ''
        trex_traffic_gen.scenario_helper.scenario_cfg = {}
        self.assertEqual(0, trex_traffic_gen._check_status())

    def test__start_server(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex_vpp.TrexTrafficGenVpp('tg0', vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.scenario_helper.scenario_cfg = {}
        self.assertIsNone(trex_traffic_gen._start_server())

    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server',
                       return_value='mock_node')
    def test_collect_kpi(self, *args):
        trex_traffic_gen = tg_trex_vpp.TrexTrafficGenVpp(
            'tg0', self.VNFD_0)
        trex_traffic_gen.scenario_helper.scenario_cfg = {
            'nodes': {trex_traffic_gen.name: "mock"}
        }
        expected = {
            'physical_node': 'mock_node',
            'collect_stats': {},
        }
        self.assertEqual(trex_traffic_gen.collect_kpi(), expected)

    @mock.patch.object(ctx_base.Context, 'get_context_from_server',
                       return_value='fake_context')
    def test_instantiate(self, *args):
        trex_traffic_gen = tg_trex_vpp.TrexTrafficGenVpp(
            'tg0', self.VNFD_0)
        trex_traffic_gen._start_server = mock.Mock(return_value=0)
        trex_traffic_gen.resource_helper = mock.MagicMock()
        trex_traffic_gen.setup_helper.setup_vnf_environment = mock.MagicMock()

        scenario_cfg = {
            "tc": "tc_baremetal_rfc2544_ipv4_1flow_64B",
            "topology": 'nsb_test_case.yaml',
            'options': {
                'packetsize': 64,
                'traffic_type': 4,
                'rfc2544': {
                    'allowed_drop_rate': '0.8 - 1',
                },
                'vnf__0': {
                    'rules': 'acl_1rule.yaml',
                    'vnf_config': {
                        'lb_config': 'SW',
                        'lb_count': 1,
                        'worker_config': '1C/1T',
                        'worker_threads': 1
                    },
                },
            },
        }
        tg_trex_vpp.WAIT_TIME = 3
        scenario_cfg.update({"nodes": {"tg0": {}, "vnf0": {}}})
        self.assertIsNone(trex_traffic_gen.instantiate(scenario_cfg, {}))

    @mock.patch.object(ctx_base.Context, 'get_context_from_server',
                       return_value='fake_context')
    def test_instantiate_error(self, *args):
        trex_traffic_gen = tg_trex_vpp.TrexTrafficGenVpp(
            'tg0', self.VNFD_0)
        trex_traffic_gen.resource_helper = mock.MagicMock()
        trex_traffic_gen.setup_helper.setup_vnf_environment = mock.MagicMock()
        scenario_cfg = {
            "tc": "tc_baremetal_rfc2544_ipv4_1flow_64B",
            "nodes": {
                "tg0": {},
                "vnf0": {}
            },
            "topology": 'nsb_test_case.yaml',
            'options': {
                'packetsize': 64,
                'traffic_type': 4,
                'rfc2544': {
                    'allowed_drop_rate': '0.8 - 1',
                },
                'vnf__0': {
                    'rules': 'acl_1rule.yaml',
                    'vnf_config': {
                        'lb_config': 'SW',
                        'lb_count': 1,
                        'worker_config': '1C/1T',
                        'worker_threads': 1,
                    },
                },
            },
        }
        trex_traffic_gen.instantiate(scenario_cfg, {})

    @mock.patch(
        'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper')
    def test_wait_for_instantiate(self, ssh, *args):
        mock_ssh(ssh)

        mock_process = mock.Mock(autospec=Process)
        mock_process.is_alive.return_value = True
        mock_process.exitcode = 432

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex_vpp.TrexTrafficGenVpp('tg0', vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper.execute.return_value = 0, '', ''
        trex_traffic_gen.scenario_helper.scenario_cfg = {}
        trex_traffic_gen._tg_process = mock_process
        self.assertEqual(432, trex_traffic_gen.wait_for_instantiate())
