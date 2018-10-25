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
import time
from collections import deque

import mock
import unittest

from yardstick.network_services.vnf_generic.vnf import tg_imsbench_sipp
from yardstick.benchmark.contexts import base as ctx_base
from yardstick import ssh


class TestSippVnf(unittest.TestCase):
    
    VNFD = {
        "short-name": "SippVnf", 
        "vdu": [
            {
                "id": "sippvnf-baremetal", 
                "routing_table": "", 
                "external-interface": [
                    {
                        "virtual-interface": {
                            "vld_id": "ims_network", 
                            "peer_ifname": "xe0", 
                            "dst_mac": "90:e2:ba:7c:41:e8", 
                            "network": {}, 
                            "local_ip": "10.80.3.11", 
                            "peer_intf": {
                                "vnf__0": {
                                    "vld_id": "data_network", 
                                    "peer_ifname": "xe1", 
                                    "dst_mac": "90:e2:ba:7c:30:e8", 
                                    "network": {}, 
                                    "local_ip": "10.80.3.7", 
                                    "node_name": "vnf__0", 
                                    "netmask": "255.255.255.0", 
                                    "peer_name": "tg__0", 
                                    "dst_ip": "10.80.3.11", 
                                    "ifname": "xe0", 
                                    "local_mac": "90:e2:ba:7c:41:a8"
                                }, 
                                "vnf__1": {
                                    "vld_id": "ims_network", 
                                    "peer_ifname": "xe1", 
                                    "dst_mac": "90:e2:ba:7c:30:e8", 
                                    "network": {}, 
                                    "local_ip": "10.80.3.7", 
                                    "node_name": "vnf__1", 
                                    "netmask": "255.255.255.0", 
                                    "peer_name": "tg__0", 
                                    "dst_ip": "10.80.3.11", 
                                    "ifname": "xe0", 
                                    "local_mac": "90:e2:ba:7c:41:e8"
                                }
                            }, 
                            "node_name": "tg__0", 
                            "netmask": "255.255.255.0", 
                            "peer_name": "vnf__1", 
                            "dst_ip": "10.80.3.7", 
                            "ifname": "xe0", 
                            "local_mac": "90:e2:ba:7c:30:e8"
                        }, 
                        "vnfd-connection-point-ref": "xe0", 
                        "name": "xe0"
                    }, 
                    {
                        "virtual-interface": {
                            "vld_id": "ims_network", 
                            "peer_ifname": "xe0", 
                            "dst_mac": "90:e2:ba:7c:41:e8", 
                            "network": {}, 
                            "local_ip": "10.80.3.11", 
                            "peer_intf": {
                                "vnf__0": {
                                    "vld_id": "data_network", 
                                    "peer_ifname": "xe1", 
                                    "dst_mac": "90:e2:ba:7c:30:e8", 
                                    "network": {}, 
                                    "local_ip": "10.80.3.7", 
                                    "peer_intf": {
                                        "vld_id": "ims_network", 
                                        "peer_ifname": "xe0", 
                                        "dst_mac": "90:e2:ba:7c:41:e8", 
                                        "network": {}, 
                                        "local_ip": "10.80.3.11", 
                                        "node_name": "tg__0", 
                                        "netmask": "255.255.255.0", 
                                        "peer_name": "vnf__1", 
                                        "dst_ip": "10.80.3.7", 
                                        "ifname": "xe0", 
                                        "local_mac": "90:e2:ba:7c:30:e8"
                                    }, 
                                    "node_name": "vnf__0", 
                                    "netmask": "255.255.255.0", 
                                    "peer_name": "tg__0", 
                                    "dst_ip": "10.80.3.11", 
                                    "ifname": "xe0", 
                                    "local_mac": "90:e2:ba:7c:41:a8"
                                }, 
                                "vnf__1": {
                                    "vld_id": "ims_network", 
                                    "peer_ifname": "xe1", 
                                    "dst_mac": "90:e2:ba:7c:30:e8", 
                                    "network": {}, 
                                    "local_ip": "10.80.3.7", 
                                    "peer_intf": {
                                        "vld_id": "ims_network", 
                                        "peer_ifname": "xe0", 
                                        "dst_mac": "90:e2:ba:7c:41:e8", 
                                        "network": {}, 
                                        "local_ip": "10.80.3.11", 
                                        "peer_intf": {
                                            "vld_id": "data_network", 
                                            "peer_ifname": "xe1", 
                                            "dst_mac": "90:e2:ba:7c:30:e8", 
                                            "network": {}, 
                                            "local_ip": "10.80.3.7", 
                                            "node_name": "vnf__0", 
                                            "netmask": "255.255.255.0", 
                                            "peer_name": "tg__0", 
                                            "dst_ip": "10.80.3.11", 
                                            "ifname": "xe0", 
                                            "local_mac": "90:e2:ba:7c:41:a8"
                                        }, 
                                        "node_name": "tg__0", 
                                        "netmask": "255.255.255.0", 
                                        "peer_name": "vnf__1", 
                                        "dst_ip": "10.80.3.7", 
                                        "ifname": "xe0", 
                                        "local_mac": "90:e2:ba:7c:30:e8"
                                    }, 
                                    "node_name": "vnf__1", 
                                    "netmask": "255.255.255.0", 
                                    "peer_name": "tg__0", 
                                    "dst_ip": "10.80.3.11", 
                                    "ifname": "xe0", 
                                    "local_mac": "90:e2:ba:7c:41:e8"
                                }
                            }, 
                            "node_name": "tg__0", 
                            "netmask": "255.255.255.0", 
                            "peer_name": "vnf__1", 
                            "dst_ip": "10.80.3.7", 
                            "ifname": "xe1", 
                            "local_mac": "90:e2:ba:7c:30:e8"
                        }, 
                        "vnfd-connection-point-ref": "xe1", 
                        "name": "xe1"
                    }
                ], 
                "name": "sippvnf-baremetal", 
                "description": "Sipp"
            }
        ], 
        "description": "ImsbenchSipp", 
        "mgmt-interface": {
            "vdu-id": "sipp-baremetal", 
            "password": "blueteam11", 
            "user": "root", 
            "ip": "10.80.3.11"
        }, 
        "benchmark": {
            "kpi": [
                "packets_in", 
                "packets_fwd", 
                "packets_dropped"
            ]
        }, 
        "id": "SippVnf", 
        "name": "SippVnf"
    }

    SCENARIO_CFG = {
        "task_id": "ba636744-898e-4783-a4aa-0a79c60953cc", 
        "tc": "tc_vims_baremetal_sipp", 
        "runner": {
            "object": "yardstick.benchmark.scenarios.networking.vnf_generic.NetworkServiceTestCase", 
            "interval": 1, 
            "output_config": {
                "DEFAULT": {
                    "debug": "False", 
                    "dispatcher": [
                        "influxdb"
                    ]
                }, 
                "nsb": {
                    "debug": "False", 
                    "trex_client_lib": "/opt/nsb_bin/trex_client/stl", 
                    "bin_path": "/opt/nsb_bin", 
                    "trex_path": "/opt/nsb_bin/trex/scripts", 
                    "dispatcher": "influxdb"
                }, 
                "dispatcher_influxdb": {
                    "username": "root", 
                    "target": "http://10.80.3.11:8086", 
                    "db_name": "yardstick", 
                    "timeout": "5", 
                    "debug": "False", 
                    "password": "root", 
                    "dispatcher": "influxdb"
                }, 
                "dispatcher_http": {
                    "debug": "False", 
                    "dispatcher": "influxdb", 
                    "timeout": "5", 
                    "target": "http://127.0.0.1:8000/results"
                }, 
                "dispatcher_file": {
                    "debug": "False", 
                    "backup_count": "0", 
                    "max_bytes": "0", 
                    "dispatcher": "influxdb", 
                    "file_path": "/tmp/yardstick.out"
                }
            }, 
            "runner_id": 18148, 
            "duration": 60, 
            "type": "Vims"
        }, 
        "nodes": {
            "vnf__0": "pcscf.yardstick-ba636744", 
            "vnf__1": "hss.yardstick-ba636744", 
            "tg__0": "sipp.yardstick-ba636744"
        }, 
        "topology": "vims-topology.yaml", 
        "type": "NSPerf", 
        "traffic_profile": "../../traffic_profiles/ipv4_throughput.yaml", 
        "task_path": "samples/vnf_samples/nsut/vims", 
        "options": {
            "init_reg_max": 5000, 
            "end_user": 10000, 
            "reg_cps": 20, 
            "rereg_cps": 20, 
            "rereg_step": 10, 
            "wait_time": 5, 
            "start_user": 1, 
            "msgc_cps": 10, 
            "dereg_step": 10, 
            "call_cps": 10, 
            "reg_step": 10, 
            "init_reg_cps": 50, 
            "dereg_cps": 20, 
            "msgc_step": 5, 
            "call_step": 5, 
            "hold_time": 15, 
            "port": 5060, 
            "run_mode": "nortp"
        }
    }
    CONTEXT_CFG = {
        "nodes": {
            "tg__0": {
                "ip": "10.80.3.11", 
                "interfaces": {
                    "xe0": {
                        "vld_id": "ims_network", 
                        "peer_ifname": "xe0", 
                        "dst_mac": "90:e2:ba:7c:41:e8", 
                        "network": {}, 
                        "local_ip": "10.80.3.11", 
                        "peer_intf": {
                            "vnf__0": {
                                "vld_id": "data_network", 
                                "peer_ifname": "xe1", 
                                "dst_mac": "90:e2:ba:7c:30:e8", 
                                "network": {}, 
                                "local_ip": "10.80.3.7", 
                                "node_name": "vnf__0", 
                                "netmask": "255.255.255.0", 
                                "peer_name": "tg__0", 
                                "dst_ip": "10.80.3.11", 
                                "ifname": "xe0", 
                                "local_mac": "90:e2:ba:7c:41:a8"
                            }, 
                            "vnf__1": {
                                "vld_id": "ims_network", 
                                "peer_ifname": "xe1", 
                                "dst_mac": "90:e2:ba:7c:30:e8", 
                                "network": {}, 
                                "local_ip": "10.80.3.7", 
                                "node_name": "vnf__1", 
                                "netmask": "255.255.255.0", 
                                "peer_name": "tg__0", 
                                "dst_ip": "10.80.3.11", 
                                "ifname": "xe0", 
                                "local_mac": "90:e2:ba:7c:41:e8"
                            }
                        }, 
                        "node_name": "tg__0", 
                        "netmask": "255.255.255.0", 
                        "peer_name": "vnf__1", 
                        "dst_ip": "10.80.3.7", 
                        "ifname": "xe0", 
                        "local_mac": "90:e2:ba:7c:30:e8"
                    }, 
                    "xe1": {
                        "vld_id": "ims_network", 
                        "peer_ifname": "xe0", 
                        "dst_mac": "90:e2:ba:7c:41:e8", 
                        "network": {}, 
                        "local_ip": "10.80.3.11", 
                        "peer_intf": {
                            "vnf__0": {
                                "vld_id": "data_network", 
                                "peer_ifname": "xe1", 
                                "dst_mac": "90:e2:ba:7c:30:e8", 
                                "network": {}, 
                                "local_ip": "10.80.3.7", 
                                "peer_intf": {
                                    "vld_id": "ims_network", 
                                    "peer_ifname": "xe0", 
                                    "dst_mac": "90:e2:ba:7c:41:e8", 
                                    "network": {}, 
                                    "local_ip": "10.80.3.11", 
                                    "node_name": "tg__0", 
                                    "netmask": "255.255.255.0", 
                                    "peer_name": "vnf__1", 
                                    "dst_ip": "10.80.3.7", 
                                    "ifname": "xe0", 
                                    "local_mac": "90:e2:ba:7c:30:e8"
                                }, 
                                "node_name": "vnf__0", 
                                "netmask": "255.255.255.0", 
                                "peer_name": "tg__0", 
                                "dst_ip": "10.80.3.11", 
                                "ifname": "xe0", 
                                "local_mac": "90:e2:ba:7c:41:a8"
                            }, 
                            "vnf__1": {
                                "vld_id": "ims_network", 
                                "peer_ifname": "xe1", 
                                "dst_mac": "90:e2:ba:7c:30:e8", 
                                "network": {}, 
                                "local_ip": "10.80.3.7", 
                                "peer_intf": {
                                    "vld_id": "ims_network", 
                                    "peer_ifname": "xe0", 
                                    "dst_mac": "90:e2:ba:7c:41:e8", 
                                    "network": {}, 
                                    "local_ip": "10.80.3.11", 
                                    "peer_intf": {
                                        "vld_id": "data_network", 
                                        "peer_ifname": "xe1", 
                                        "dst_mac": "90:e2:ba:7c:30:e8", 
                                        "network": {}, 
                                        "local_ip": "10.80.3.7", 
                                        "node_name": "vnf__0", 
                                        "netmask": "255.255.255.0", 
                                        "peer_name": "tg__0", 
                                        "dst_ip": "10.80.3.11", 
                                        "ifname": "xe0", 
                                        "local_mac": "90:e2:ba:7c:41:a8"
                                    }, 
                                    "node_name": "tg__0", 
                                    "netmask": "255.255.255.0", 
                                    "peer_name": "vnf__1", 
                                    "dst_ip": "10.80.3.7", 
                                    "ifname": "xe0", 
                                    "local_mac": "90:e2:ba:7c:30:e8"
                                }, 
                                "node_name": "vnf__1", 
                                "netmask": "255.255.255.0", 
                                "peer_name": "tg__0", 
                                "dst_ip": "10.80.3.11", 
                                "ifname": "xe0", 
                                "local_mac": "90:e2:ba:7c:41:e8"
                            }
                        }, 
                        "node_name": "tg__0", 
                        "netmask": "255.255.255.0", 
                        "peer_name": "vnf__1", 
                        "dst_ip": "10.80.3.7", 
                        "ifname": "xe1", 
                        "local_mac": "90:e2:ba:7c:30:e8"
                    }
                }, 
                "user": "root", 
                "password": "blueteam11", 
                "VNF model": "../../vnf_descriptors/tg_sipp_vnfd.yaml", 
                "name": "sipp.yardstick-a75a3aff", 
                "vnfd-id-ref": "tg__0", 
                "member-vnf-index": "1", 
                "role": "TrafficGen", 
                "ctx_type": "Node"
            }, 
            "vnf__0": {
                "ip": "10.80.3.7", 
                "interfaces": {
                    "xe0": {
                        "vld_id": "data_network", 
                        "peer_ifname": "xe1", 
                        "dst_mac": "90:e2:ba:7c:30:e8", 
                        "network": {}, 
                        "local_ip": "10.80.3.7", 
                        "peer_intf": {
                            "tg__0": {
                                "vld_id": "ims_network", 
                                "peer_ifname": "xe0", 
                                "dst_mac": "90:e2:ba:7c:41:e8", 
                                "network": {}, 
                                "local_ip": "10.80.3.11", 
                                "node_name": "tg__0", 
                                "netmask": "255.255.255.0", 
                                "peer_name": "vnf__1", 
                                "dst_ip": "10.80.3.7", 
                                "ifname": "xe1", 
                                "local_mac": "90:e2:ba:7c:30:e8"
                            }
                        }, 
                        "node_name": "vnf__0", 
                        "netmask": "255.255.255.0", 
                        "peer_name": "tg__0", 
                        "dst_ip": "10.80.3.11", 
                        "ifname": "xe0", 
                        "local_mac": "90:e2:ba:7c:41:a8"
                    }
                }, 
                "user": "root", 
                "password": "blueteam11", 
                "VNF model": "../../vnf_descriptors/vims_pcscf_vnfd.yaml", 
                "name": "pcscf.yardstick-a75a3aff", 
                "vnfd-id-ref": "vnf__0", 
                "member-vnf-index": "2", 
                "role": "VirtualNetworkFunction", 
                "ctx_type": "Node"
            }, 
            "vnf__1": {
                "ip": "10.80.3.7", 
                "interfaces": {
                    "xe0": {
                        "vld_id": "ims_network", 
                        "peer_ifname": "xe1", 
                        "dst_mac": "90:e2:ba:7c:30:e8", 
                        "network": {}, 
                        "local_ip": "10.80.3.7", 
                        "peer_intf": {
                            "tg__0": {
                                "vld_id": "ims_network", 
                                "peer_ifname": "xe0", 
                                "dst_mac": "90:e2:ba:7c:41:e8", 
                                "network": {}, 
                                "local_ip": "10.80.3.11", 
                                "peer_intf": {
                                    "vld_id": "data_network", 
                                    "peer_ifname": "xe1", 
                                    "dst_mac": "90:e2:ba:7c:30:e8", 
                                    "network": {}, 
                                    "local_ip": "10.80.3.7", 
                                    "peer_intf": {
                                        "vld_id": "ims_network", 
                                        "peer_ifname": "xe0", 
                                        "dst_mac": "90:e2:ba:7c:41:e8", 
                                        "network": {}, 
                                        "local_ip": "10.80.3.11", 
                                        "node_name": "tg__0", 
                                        "netmask": "255.255.255.0", 
                                        "peer_name": "vnf__1", 
                                        "dst_ip": "10.80.3.7", 
                                        "ifname": "xe0", 
                                        "local_mac": "90:e2:ba:7c:30:e8"
                                    }, 
                                    "node_name": "vnf__0", 
                                    "netmask": "255.255.255.0", 
                                    "peer_name": "tg__0", 
                                    "dst_ip": "10.80.3.11", 
                                    "ifname": "xe0", 
                                    "local_mac": "90:e2:ba:7c:41:a8"
                                }, 
                                "node_name": "tg__0", 
                                "netmask": "255.255.255.0", 
                                "peer_name": "vnf__1", 
                                "dst_ip": "10.80.3.7", 
                                "ifname": "xe1", 
                                "local_mac": "90:e2:ba:7c:30:e8"
                            }
                        }, 
                        "node_name": "vnf__1", 
                        "netmask": "255.255.255.0", 
                        "peer_name": "tg__0", 
                        "dst_ip": "10.80.3.11", 
                        "ifname": "xe0", 
                        "local_mac": "90:e2:ba:7c:41:e8"
                    }
                }, 
                "user": "root", 
                "password": "blueteam11", 
                "VNF model": "../../vnf_descriptors/vims_hss_vnfd.yaml", 
                "name": "hss.yardstick-a75a3aff", 
                "vnfd-id-ref": "vnf__1", 
                "member-vnf-index": "3", 
                "role": "VirtualNetworkFunction", 
                "ctx_type": "Node"
            }
        }, 
        "networks": {}
    }

    def setUp(self):
        self._mock_ssh = mock.patch.object(ssh, 'SSH')
        self.mock_ssh = self._mock_ssh.start()

        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_ssh.stop()

    def test___init__(self):
        sipp_vnf = tg_imsbench_sipp.SippVnf('tg__0', self.VNFD, 'task_id')
        self.assertIsInstance(sipp_vnf.resource_helper, 
                              tg_imsbench_sipp.SippResourceHelper) 

    @mock.patch.object(ctx_base.Context, 'get_context_from_server',
                       return_value='fake_context')

    def test_instantiate(self, *args):
        sipp_vnf = tg_imsbench_sipp.SippVnf('tg__0', self.VNFD, 'task_id')
        self.assertIsNone(sipp_vnf.instantiate(self.SCENARIO_CFG,
                          self.CONTEXT_CFG))

    def test_terminate(self):
        sipp_vnf = tg_imsbench_sipp.SippVnf('tg__0', self.VNFD, 'task_id')
        sipp_vnf.ssh_helper = mock.MagicMock()
        sipp_vnf.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(sipp_vnf.terminate())    
