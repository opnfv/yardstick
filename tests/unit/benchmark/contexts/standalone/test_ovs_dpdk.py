# Copyright (c) 2016-2017 Intel Corporation
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

# Unittest for yardstick.benchmark.contexts.standalone.standaloneovs

from __future__ import absolute_import
import os
import unittest
import mock

from yardstick.benchmark.contexts.standalone import ovs_dpdk
from yardstick.benchmark.contexts.standalone.base import CpuProperties
from yardstick.network_services.helpers.dpdkbindnic_helper import DpdkBindHelper
from yardstick.common.cpu_model import CpuList
from yardstick.common.cpu_model import CpuInfo
from yardstick.common.cpu_model import CpuModel

CPU_CONFIGURATION = {
    'cpu_properties': {
        'cpu_cores_pool': '0-15'
    }
}

EXAMPLE_HT_TOPO = """\
0: 0, 10
1: 1, 11
2: 2, 12
3: 3, 13
4: 4, 14
5: 5, 15
6: 6, 16
7: 7, 17
8: 8, 18
9: 9, 19
10: 0, 10
11: 1, 11
12: 2, 12
13: 3, 13
14: 4, 14
15: 5, 15
16: 6, 16
17: 7, 17
18: 8, 18
19: 9, 19
"""


class OvsDpdkContextTestCase(unittest.TestCase):

    NODES_SAMPLE = "nodes_sample.yaml"
    NODES_ovs_dpdk_SAMPLE = "nodes_ovs_dpdk_sample.yaml"
    NODES_DUPLICATE_SAMPLE = "nodes_duplicate_sample.yaml"

    ATTRS = {
        'name': 'StandaloneOvsDpdk',
        'file': 'pod',
        'flavor': {},
        'servers': {},
        'networks': {},
    }

    NETWORKS = {
        'mgmt': {'cidr': '152.16.100.10/24'},
        'private_0': {
            'phy_port': "0000:05:00.0",
            'vpci': "0000:00:07.0",
            'cidr': '152.16.100.10/24',
            'interface': 'if0',
            'mac': "00:00:00:00:00:01",
            'vf_pci': {
                'vf_pci': 0,
            },
            'gateway_ip': '152.16.100.20',
        },
        'public_0': {
            'phy_port': "0000:05:00.1",
            'vpci': "0000:00:08.0",
            'cidr': '152.16.40.10/24',
            'interface': 'if0',
            'vf_pci': {
                'vf_pci': 0,
            },
            'mac': "00:00:00:00:00:01",
            'gateway_ip': '152.16.100.20',
        },
    }

    SERVERS = {
        'vnf__0': {
            'cpu_properties': {
                'isolate_cpus': [2, 4, 6],
                'emulatorpin': '0',
            },
        },
    }

    VM_FLAVOR = {
        'extra_specs': {
            'hw:cpu_cores': '8',
            'hw:cpu_threads': '1',
        },
    }

    def setUp(self):
        self.ovs_dpdk = ovs_dpdk.OvsDpdkContext()
        self.ovs_dpdk.disable_call_tracking()

    def test___init__(self):
        self.assertIsNone(self.ovs_dpdk.file_path)
        self.assertEqual(self.ovs_dpdk.first_run, True)

    @mock.patch('yardstick.benchmark.contexts.standalone.base.model')
    def test_init(self, mock_model):
        mock_model.parse_pod_file.return_value = [{}, [{}], {}]
        self.assertIsNone(self.ovs_dpdk.init(self.ATTRS))

    def test__setup_ovs(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
            self.ovs_dpdk.connection = ssh_mock
            self.ovs_dpdk.dpdk_bind_helper = mock.Mock(autospec=DpdkBindHelper)
            self.ovs_dpdk.networks = self.NETWORKS
            self.ovs_dpdk.ovs_properties = {}
            self.assertIsNone(self.ovs_dpdk._setup_ovs())

    def test__start_ovs_serverswitch(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
            self.ovs_dpdk.connection = ssh_mock
            self.ovs_dpdk.networks = self.NETWORKS
            self.ovs_dpdk.ovs_properties = {}
            self.ovs_dpdk.wait_for_vswitchd = 0
            self.ovs_dpdk.cpu_properties = CpuProperties()
            self.ovs_dpdk.cpu_properties.pmd_pin = CpuList('1,2')

            self.assertIsNone(self.ovs_dpdk._start_ovs_serverswitch())

    def test__setup_ovs_bridge_add_flows(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
            self.ovs_dpdk.connection = ssh_mock
            self.ovs_dpdk.networks = self.NETWORKS
            self.ovs_dpdk.ovs_properties = {
                'version': {'ovs': '2.7.0'}
            }
            self.ovs_dpdk.wait_for_vswitchd = 0
            self.assertIsNone(self.ovs_dpdk._setup_ovs_bridge_add_flows())

    def test__cleanup_ovs_dpdk_env(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
            self.ovs_dpdk.connection = ssh_mock
            self.ovs_dpdk.networks = self.NETWORKS
            self.ovs_dpdk.ovs_properties = {
                'version': {'ovs': '2.7.0'}
            }
            self.ovs_dpdk.wait_for_vswitchd = 0
            self.assertIsNone(self.ovs_dpdk._cleanup_ovs_dpdk_env())

    @mock.patch('yardstick.benchmark.contexts.standalone.ovs_dpdk.OvsDeploy')
    def test__check_ovs_dpdk_env(self, _):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "a", ""))
            ssh.return_value = ssh_mock
            self.ovs_dpdk.connection = ssh_mock
            self.ovs_dpdk.networks = self.NETWORKS
            self.ovs_dpdk.wait_for_vswitchd = 0
            self.ovs_dpdk._cleanup_ovs_dpdk_env = mock.Mock()

            self.ovs_dpdk.ovs_properties = {
                'version': {'ovs': '2.8.0', 'dpdk': '17.05.2'}
            }
            self.assertIsNone(self.ovs_dpdk._check_ovs_dpdk_env())

            self.ovs_dpdk.ovs_properties = {
                'version': {'ovs': '2.0.0'}
            }
            self.ovs_dpdk.wait_for_vswitchd = 0
            self.assertRaises(Exception, self.ovs_dpdk._check_ovs_dpdk_env)

    @mock.patch('yardstick.benchmark.contexts.standalone.base.DpdkBindHelper')
    @mock.patch('yardstick.ssh.SSH')
    def test_deploy(self, *_):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.ovs_dpdk.vm_deploy = False
        self.assertIsNone(self.ovs_dpdk.deploy())

        self.ovs_dpdk.vm_deploy = True
        self.ovs_dpdk.host_mgmt = {}
        self.ovs_dpdk.install_req_libs = mock.Mock()
        self.ovs_dpdk._check_ovs_dpdk_env = mock.Mock(return_value={})
        self.ovs_dpdk._setup_ovs = mock.Mock(return_value={})
        self.ovs_dpdk._start_ovs_serverswitch = mock.Mock(return_value={})
        self.ovs_dpdk._setup_ovs_bridge_add_flows = mock.Mock(return_value={})
        self.ovs_dpdk.setup_context = mock.Mock(return_value={})
        self.ovs_dpdk.wait_for_vnfs_to_start = mock.Mock(return_value={})
        self.ovs_dpdk.networks = self.NETWORKS
        self.ovs_dpdk.handle_cpu_configuration = mock.Mock()
        self.assertIsNone(self.ovs_dpdk.deploy())

    @mock.patch('yardstick.benchmark.contexts.standalone.ovs_dpdk.model')
    @mock.patch('yardstick.ssh.SSH')
    def test_undeploy(self, *_):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.ovs_dpdk.vm_deploy = False
        self.assertIsNone(self.ovs_dpdk.undeploy())

        self.ovs_dpdk.vm_deploy = True
        self.ovs_dpdk.connection = ssh_mock
        self.ovs_dpdk.dpdk_bind_helper = mock.Mock(autospec=DpdkBindHelper)
        self.ovs_dpdk.vm_names = ['vm_0', 'vm_1']
        self.ovs_dpdk.drivers = ['vm_0', 'vm_1']
        self.ovs_dpdk._cleanup_ovs_dpdk_env = mock.Mock()
        self.ovs_dpdk.networks = self.NETWORKS
        self.assertIsNone(self.ovs_dpdk.undeploy())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test__get_server_with_dic_attr_name(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_ovs_dpdk_SAMPLE)
        }

        self.ovs_dpdk.init(attrs)

        attr_name = {'name': 'foo.bar'}
        result = self.ovs_dpdk._get_server(attr_name)

        self.assertEqual(result, None)

    @mock.patch('yardstick.benchmark.contexts.standalone.ovs_dpdk.model')
    def test__get_server_not_found(self, mock_model):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_ovs_dpdk_SAMPLE)
        }

        mock_model.parse_pod_file.return_value = [{}, {}, {}]
        self.ovs_dpdk.init(attrs)

        attr_name = 'bar.foo'
        result = self.ovs_dpdk._get_server(attr_name)

        self.assertEqual(result, None)

    def test__get_server_mismatch(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_ovs_dpdk_SAMPLE)
        }

        self.ovs_dpdk.init(attrs)

        attr_name = 'bar.foo1'
        result = self.ovs_dpdk._get_server(attr_name)

        self.assertEqual(result, None)

    def test__get_server_duplicate(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_DUPLICATE_SAMPLE)
        }

        self.ovs_dpdk.init(attrs)

        attr_name = 'node1.foo'
        with self.assertRaises(ValueError):
            self.ovs_dpdk._get_server(attr_name)

    def test__get_server_found(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_ovs_dpdk_SAMPLE)
        }

        self.ovs_dpdk.init(attrs)

        attr_name = 'node1.foo'
        result = self.ovs_dpdk._get_server(attr_name)

        self.assertEqual(result['ip'], '10.229.47.137')
        self.assertEqual(result['name'], 'node1.foo')
        self.assertEqual(result['user'], 'root')
        self.assertEqual(result['key_filename'], '/root/.yardstick_key')

    def test__get_network(self):
        network1 = {
            'name': 'net_1',
            'vld_id': 'vld111',
            'segmentation_id': 'seg54',
            'network_type': 'type_a',
            'physical_network': 'phys',
        }
        network2 = {
            'name': 'net_2',
            'vld_id': 'vld999',
        }
        self.ovs_dpdk.networks = {
            'a': network1,
            'b': network2,
        }

        attr_name = {}
        self.assertIsNone(self.ovs_dpdk._get_network(attr_name))

        attr_name = {'vld_id': 'vld777'}
        self.assertIsNone(self.ovs_dpdk._get_network(attr_name))

        self.assertIsNone(self.ovs_dpdk._get_network(None))

        attr_name = 'vld777'
        self.assertIsNone(self.ovs_dpdk._get_network(attr_name))

        attr_name = {'vld_id': 'vld999'}
        expected = {
            "name": 'net_2',
            "vld_id": 'vld999',
            "segmentation_id": None,
            "network_type": None,
            "physical_network": None,
        }
        result = self.ovs_dpdk._get_network(attr_name)
        self.assertDictEqual(result, expected)

        attr_name = 'a'
        expected = network1
        result = self.ovs_dpdk._get_network(attr_name)
        self.assertDictEqual(result, expected)

    def test__configure_nics(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.ovs_dpdk.vm_deploy = True
        self.ovs_dpdk.connection = ssh_mock
        self.ovs_dpdk.vm_names = ['vm_0', 'vm_1']
        self.ovs_dpdk.drivers = []
        self.ovs_dpdk.networks = self.NETWORKS
        self.ovs_dpdk.get_vf_datas = mock.Mock(return_value="")
        self.assertIsNone(self.ovs_dpdk._configure_nics())

    @mock.patch('yardstick.benchmark.contexts.standalone.ovs_dpdk.model')
    def test__enable_interfaces(self, _):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.ovs_dpdk.vm_deploy = True
        self.ovs_dpdk.connection = ssh_mock
        self.ovs_dpdk.vm_names = ['vm_0', 'vm_1']
        self.ovs_dpdk.drivers = []
        self.ovs_dpdk.networks = self.NETWORKS
        self.ovs_dpdk.get_vf_datas = mock.Mock(return_value="")
        self.assertIsNone(self.ovs_dpdk._enable_interfaces(0, 0, ["private_0"], 'test'))

    @mock.patch('yardstick.benchmark.contexts.standalone.base.model')
    def test_setup_context(self, mock_libvirt):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.ovs_dpdk.vm_deploy = True
        self.ovs_dpdk.connection = ssh_mock
        self.ovs_dpdk.vm_names = ['vm_0', 'vm_1']
        self.ovs_dpdk.drivers = []
        self.ovs_dpdk.servers = {
            'vnf_0': {
                'network_ports': {
                    'mgmt': {'cidr': '152.16.100.10/24'},
                    'xe0': ['private_0'],
                    'xe1': ['public_0']
                }
            }
        }
        self.ovs_dpdk.networks = self.NETWORKS
        self.ovs_dpdk.host_mgmt = {}
        self.ovs_dpdk.flavor = {}
        self.ovs_dpdk._configure_nics_for_ovs_dpdk = mock.Mock(return_value="")
        mock_libvirt.check_if_vm_exists_and_delete = mock.Mock(return_value="")
        mock_libvirt.build_vm_xml = mock.Mock(return_value=[6, "00:00:00:00:00:01"])
        self.ovs_dpdk._enable_interfaces = mock.Mock(return_value="")
        mock_libvirt.virsh_create_vm = mock.Mock(return_value="")
        mock_libvirt.pin_vcpu_for_perf = mock.Mock(return_value="")
        self.ovs_dpdk.cloud_init = mock.Mock()
        self.ovs_dpdk.cloud_init.enabled.return_value = True
        self.assertIsNotNone(self.ovs_dpdk.setup_context())

    CPUINFO = "yardstick.benchmark.contexts.standalone.base.CpuInfo"

    @mock.patch("yardstick.benchmark.contexts.standalone.base.CpuInfo")
    def test_handle_cpu_configuration_isolcpus(self, mock_cpuinfo):
        my_mock = mock.Mock(autospec=CpuInfo)
        my_mock.isolcpus = CpuList('0-19')
        my_mock.ht_topo = mock.Mock(return_value=EXAMPLE_HT_TOPO)
        mock_cpuinfo.return_value = my_mock
        self.ovs_dpdk.nfvi_host = [{}]
        self.ovs_dpdk._specific_cpu_handling = mock.Mock()
        self.ovs_dpdk._vm_cpu_handling = mock.Mock()

        self.ovs_dpdk.handle_cpu_configuration()

        self.assertEquals(self.ovs_dpdk.cpu_model.cpu_cores_pool, CpuList('0-9'))


    def test__specific_cpu_handling(self):
        self.ovs_dpdk.cpu_model = CpuModel(mock.Mock())
        self.ovs_dpdk.cpu_model.exclude_ht_cores = False
        self.ovs_dpdk.cpu_model.cpu_cores_pool = CpuList('0-10')
        self.ovs_dpdk.cpu_properties = CpuProperties()
        self.ovs_dpdk.attrs = {
            'ovs_properties': {
                'pmd_threads': 2
            }
        }

        self.ovs_dpdk._specific_cpu_handling()

        self.assertEquals(self.ovs_dpdk.cpu_model.cpu_cores_pool, CpuList('3-10'))

    def test__vm_cpu_handling(self):
        self.ovs_dpdk.cpu_properties = CpuProperties()
        self.ovs_dpdk.servers = self.SERVERS
        self.ovs_dpdk.vm_flavor = self.VM_FLAVOR
        self.ovs_dpdk.cpu_model = CpuModel(mock.Mock)
        self.ovs_dpdk.cpu_model.exclude_ht_cores = False
        self.ovs_dpdk.cpu_model.cpu_cores_pool = CpuList('3-10')

        self.ovs_dpdk._vm_cpu_handling()

        expected = {
            'cpu_map': {
                0: str(CpuList('6-10')),
                1: str(CpuList('6-10')),
                2: '3',
                3: str(CpuList('6-10')),
                4: '4',
                5: str(CpuList('6-10')),
                6: '5',
                7: str(CpuList('6-10')),
            },
            'emulatorpin': '0',
        }

        self.assertEquals(self.ovs_dpdk.cpu_properties.vm['vnf__0'], expected)

    @mock.patch("yardstick.benchmark.contexts.standalone.base.CpuInfo")
    def test_handle_cpu_configuration_interface_numa(self, mock_cpuinfo):
        my_mock = mock.Mock(autospec=CpuInfo)
        my_mock.isolcpus = CpuList('')
        my_mock.numa_node_to_cpus = mock.Mock(return_value='0-9')
        my_mock.pci_to_numa_node = mock.Mock(return_value=0)
        my_mock.lscpu = {'On-line CPU(s) list': '0-19'}
        my_mock.ht_topo = mock.Mock(return_value=EXAMPLE_HT_TOPO)
        mock_cpuinfo.return_value = my_mock
        self.ovs_dpdk.nfvi_host = [{}]
        self.ovs_dpdk._specific_cpu_handling = mock.Mock()
        self.ovs_dpdk._vm_cpu_handling = mock.Mock()

        self.ovs_dpdk.networks = self.NETWORKS

        self.ovs_dpdk.handle_cpu_configuration()

        self.assertEquals(self.ovs_dpdk.cpu_model.cpu_cores_pool, CpuList('0-9'))

    @mock.patch("yardstick.benchmark.contexts.standalone.base.CpuInfo")
    def test_handle_cpu_configuration_all(self, mock_cpuinfo):
        my_mock = mock.Mock(autospec=CpuInfo)
        my_mock.isolcpus = None
        my_mock.numa_node_to_cpus = mock.Mock(return_value=None)
        my_mock.pci_to_numa_node = mock.Mock(return_value=0)
        my_mock.lscpu = {'On-line CPU(s) list': '0-19'}
        my_mock.ht_topo = mock.Mock(return_value=EXAMPLE_HT_TOPO)
        mock_cpuinfo.return_value = my_mock
        self.ovs_dpdk.nfvi_host = [{}]
        self.ovs_dpdk._specific_cpu_handling = mock.Mock()
        self.ovs_dpdk._vm_cpu_handling = mock.Mock()
        self.ovs_dpdk.networks = self.NETWORKS


        self.ovs_dpdk.handle_cpu_configuration()

        self.assertEquals(self.ovs_dpdk.cpu_model.cpu_cores_pool, CpuList('0-9'))

    @mock.patch("yardstick.benchmark.contexts.standalone.base.CpuInfo")
    def test_handle_cpu_configuration_ht_allowed(self, mock_cpuinfo):
        my_mock = mock.Mock(autospec=CpuInfo)
        my_mock.isolcpus = CpuList('0-19')
        my_mock.ht_topo = mock.Mock(return_value=EXAMPLE_HT_TOPO)
        mock_cpuinfo.return_value = my_mock
        self.ovs_dpdk.nfvi_host = [{}]
        self.ovs_dpdk._specific_cpu_handling = mock.Mock()
        self.ovs_dpdk._vm_cpu_handling = mock.Mock()

        self.ovs_dpdk.attrs['cpu_properties'] = {
            'allow_ht_threads': True,
        }
        self.ovs_dpdk.networks = self.NETWORKS

        self.ovs_dpdk.handle_cpu_configuration()

        self.assertEquals(self.ovs_dpdk.cpu_model.cpu_cores_pool, CpuList('0-9'))
