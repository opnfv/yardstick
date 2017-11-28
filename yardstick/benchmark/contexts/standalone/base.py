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

import copy
import logging
import os
import tempfile
from yardstick import ssh
from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.contexts import common
from yardstick.common.constants import ANSIBLE_DIR
from yardstick.common.cpu_model import CpuList
from collections import OrderedDict
from yardstick.benchmark.contexts.standalone import model
from yardstick.network_services.helpers.dpdkbindnic_helper import DpdkBindHelper
from yardstick.common.ansible_common import AnsibleCommon
from yardstick.common.utils import MethodCallsOrder
from yardstick.common.cpu_model import CpuInfo
from yardstick.common.cpu_model import CpuModel

LOG = logging.getLogger(__name__)


class CpuProperties(object):
    KEYS = ['emulator_threads',
            'emulator_pin',
            'cpu_cores_pool',
            'allow_ht_threads',
            'pmd_threads',
            'pmd_thread_pin',
            ]

    def __init__(self, props):
        for a_key in self.KEYS:
            self.__setattr__(a_key, props.get(a_key))


class CloudInit(object):

    DEFAULT_IMAGE_PATH = '/var/lib/yardstick'

    def __init__(self, node):
        self.node = node
        self.cfg = node.get('cloud_init', {})

    def generate_iso_images(self):
        if not self.cfg.get('generate_iso_images', False):
            return

        tmpdir = tempfile.mkdtemp(prefix='ansible-')
        playbook_vars = copy.deepcopy(self.cfg)
        playbook_vars['vm_path'] = tmpdir
        ansible_exec = AnsibleCommon(nodes=[self.node], test_vars=playbook_vars)
        ansible_exec.gen_inventory_ini_dict()
        ansible_exec.execute_ansible(os.path.join(ANSIBLE_DIR, 'build_cloudinit_iso_images.yml'),
                                     tmpdir)

    @property
    def iso_image_path(self):
        return self.cfg.get('iso_image_path', self.DEFAULT_IMAGE_PATH)

    @property
    def enabled(self):
        return self.cfg.get('enabled', False)


