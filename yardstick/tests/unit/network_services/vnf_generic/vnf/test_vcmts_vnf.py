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
import mock
import copy
import os

from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh
from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper
from yardstick.network_services.vnf_generic.vnf import vcmts_vnf

from influxdb.resultset import ResultSet

NAME = "vnf__0"


class TestInfluxDBHelper(unittest.TestCase):

    def test___init__(self):
        influxdb_helper = vcmts_vnf.InfluxDBHelper("localhost", 8086)
        self.assertEqual(influxdb_helper._vcmts_influxdb_ip, "localhost")
        self.assertEqual(influxdb_helper._vcmts_influxdb_port, 8086)
        self.assertIsNotNone(influxdb_helper._last_upstream_rx)
        self.assertIsNotNone(influxdb_helper._last_values_time)

    def test_start(self):
        influxdb_helper = vcmts_vnf.InfluxDBHelper("localhost", 8086)
        influxdb_helper.start()
        self.assertIsNotNone(influxdb_helper._read_client)
        self.assertIsNotNone(influxdb_helper._write_client)

    def test__get_last_value_time(self):
        influxdb_helper = vcmts_vnf.InfluxDBHelper("localhost", 8086)
        self.assertEqual(influxdb_helper._get_last_value_time('cpu_value'),
                         vcmts_vnf.InfluxDBHelper.INITIAL_VALUE)

        influxdb_helper._last_values_time['cpu_value'] = "RANDOM"
        self.assertEqual(influxdb_helper._get_last_value_time('cpu_value'),
                         "RANDOM")

    def test__set_last_value_time(self):
        influxdb_helper = vcmts_vnf.InfluxDBHelper("localhost", 8086)
        influxdb_helper._set_last_value_time('cpu_value', '00:00')
        self.assertEqual(influxdb_helper._last_values_time['cpu_value'],
                         "'00:00'")

    def test__query_measurement(self):
        influxdb_helper = vcmts_vnf.InfluxDBHelper("localhost", 8086)
        influxdb_helper._read_client = mock.MagicMock()

        resulted_generator = mock.MagicMock()
        resulted_generator.keys.return_value = []
        influxdb_helper._read_client.query.return_value = resulted_generator
        query_result = influxdb_helper._query_measurement('cpu_value')
        self.assertIsNone(query_result)

        resulted_generator = mock.MagicMock()
        resulted_generator.keys.return_value = ["", ""]
        resulted_generator.get_points.return_value = ResultSet({"":""})
        influxdb_helper._read_client.query.return_value = resulted_generator
        query_result = influxdb_helper._query_measurement('cpu_value')
        self.assertIsNotNone(query_result)

    def test__rw_measurment(self):
        influxdb_helper = vcmts_vnf.InfluxDBHelper("localhost", 8086)
        influxdb_helper._query_measurement = mock.MagicMock()
        influxdb_helper._query_measurement.return_value = None
        influxdb_helper._rw_measurment('cpu_value', [])
        self.assertEqual(len(influxdb_helper._last_values_time), 0)

        entry = {
            "type":"type",
            "host":"host",
            "time":"time",
            "id": "1",
            "value": "1.0"
        }
        influxdb_helper._query_measurement.return_value = [entry]
        influxdb_helper._write_client = mock.MagicMock()
        influxdb_helper._rw_measurment('cpu_value', ["id", "value"])
        self.assertEqual(len(influxdb_helper._last_values_time), 1)
        influxdb_helper._write_client.write_points.assert_called_once()

    def test_copy_kpi(self):
        influxdb_helper = vcmts_vnf.InfluxDBHelper("localhost", 8086)
        influxdb_helper._rw_measurment = mock.MagicMock()
        influxdb_helper.copy_kpi()
        influxdb_helper._rw_measurment.assert_called()