class StandaloneBase(Context):

    __context_type__ = "StandaloneBase"

    ROLE = None
    DOMAIN_XML_FILE = '/tmp/vm_ovs_%d.xml'

    METHOD_CALL_ORDER = ['init', 'deploy', 'setup_context', 'undeploy']

    def __init__(self):
        self.file_path = None
        self.first_run = True
        self.dpdk_bind_helper = None
        self.vm_names = []
        self.name = None
        self.nfvi_host = []
        self.nodes = []
        self.attrs = {}
        self.vm_flavor = None
        self.servers = None
        self.vm_deploy = None
        self.host_mgmt = None
        self.connection = None
        self.networks = None
        self.cloud_init = None
        self.cpu_properties = {}
        MethodCallsOrder.add(self, self.METHOD_CALL_ORDER)
        super(StandaloneBase, self).__init__()

    @MethodCallsOrder.validate
    def init(self, attrs):
        """initializes itself from the supplied arguments"""
        self.name = attrs["name"]
        self.file_path = attrs.get("file", "pod.yaml")

        self.nodes, self.nfvi_host, self.host_mgmt = \
            model.parse_pod_file(self.file_path, self.ROLE)

        self.attrs = attrs
        self.vm_flavor = attrs.get('flavor', {})
        self.servers = OrderedDict(sorted(attrs.get('servers', {}).items()))
        self.vm_deploy = attrs.get("vm_deploy", True)
        # add optional static network definition
        self.networks = OrderedDict(sorted(attrs.get("networks", {}).items()))

        self.cloud_init = CloudInit(self.nfvi_host[0])

        LOG.debug("Nodes: %r", self.nodes)
        LOG.debug("NFVi Node: %r", self.nfvi_host)
        LOG.debug("Networks: %r", self.networks)

    def _specific_deploy(self):  # pragma: no cover
        # to be implemented by a subclass
        raise NotImplemented

    def _vm_cpu_handling(self):
        self.cpu_properties.vm = {}
        extra_spec = self.vm_flavor.get('extra_specs', {})
        cpu_cores = extra_spec.get('hw:cpu_cores', '2')
        cpu_threads = extra_spec.get('hw:cpu_threads', '2')
        vcpus = list(range(int(cpu_cores) * int(cpu_threads)))

        for key, vnf in self.servers.items():
            cpu_map = {}
            self.cpu_properties.vm[key] = {
                'cpu_map': cpu_map,
                'emulatorpin': None,
            }
            if vnf.get('cpu_properties'):
                isolate_cpus = vnf['cpu_properties'].get('isolate_cpus')
                for vcpu in isolate_cpus:
                    cpu_map[vcpu] = str(self.cpu_model.allocate(1))
                    LOG.info('VM {} vcpu {} pinned to core {}'.format(key,
                                                                      vcpu,
                                                                      cpu_map[vcpu]))
                emulatorpin = vnf['cpu_properties'].get('emulatorpin')
                if emulatorpin is None:
                    emulatorpin = self.cpu_properties.emulator_pin
                if emulatorpin is None:
                    emulatorpin = self.cpu_model.allocate(self.cpu_properties.emulator_threads)
                self.cpu_properties.vm[key]['emulatorpin'] = emulatorpin
        # whatever is not allocated, pinned to the remaining cores from the free pool.
        # If not done, it would be pinned to all cpus by the libvirt.
        free_cores = str(self.cpu_model.cpu_cores_pool)
        for vm in self.cpu_properties.vm.values():
            isolated = vm['cpu_map'].keys()
            if vm['emulatorpin'] is None:
                vm['emulatorpin'] = free_cores
            for cpu in vcpus:
                if cpu in isolated:
                    continue
                vm['cpu_map'][cpu] = free_cores

    def handle_cpu_configuration(self):
        # Detect witch CPU cores we will work with
        cpu_info = CpuInfo(self.connection)
        cpu_pool = None

        self.cpu_properties = CpuProperties(self.nfvi_host[0].get('cpu_properties', {}))

        cpu_pool = CpuList(self.cpu_properties.cpu_cores_pool)
        exclude_ht_cores = not bool(self.cpu_properties.allow_ht_threads)

        if not cpu_pool:
            cpu_pool = cpu_info.isolcpus
        if not cpu_pool:
            try:
                first_interface = self.networks.keys()[0]
                pci_addr = self.networks[first_interface]['phy_port']
                numa_node = cpu_info.pci_to_numa_node(pci_addr)
                cpu_pool = cpu_info.numa_node_to_cpus(numa_node)
            except KeyError:
                pass
        if not cpu_pool:
            cpu_pool = cpu_info.lscpu['On-line CPU(s) list']
        if not cpu_pool:
            raise Exception('Cannot get list of CPUs')

        self.cpu_model = CpuModel(cpu_info)
        self.cpu_model.exclude_ht_cores = exclude_ht_cores
        self.cpu_model.cpu_cores_pool = cpu_pool

        # ovs-dpdk satisfies the dpdk's pmd's requirements
        self._specific_cpu_handling()

        # from the remaining cores, the VM vcpus that should be isolated get their dedicated
        # cores. The rest is pinned to the remaining free cores from our pool.
        self._vm_cpu_handling()

    @MethodCallsOrder.validate
    def deploy(self):
        if not self.vm_deploy:
            return

        self.connection = ssh.SSH.from_node(self.host_mgmt)
        self.dpdk_bind_helper = DpdkBindHelper(self.connection)
        self.dpdk_bind_helper.read_status()
        self.dpdk_bind_helper.save_used_drivers()
        model.install_req_libs(self.connection)
        model.populate_nic_details(self.connection, self.networks, self.dpdk_bind_helper)

        self.handle_cpu_configuration()

        self._specific_deploy()
        self.nodes = self.setup_context()

        LOG.debug("Waiting for VM to come up...")
        model.wait_for_vnfs_to_start(self.connection, self.servers, self.nodes)

    def _specific_undeploy(self):  # pragma: no cover
        # to be implemented by a subclass
        raise NotImplemented

    @MethodCallsOrder.validate
    def undeploy(self):
        if not self.vm_deploy:
            return

        for vm in self.vm_names:
            model.check_if_vm_exists_and_delete(vm, self.connection)

        self._specific_undeploy()

    def _get_server(self, attr_name):
        return common.get_server(self, attr_name)

    def _get_network(self, attr_name):
        return common.get_network(self, attr_name)

    @MethodCallsOrder.validate
    def setup_context(self):
        nodes = []

        self._configure_nics()

        for vm_index, (key, vnf) in enumerate(self.servers.items()):
            cfg = self.DOMAIN_XML_FILE % vm_index
            vm_name = "vm_%d" % vm_index

            # 1. Check and delete VM if already exists
            model.check_if_vm_exists_and_delete(vm_name, self.connection)

            vcpu, mac = model.build_vm_xml(self.connection, self.vm_flavor, cfg, vm_name, vm_index)

            for port_index, (vkey, vfs) in enumerate(sorted(vnf["network_ports"].items())):
                if vkey == "mgmt":
                    continue
                self._enable_interfaces(vm_index, port_index, vfs, cfg)

            if self.cloud_init.enabled:
                self.cloud_init.generate_iso_images()
                iso_image_path = '{0}/vm{1}/vm{1}-cidata.iso'.format(
                    self.cloud_init.iso_image_path,
                    vm_index,
                )
                model.add_nodata_source(cfg, iso_image_path)

            model.add_vm_vcpu_pinning(key, cfg, self.cpu_properties)

            # copy xml to target...
            self.connection.put(cfg, cfg)

            LOG.info("virsh create ...")
            model.virsh_create_vm(self.connection, cfg)

            self.vm_names.append(vm_name)

            # build vnf node details
            nodes.append(model.generate_vnf_instance(self.vm_flavor, self.networks,
                                                     self.host_mgmt.get('ip'), key, vnf, mac))

        return nodes