class TestVcmtsdSetupEnvHelper(unittest.TestCase):
    POD_CFG = {
        "cm_crypto": "aes",
        "cpu_socket_id": "0",
        "ds_core_pool_index": "2",
        "ds_core_type": "exclusive",
        "net_ds": "1a:02.1",
        "net_us": "1a:02.0",
        "num_ofdm": "1",
        "num_subs": "100",
        "power_mgmt": "pm_on",
        "qat": "qat_off",
        "service_group_config": "",
        "sg_id": "0",
        "vcmtsd_image": "vcmts-d:perf"
    }

    OPTIONS = {
        "pktgen_values": "/tmp/pktgen_values.yaml",
        "tg__0": {
            "pktgen_id": 0
        },
        "vcmts_influxdb_ip": "10.80.5.150",
        "vcmts_influxdb_port": 8086,
        "vcmtsd_values": "/tmp/vcmtsd_values.yaml",
        "vnf__0": {
            "sg_id": 0,
            "stream_dir": "us"
        },
        "vnf__1": {
            "sg_id": 0,
            "stream_dir": "ds"
        }
    }

    def setUp(self):
        vnfd_helper = VnfdHelper(
            TestVcmtsVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS

        self.setup_helper = vcmts_vnf.VcmtsdSetupEnvHelper(
            vnfd_helper, ssh_helper, scenario_helper)

    def _build_us_parameters(self):
        return vcmts_vnf.VcmtsdSetupEnvHelper.BASE_PARAMETERS + " " \
             + " /opt/bin/cmk isolate --conf-dir=/etc/cmk" \
             + " --socket-id=" + str(self.POD_CFG['cpu_socket_id']) \
             + " --pool=shared" \
             + " /vcmts-config/run_upstream.sh " + self.POD_CFG['sg_id'] \
             + " " + self.POD_CFG['ds_core_type'] \
             + " " + str(self.POD_CFG['num_ofdm']) + "ofdm" \
             + " " + str(self.POD_CFG['num_subs']) + "cm" \
             + " " + self.POD_CFG['cm_crypto'] \
             + " " + self.POD_CFG['qat'] \
             + " " + self.POD_CFG['net_us'] \
             + " " + self.POD_CFG['power_mgmt']

    def test_build_us_parameters(self):
        constructed = self._build_us_parameters()
        result = self.setup_helper.build_us_parameters(self.POD_CFG)
        self.assertEqual(constructed, result)

    def _build_ds_parameters(self):
        return vcmts_vnf.VcmtsdSetupEnvHelper.BASE_PARAMETERS + " " \
             + " /opt/bin/cmk isolate --conf-dir=/etc/cmk" \
             + " --socket-id=" + str(self.POD_CFG['cpu_socket_id']) \
             + " --pool=" + self.POD_CFG['ds_core_type'] \
             + " /vcmts-config/run_downstream.sh " + self.POD_CFG['sg_id'] \
             + " " + self.POD_CFG['ds_core_type'] \
             + " " + str(self.POD_CFG['ds_core_pool_index']) \
             + " " + str(self.POD_CFG['num_ofdm']) + "ofdm" \
             + " " + str(self.POD_CFG['num_subs']) + "cm" \
             + " " + self.POD_CFG['cm_crypto'] \
             + " " + self.POD_CFG['qat'] \
             + " " + self.POD_CFG['net_ds'] \
             + " " + self.POD_CFG['power_mgmt']

    def test_build_ds_parameters(self):
        constructed = self._build_ds_parameters()
        result = self.setup_helper.build_ds_parameters(self.POD_CFG)
        self.assertEqual(constructed, result)

    def test_build_cmd(self):
        us_constructed = self._build_us_parameters()
        us_result = self.setup_helper.build_cmd('us', self.POD_CFG)
        self.assertEqual(us_constructed, us_result)
        ds_constructed = self._build_ds_parameters()
        ds_result = self.setup_helper.build_cmd('ds', self.POD_CFG)
        self.assertEqual(ds_constructed, ds_result)

    def test_run_vcmtsd(self):
        us_constructed = self._build_us_parameters()

        vnfd_helper = VnfdHelper(
            TestVcmtsVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.MagicMock()
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS

        setup_helper = vcmts_vnf.VcmtsdSetupEnvHelper(
            vnfd_helper, ssh_helper, scenario_helper)

        setup_helper.run_vcmtsd('us', self.POD_CFG)
        ssh_helper.send_command.assert_called_with(us_constructed)

    def test_setup_vnf_environment(self):
        self.assertIsNone(self.setup_helper.setup_vnf_environment())

class TestVcmtsVNF(unittest.TestCase):

    VNFD = {'vnfd:vnfd-catalog':
            {'vnfd':
            [{
            "benchmark": {
                "kpi": [
                    "upstream/bits_per_second"
                ]
            },
            "connection-point": [
                {
                    "name": "xe0",
                    "type": "VPORT"
                },
                {
                    "name": "xe1",
                    "type": "VPORT"
                }
            ],
            "description": "vCMTS Upstream-Downstream Kubernetes",
            "id": "VcmtsVNF",
            "mgmt-interface": {
                "ip": "192.168.100.35",
                "key_filename": "/tmp/yardstick_key-81dcca91",
                "user": "root",
                "vdu-id": "vcmtsvnf-kubernetes"
            },
            "name": "vcmtsvnf",
            "short-name": "vcmtsvnf",
            "vdu": [
                {
                    "description": "vCMTS Upstream-Downstream Kubernetes",
                    "external-interface": [],
                    "id": "vcmtsvnf-kubernetes",
                    "name": "vcmtsvnf-kubernetes"
                }
            ],
            "vm-flavor": {
                "memory-mb": "4096",
                "vcpu-count": "4"
            }
        }]
        }
    }

    POD_CFG = [
        {
            "cm_crypto": "aes",
            "cpu_socket_id": "0",
            "ds_core_pool_index": "2",
            "ds_core_type": "exclusive",
            "net_ds": "1a:02.1",
            "net_us": "1a:02.0",
            "num_ofdm": "1",
            "num_subs": "100",
            "power_mgmt": "pm_on",
            "qat": "qat_off",
            "service_group_config": "",
            "sg_id": "0",
            "vcmtsd_image": "vcmts-d:perf"
        },
    ]

    SCENARIO_CFG = {
        "nodes": {
            "tg__0": "pktgen0-k8syardstick-afae18b2",
            "vnf__0": "vnf0us-k8syardstick-afae18b2",
            "vnf__1": "vnf0ds-k8syardstick-afae18b2"
        },
        "options": {
            "pktgen_values": "/tmp/pktgen_values.yaml",
            "tg__0": {
                "pktgen_id": 0
            },
            "vcmts_influxdb_ip": "10.80.5.150",
            "vcmts_influxdb_port": 8086,
            "vcmtsd_values": "/tmp/vcmtsd_values.yaml",
            "vnf__0": {
                "sg_id": 0,
                "stream_dir": "us"
            },
            "vnf__1": {
                "sg_id": 0,
                "stream_dir": "ds"
            }
        },
        "task_id": "afae18b2-9902-477f-8128-49afde7c3040",
        "task_path": "samples/vnf_samples/nsut/cmts",
        "tc": "tc_vcmts_k8s_pktgen",
        "topology": "k8s_vcmts_topology.yaml",
        "traffic_profile": "../../traffic_profiles/fixed.yaml",
        "type": "NSPerf"
    }

    CONTEXT_CFG = {
        "networks": {
            "flannel": {
                "name": "flannel"
            },
            "xe0": {
                "name": "xe0"
            },
            "xe1": {
                "name": "xe1"
            }
        },
        "nodes": {
            "tg__0": {
                "VNF model": "../../vnf_descriptors/tg_vcmts_tpl.yaml",
                "interfaces": {
                    "flannel": {
                        "local_ip": "192.168.24.110",
                        "local_mac": None,
                        "network_name": "flannel"
                    },
                    "xe0": {
                        "local_ip": "192.168.24.110",
                        "local_mac": None,
                        "network_name": "xe0"
                    },
                    "xe1": {
                        "local_ip": "192.168.24.110",
                        "local_mac": None,
                        "network_name": "xe1"
                    }
                },
                "ip": "192.168.24.110",
                "key_filename": "/tmp/yardstick_key-afae18b2",
                "member-vnf-index": "1",
                "name": "pktgen0-k8syardstick-afae18b2",
                "private_ip": "192.168.24.110",
                "service_ports": [
                    {
                        "name": "ssh",
                        "node_port": 17153,
                        "port": 22,
                        "protocol": "TCP",
                        "target_port": 22
                    },
                    {
                        "name": "lua",
                        "node_port": 51250,
                        "port": 22022,
                        "protocol": "TCP",
                        "target_port": 22022
                    }
                ],
                "ssh_port": 17153,
                "user": "root",
                "vnfd-id-ref": "tg__0"
            },
            "vnf__0": {
                "VNF model": "../../vnf_descriptors/vnf_vcmts_tpl.yaml",
                "interfaces": {
                    "flannel": {
                        "local_ip": "192.168.100.53",
                        "local_mac": None,
                        "network_name": "flannel"
                    },
                    "xe0": {
                        "local_ip": "192.168.100.53",
                        "local_mac": None,
                        "network_name": "xe0"
                    },
                    "xe1": {
                        "local_ip": "192.168.100.53",
                        "local_mac": None,
                        "network_name": "xe1"
                    }
                },
                "ip": "192.168.100.53",
                "key_filename": "/tmp/yardstick_key-afae18b2",
                "member-vnf-index": "3",
                "name": "vnf0us-k8syardstick-afae18b2",
                "private_ip": "192.168.100.53",
                "service_ports": [
                    {
                        "name": "ssh",
                        "node_port": 34027,
                        "port": 22,
                        "protocol": "TCP",
                        "target_port": 22
                    },
                    {
                        "name": "lua",
                        "node_port": 32580,
                        "port": 22022,
                        "protocol": "TCP",
                        "target_port": 22022
                    }
                ],
                "ssh_port": 34027,
                "user": "root",
                "vnfd-id-ref": "vnf__0"
            },
            "vnf__1": {
                "VNF model": "../../vnf_descriptors/vnf_vcmts_tpl.yaml",
                "interfaces": {
                    "flannel": {
                        "local_ip": "192.168.100.52",
                        "local_mac": None,
                        "network_name": "flannel"
                    },
                    "xe0": {
                        "local_ip": "192.168.100.52",
                        "local_mac": None,
                        "network_name": "xe0"
                    },
                    "xe1": {
                        "local_ip": "192.168.100.52",
                        "local_mac": None,
                        "network_name": "xe1"
                    }
                },
                "ip": "192.168.100.52",
                "key_filename": "/tmp/yardstick_key-afae18b2",
                "member-vnf-index": "4",
                "name": "vnf0ds-k8syardstick-afae18b2",
                "private_ip": "192.168.100.52",
                "service_ports": [
                    {
                        "name": "ssh",
                        "node_port": 58661,
                        "port": 22,
                        "protocol": "TCP",
                        "target_port": 22
                    },
                    {
                        "name": "lua",
                        "node_port": 58233,
                        "port": 22022,
                        "protocol": "TCP",
                        "target_port": 22022
                    }
                ],
                "ssh_port": 58661,
                "user": "root",
                "vnfd-id-ref": "vnf__1"
            },
        }
    }

    VCMTSD_VALUES_PATH = "/tmp/vcmtsd_values.yaml"

    VCMTSD_VALUES = \
            "serviceAccount: cmk-serviceaccount\n" \
            "topology:\n" \
            "  vcmts_replicas: 16\n" \
            "  vcmts_pods:\n" \
            "    - service_group_config:\n" \
            "      sg_id: 0\n" \
            "      net_us: 18:02.0\n" \
            "      net_ds: 18:02.1\n" \
            "      num_ofdm: 4\n" \
            "      num_subs: 300\n" \
            "      cm_crypto: aes\n" \
            "      qat: qat_off\n" \
            "      power_mgmt: pm_on\n" \
            "      cpu_socket_id: 0\n" \
            "      ds_core_type: exclusive\n" \
            "      ds_core_pool_index: 0\n" \
            "      vcmtsd_image: vcmts-d:feat"

    def setUp(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.vnf = vcmts_vnf.VcmtsVNF(NAME, vnfd)

    def test___init__(self, *args):
        self.assertIsNotNone(self.vnf.setup_helper)

    def test_extract_pod_cfg(self):
        pod_cfg = self.vnf.extract_pod_cfg(self.POD_CFG, "0")
        self.assertIsNotNone(pod_cfg)
        self.assertEqual(pod_cfg['sg_id'], '0')
        pod_cfg = self.vnf.extract_pod_cfg(self.POD_CFG, "1")
        self.assertIsNone(pod_cfg)

    def test_instantiate_missing_influxdb_info(self):
        err_scenario_cfg = copy.deepcopy(self.SCENARIO_CFG)
        err_scenario_cfg['options'].pop('vcmts_influxdb_ip', None)
        with self.assertRaises(KeyError):
            self.vnf.instantiate(err_scenario_cfg, self.CONTEXT_CFG)

    def test_instantiate_missing_vcmtsd_values_file(self):
        if os.path.isfile(self.VCMTSD_VALUES_PATH):
            os.remove(self.VCMTSD_VALUES_PATH)
        err_scenario_cfg = copy.deepcopy(self.SCENARIO_CFG)
        err_scenario_cfg['options']['vcmtsd_values'] = self.VCMTSD_VALUES_PATH
        with self.assertRaises(RuntimeError):
            self.vnf.instantiate(err_scenario_cfg, self.CONTEXT_CFG)

    def test_instantiate_empty_vcmtsd_values_file(self):
        yaml_sample = open(self.VCMTSD_VALUES_PATH, 'w')
        yaml_sample.write("")
        yaml_sample.close()

        err_scenario_cfg = copy.deepcopy(self.SCENARIO_CFG)
        err_scenario_cfg['options']['vcmtsd_values'] = self.VCMTSD_VALUES_PATH
        with self.assertRaises(RuntimeError):
            self.vnf.instantiate(err_scenario_cfg, self.CONTEXT_CFG)

        if os.path.isfile(self.VCMTSD_VALUES_PATH):
            os.remove(self.VCMTSD_VALUES_PATH)

    def test_instantiate_missing_vcmtsd_values_key(self):
        err_scenario_cfg = copy.deepcopy(self.SCENARIO_CFG)
        err_scenario_cfg['options'].pop('vcmtsd_values', None)
        with self.assertRaises(KeyError):
            self.vnf.instantiate(err_scenario_cfg, self.CONTEXT_CFG)

    def test_instantiate_invalid_sg_id(self):
        yaml_sample = open(self.VCMTSD_VALUES_PATH, 'w')
        yaml_sample.write(self.VCMTSD_VALUES)
        yaml_sample.close()

        err_scenario_cfg = copy.deepcopy(self.SCENARIO_CFG)
        err_scenario_cfg['options'][NAME]['sg_id'] = 8
        with self.assertRaises(KeyError):
            self.vnf.instantiate(err_scenario_cfg, self.CONTEXT_CFG)

        if os.path.isfile(self.VCMTSD_VALUES_PATH):
            os.remove(self.VCMTSD_VALUES_PATH)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.vcmts_vnf.VnfSshHelper')
    def test_instantiate_all_valid(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vnf = vcmts_vnf.VcmtsVNF(NAME, vnfd)

        yaml_sample = open(self.VCMTSD_VALUES_PATH, 'w')
        yaml_sample.write(self.VCMTSD_VALUES)
        yaml_sample.close()

        vnf.instantiate(self.SCENARIO_CFG, self.CONTEXT_CFG)
        self.assertEqual(vnf.vcmts_influxdb_ip, "10.80.5.150")
        self.assertEqual(vnf.vcmts_influxdb_port, 8086)

        if os.path.isfile(self.VCMTSD_VALUES_PATH):
            os.remove(self.VCMTSD_VALUES_PATH)

    def test__update_collectd_options(self):
        scenario_cfg = {'options':
                            {'collectd':
                                 {'interval': 3,
                                  'plugins':
                                      {'plugin3': {'param': 3}}},
                             'vnf__0':
                                 {'collectd':
                                      {'interval': 2,
                                       'plugins':
                                           {'plugin3': {'param': 2},
                                            'plugin2': {'param': 2}}}}}}
        context_cfg = {'nodes':
                           {'vnf__0':
                                {'collectd':
                                     {'interval': 1,
                                      'plugins':
                                          {'plugin3': {'param': 1},
                                           'plugin2': {'param': 1},
                                           'plugin1': {'param': 1}}}}}}
        expected = {'interval': 1,
                    'plugins':
                        {'plugin3': {'param': 1},
                         'plugin2': {'param': 1},
                         'plugin1': {'param': 1}}}

        self.vnf._update_collectd_options(scenario_cfg, context_cfg)
        self.assertEqual(self.vnf.setup_helper.collectd_options, expected)

    def test__update_options(self):
        options1 = {'interval': 1,
                    'param1': 'value1',
                    'plugins':
                        {'plugin3': {'param': 3},
                         'plugin2': {'param': 1},
                         'plugin1': {'param': 1}}}
        options2 = {'interval': 2,
                    'param2': 'value2',
                    'plugins':
                        {'plugin4': {'param': 4},
                         'plugin2': {'param': 2},
                         'plugin1': {'param': 2}}}
        expected = {'interval': 1,
                    'param1': 'value1',
                    'param2': 'value2',
                    'plugins':
                        {'plugin4': {'param': 4},
                         'plugin3': {'param': 3},
                         'plugin2': {'param': 1},
                         'plugin1': {'param': 1}}}

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vnf = vcmts_vnf.VcmtsVNF('vnf1', vnfd)
        vnf._update_options(options2, options1)
        self.assertEqual(options2, expected)

    def test_wait_for_instantiate(self):
        self.assertIsNone(self.vnf.wait_for_instantiate())

    def test_terminate(self):
        self.assertIsNone(self.vnf.terminate())

    def test_scale(self):
        self.assertIsNone(self.vnf.scale())

    def test_collect_kpi(self):
        self.vnf.influxdb_helper = mock.MagicMock()
        self.vnf.collect_kpi()
        self.vnf.influxdb_helper.copy_kpi.assert_called_once()

    def test_start_collect(self):
        self.vnf.vcmts_influxdb_ip = "localhost"
        self.vnf.vcmts_influxdb_port = 8800

        self.assertIsNone(self.vnf.start_collect())
        self.assertIsNotNone(self.vnf.influxdb_helper)

    def test_stop_collect(self):
        self.assertIsNone(self.vnf.stop_collect())
