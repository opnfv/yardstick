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
""" Base class implementation for generic vnf implementation """

from __future__ import absolute_import

import posixpath
import time
import logging
import os
import re
import subprocess
from collections import Mapping

from multiprocessing import Queue, Value, Process

from six.moves import cStringIO

from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.scenarios.networking.vnf_generic import find_relative_file
from yardstick.network_services.helpers.cpu import CpuSysCores
from yardstick.network_services.helpers.samplevnf_helper import MultiPortConfig
from yardstick.network_services.nfvi.resource import ResourceProfile
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper
from yardstick.network_services.vnf_generic.vnf.base import GenericTrafficGen
from yardstick.network_services.utils import get_nsb_option

from trex_stl_lib.trex_stl_client import STLClient
from trex_stl_lib.trex_stl_client import LoggerApi
from trex_stl_lib.trex_stl_exceptions import STLError

from yardstick.ssh import AutoConnectSSH

DPDK_VERSION = "dpdk-16.07"

LOG = logging.getLogger(__name__)


REMOTE_TMP = "/tmp"


class VnfSshHelper(AutoConnectSSH):

    def __init__(self, node, bin_path, wait=None):
        self.node = node
        kwargs = self.args_from_node(self.node)
        if wait:
            kwargs.setdefault('wait', wait)

        super(VnfSshHelper, self).__init__(**kwargs)
        self.bin_path = bin_path

    @staticmethod
    def get_class():
        # must return static class name, anything else refers to the calling class
        # i.e. the subclass, not the superclass
        return VnfSshHelper

    def copy(self):
        # this copy constructor is different from SSH classes, since it uses node
        return self.get_class()(self.node, self.bin_path)

    def upload_config_file(self, prefix, content):
        cfg_file = os.path.join(REMOTE_TMP, prefix)
        LOG.debug(content)
        file_obj = cStringIO(content)
        self.put_file_obj(file_obj, cfg_file)
        return cfg_file

    def join_bin_path(self, *args):
        return os.path.join(self.bin_path, *args)

    def provision_tool(self, tool_path=None, tool_file=None):
        if tool_path is None:
            tool_path = self.bin_path
        return super(VnfSshHelper, self).provision_tool(tool_path, tool_file)


class SetupEnvHelper(object):

    CFG_CONFIG = os.path.join(REMOTE_TMP, "sample_config")
    CFG_SCRIPT = os.path.join(REMOTE_TMP, "sample_script")
    CORES = []
    DEFAULT_CONFIG_TPL_CFG = "sample.cfg"
    PIPELINE_COMMAND = ''
    VNF_TYPE = "SAMPLE"

    def __init__(self, vnfd_helper, ssh_helper, scenario_helper):
        super(SetupEnvHelper, self).__init__()
        self.vnfd_helper = vnfd_helper
        self.ssh_helper = ssh_helper
        self.scenario_helper = scenario_helper

    def _get_ports_gateway(self, name):
        routing_table = self.vnfd_helper.vdu0.get('routing_table', [])
        for route in routing_table:
            if name == route['if']:
                return route['gateway']
        return None

    def build_config(self):
        raise NotImplementedError

    def setup_vnf_environment(self):
        pass
        # raise NotImplementedError

    def tear_down(self):
        raise NotImplementedError


class DpdkVnfSetupEnvHelper(SetupEnvHelper):

    APP_NAME = 'DpdkVnf'
    DPDK_BIND_CMD = "sudo {dpdk_nic_bind} {force} -b {driver} {vpci}"
    DPDK_UNBIND_CMD = "sudo {dpdk_nic_bind} --force -b {driver} {vpci}"
    FIND_NET_CMD = "find /sys/class/net -lname '*{}*' -printf '%f'"

    HW_DEFAULT_CORE = 3
    SW_DEFAULT_CORE = 2

    DPDK_STATUS_DRIVER_RE = re.compile(r"(\d{2}:\d{2}\.\d).*drv=([-\w]+)")

    @staticmethod
    def _update_packet_type(ip_pipeline_cfg, traffic_options):
        match_str = 'pkt_type = ipv4'
        replace_str = 'pkt_type = {0}'.format(traffic_options['pkt_type'])
        pipeline_config_str = ip_pipeline_cfg.replace(match_str, replace_str)
        return pipeline_config_str

    @classmethod
    def _update_traffic_type(cls, ip_pipeline_cfg, traffic_options):
        traffic_type = traffic_options['traffic_type']

        if traffic_options['vnf_type'] is not cls.APP_NAME:
            match_str = 'traffic_type = 4'
            replace_str = 'traffic_type = {0}'.format(traffic_type)

        elif traffic_type == 4:
            match_str = 'pkt_type = ipv4'
            replace_str = 'pkt_type = ipv4'

        else:
            match_str = 'pkt_type = ipv4'
            replace_str = 'pkt_type = ipv6'

        pipeline_config_str = ip_pipeline_cfg.replace(match_str, replace_str)
        return pipeline_config_str

    def __init__(self, vnfd_helper, ssh_helper, scenario_helper):
        super(DpdkVnfSetupEnvHelper, self).__init__(vnfd_helper, ssh_helper, scenario_helper)
        self.all_ports = None
        self.bound_pci = None
        self._dpdk_nic_bind = None
        self.socket = None
        self.used_drivers = None

    @property
    def dpdk_nic_bind(self):
        if self._dpdk_nic_bind is None:
            self._dpdk_nic_bind = self.ssh_helper.provision_tool(tool_file="dpdk-devbind.py")
        return self._dpdk_nic_bind

    def _setup_hugepages(self):
        cmd = "awk '/Hugepagesize/ { print $2$3 }' < /proc/meminfo"
        hugepages = self.ssh_helper.execute(cmd)[1].rstrip()

        memory_path = \
            '/sys/kernel/mm/hugepages/hugepages-%s/nr_hugepages' % hugepages
        self.ssh_helper.execute("awk -F: '{ print $1 }' < %s" % memory_path)

        if hugepages == "2048kB":
            pages = 8192
        else:
            pages = 16

        self.ssh_helper.execute("echo %s | sudo tee %s" % (pages, memory_path))

    def _get_dpdk_port_num(self, name):
        interface = self.vnfd_helper.find_interface(name=name)
        return interface['virtual-interface']['dpdk_port_num']

    def build_config(self):
        vnf_cfg = self.scenario_helper.vnf_cfg
        task_path = self.scenario_helper.task_path

        lb_count = vnf_cfg.get('lb_count', 3)
        lb_config = vnf_cfg.get('lb_config', 'SW')
        worker_config = vnf_cfg.get('worker_config', '1C/1T')
        worker_threads = vnf_cfg.get('worker_threads', 3)

        traffic_type = self.scenario_helper.all_options.get('traffic_type', 4)
        traffic_options = {
            'traffic_type': traffic_type,
            'pkt_type': 'ipv%s' % traffic_type,
            'vnf_type': self.VNF_TYPE,
        }

        config_tpl_cfg = find_relative_file(self.DEFAULT_CONFIG_TPL_CFG, task_path)
        config_basename = posixpath.basename(self.CFG_CONFIG)
        script_basename = posixpath.basename(self.CFG_SCRIPT)
        multiport = MultiPortConfig(self.scenario_helper.topology,
                                    config_tpl_cfg,
                                    config_basename,
                                    self.vnfd_helper.interfaces,
                                    self.VNF_TYPE,
                                    lb_count,
                                    worker_threads,
                                    worker_config,
                                    lb_config,
                                    self.socket)

        multiport.generate_config()
        with open(self.CFG_CONFIG) as handle:
            new_config = handle.read()

        new_config = self._update_traffic_type(new_config, traffic_options)
        new_config = self._update_packet_type(new_config, traffic_options)

        self.ssh_helper.upload_config_file(config_basename, new_config)
        self.ssh_helper.upload_config_file(script_basename,
                                           multiport.generate_script(self.vnfd_helper))
        self.all_ports = multiport.port_pair_list

        LOG.info("Provision and start the %s", self.APP_NAME)
        self._build_pipeline_kwargs()
        return self.PIPELINE_COMMAND.format(**self.pipeline_kwargs)

    def _build_pipeline_kwargs(self):
        tool_path = self.ssh_helper.provision_tool(tool_file=self.APP_NAME)
        ports_len_hex = hex(2 ** (len(self.all_ports) + 1) - 1)
        self.pipeline_kwargs = {
            'cfg_file': self.CFG_CONFIG,
            'script': self.CFG_SCRIPT,
            'ports_len_hex': ports_len_hex,
            'tool_path': tool_path,
        }

    def _get_app_cpu(self):
        if self.CORES:
            return self.CORES

        vnf_cfg = self.scenario_helper.vnf_cfg
        sys_obj = CpuSysCores(self.ssh_helper)
        self.sys_cpu = sys_obj.get_core_socket()
        num_core = int(vnf_cfg["worker_threads"])
        if vnf_cfg.get("lb_config", "SW") == 'HW':
            num_core += self.HW_DEFAULT_CORE
        else:
            num_core += self.SW_DEFAULT_CORE
        app_cpu = self.sys_cpu[str(self.socket)][:num_core]
        return app_cpu

    def _get_cpu_sibling_list(self, cores=None):
        if cores is None:
            cores = self._get_app_cpu()
        sys_cmd_template = "%s/cpu%s/topology/thread_siblings_list"
        awk_template = "awk -F: '{ print $1 }' < %s"
        sys_path = "/sys/devices/system/cpu/"
        cpu_topology = []
        try:
            for core in cores:
                sys_cmd = sys_cmd_template % (sys_path, core)
                cpu_id = self.ssh_helper.execute(awk_template % sys_cmd)[1]
                cpu_topology.extend(cpu.strip() for cpu in cpu_id.split(','))

            return cpu_topology
        except Exception:
            return []

    def _validate_cpu_cfg(self):
        return self._get_cpu_sibling_list()

    def _find_used_drivers(self):
        cmd = "{0} -s".format(self.dpdk_nic_bind)
        rc, dpdk_status, _ = self.ssh_helper.execute(cmd)

        self.used_drivers = {
            vpci: (index, driver)
            for index, (vpci, driver)
            in enumerate(self.DPDK_STATUS_DRIVER_RE.findall(dpdk_status))
            if any(b.endswith(vpci) for b in self.bound_pci)
        }

    def setup_vnf_environment(self):
        self._setup_dpdk()
        resource = self._setup_resources()
        self._kill_vnf()
        self._detect_drivers()
        return resource

    def _kill_vnf(self):
        self.ssh_helper.execute("sudo pkill %s" % self.APP_NAME)

    def _setup_dpdk(self):
        """ setup dpdk environment needed for vnf to run """

        self._setup_hugepages()
        self.ssh_helper.execute("sudo modprobe uio && sudo modprobe igb_uio")

        exit_status = self.ssh_helper.execute("lsmod | grep -i igb_uio")[0]
        if exit_status == 0:
            return

        dpdk = self.ssh_helper.join_bin_path(DPDK_VERSION)
        dpdk_setup = self.ssh_helper.provision_tool(tool_file="nsb_setup.sh")
        exit_status = self.ssh_helper.execute("which {} >/dev/null 2>&1".format(dpdk))[0]
        if exit_status != 0:
            self.ssh_helper.execute("bash %s dpdk >/dev/null 2>&1" % dpdk_setup)

    def _setup_resources(self):
        interfaces = self.vnfd_helper.interfaces
        self.bound_pci = [v['virtual-interface']["vpci"] for v in interfaces]

        # what is this magic?  how do we know which socket is for which port?
        # what about quad-socket?
        if any(v[5] == "0" for v in self.bound_pci):
            self.socket = 0
        else:
            self.socket = 1

        cores = self._validate_cpu_cfg()
        return ResourceProfile(self.vnfd_helper.mgmt_interface,
                               interfaces=self.vnfd_helper.interfaces, cores=cores)

    def _detect_drivers(self):
        interfaces = self.vnfd_helper.interfaces

        self._find_used_drivers()
        for vpci, (index, _) in self.used_drivers.items():
            try:
                intf1 = next(v for v in interfaces if vpci == v['virtual-interface']['vpci'])
            except StopIteration:
                pass
            else:
                intf1['dpdk_port_num'] = index

        for vpci in self.bound_pci:
            self._bind_dpdk('igb_uio', vpci)
            time.sleep(2)

    def _bind_dpdk(self, driver, vpci, force=True):
        if force:
            force = '--force '
        else:
            force = ''
        cmd = self.DPDK_BIND_CMD.format(force=force,
                                        dpdk_nic_bind=self.dpdk_nic_bind,
                                        driver=driver,
                                        vpci=vpci)
        self.ssh_helper.execute(cmd)

    def _detect_and_bind_dpdk(self, vpci, driver):
        find_net_cmd = self.FIND_NET_CMD.format(vpci)
        exit_status, _, _ = self.ssh_helper.execute(find_net_cmd)
        if exit_status == 0:
            # already bound
            return None
        self._bind_dpdk(driver, vpci)
        exit_status, stdout, _ = self.ssh_helper.execute(find_net_cmd)
        if exit_status != 0:
            # failed to bind
            return None
        return stdout

    def _bind_kernel_devices(self):
        for intf in self.vnfd_helper.interfaces:
            vi = intf["virtual-interface"]
            stdout = self._detect_and_bind_dpdk(vi["vpci"], vi["driver"])
            if stdout is not None:
                vi["local_iface_name"] = posixpath.basename(stdout)

    def tear_down(self):
        for vpci, (_, driver) in self.used_drivers.items():
            self.ssh_helper.execute(self.DPDK_UNBIND_CMD.format(dpdk_nic_bind=self.dpdk_nic_bind,
                                                                driver=driver,
                                                                vpci=vpci))


class ResourceHelper(object):

    COLLECT_KPI = ''
    MAKE_INSTALL = 'cd {0} && make && sudo make install'
    RESOURCE_WORD = 'sample'

    COLLECT_MAP = {}

    def __init__(self, setup_helper):
        super(ResourceHelper, self).__init__()
        self.resource = None
        self.setup_helper = setup_helper
        self.ssh_helper = setup_helper.ssh_helper

    def setup(self):
        self.resource = self.setup_helper.setup_vnf_environment()

    def generate_cfg(self):
        pass

    def _collect_resource_kpi(self):
        result = {}
        status = self.resource.check_if_sa_running("collectd")[0]
        if status:
            result = self.resource.amqp_collect_nfvi_kpi()

        result = {"core": result}
        return result

    def start_collect(self):
        self.resource.initiate_systemagent(self.ssh_helper.bin_path)
        self.resource.start()
        self.resource.amqp_process_for_nfvi_kpi()

    def stop_collect(self):
        if self.resource:
            self.resource.stop()

    def collect_kpi(self):
        return self._collect_resource_kpi()


class ClientResourceHelper(ResourceHelper):

    RUN_DURATION = 60
    QUEUE_WAIT_TIME = 5
    SYNC_PORT = 1
    ASYNC_PORT = 2

    def __init__(self, setup_helper):
        super(ClientResourceHelper, self).__init__(setup_helper)
        self.vnfd_helper = setup_helper.vnfd_helper
        self.scenario_helper = setup_helper.scenario_helper

        self.client = None
        self.client_started = Value('i', 0)
        self.my_ports = None
        self._queue = Queue()
        self._result = {}
        self._terminated = Value('i', 0)
        self._vpci_ascending = None

    def _build_ports(self):
        self.my_ports = [0, 1]

    def get_stats(self, *args, **kwargs):
        try:
            return self.client.get_stats(*args, **kwargs)
        except STLError:
            LOG.exception("TRex client not connected")
            return {}

    def generate_samples(self, key=None, default=None):
        last_result = self.get_stats(self.my_ports)
        key_value = last_result.get(key, default)

        if not isinstance(last_result, Mapping):  # added for mock unit test
            self._terminated.value = 1
            return {}

        samples = {}
        for vpci_idx, vpci in enumerate(self._vpci_ascending):
            name = self.vnfd_helper.find_virtual_interface(vpci=vpci)["name"]
            # fixme: VNFDs KPIs values needs to be mapped to TRex structure
            xe_value = last_result.get(vpci_idx, {})
            samples[name] = {
                "rx_throughput_fps": float(xe_value.get("rx_pps", 0.0)),
                "tx_throughput_fps": float(xe_value.get("tx_pps", 0.0)),
                "rx_throughput_mbps": float(xe_value.get("rx_bps", 0.0)),
                "tx_throughput_mbps": float(xe_value.get("tx_bps", 0.0)),
                "in_packets": int(xe_value.get("ipackets", 0)),
                "out_packets": int(xe_value.get("opackets", 0)),
            }
            if key:
                samples[name][key] = key_value
        return samples

    def _run_traffic_once(self, traffic_profile):
        traffic_profile.execute(self)
        self.client_started.value = 1
        time.sleep(self.RUN_DURATION)
        samples = self.generate_samples()
        time.sleep(self.QUEUE_WAIT_TIME)
        self._queue.put(samples)

    def run_traffic(self, traffic_profile):
        # fixme: fix passing correct trex config file,
        # instead of searching the default path
        try:
            self._build_ports()
            self.client = self._connect()
            self.client.reset(ports=self.my_ports)
            self.client.remove_all_streams(self.my_ports)  # remove all streams
            traffic_profile.register_generator(self)

            while self._terminated.value == 0:
                self._run_traffic_once(traffic_profile)

            self.client.stop(self.my_ports)
            self.client.disconnect()
            self._terminated.value = 0
        except STLError:
            if self._terminated.value:
                LOG.debug("traffic generator is stopped")
                return  # return if trex/tg server is stopped.
            raise

    def terminate(self):
        self._terminated.value = 1  # stop client

    def clear_stats(self, ports=None):
        if ports is None:
            ports = self.my_ports
        self.client.clear_stats(ports=ports)

    def start(self, ports=None, *args, **kwargs):
        if ports is None:
            ports = self.my_ports
        self.client.start(ports=ports, *args, **kwargs)

    def collect_kpi(self):
        if not self._queue.empty():
            kpi = self._queue.get()
            self._result.update(kpi)
        LOG.debug("Collect {0} KPIs {1}".format(self.RESOURCE_WORD, self._result))
        return self._result

    def _connect(self, client=None):
        if client is None:
            client = STLClient(username=self.vnfd_helper.mgmt_interface["user"],
                               server=self.vnfd_helper.mgmt_interface["ip"],
                               verbose_level=LoggerApi.VERBOSE_QUIET)

        # try to connect with 5s intervals, 30s max
        for idx in range(6):
            try:
                client.connect()
                break
            except STLError:
                LOG.info("Unable to connect to Trex Server.. Attempt %s", idx)
                time.sleep(5)
        return client


class Rfc2544ResourceHelper(object):

    DEFAULT_CORRELATED_TRAFFIC = False
    DEFAULT_LATENCY = False
    DEFAULT_TOLERANCE = '0.0001 - 0.0001'

    def __init__(self, scenario_helper):
        super(Rfc2544ResourceHelper, self).__init__()
        self.scenario_helper = scenario_helper
        self._correlated_traffic = None
        self.iteration = Value('i', 0)
        self._latency = None
        self._rfc2544 = None
        self._tolerance_low = None
        self._tolerance_high = None

    @property
    def rfc2544(self):
        if self._rfc2544 is None:
            self._rfc2544 = self.scenario_helper.all_options['rfc2544']
        return self._rfc2544

    @property
    def tolerance_low(self):
        if self._tolerance_low is None:
            self.get_rfc_tolerance()
        return self._tolerance_low

    @property
    def tolerance_high(self):
        if self._tolerance_high is None:
            self.get_rfc_tolerance()
        return self._tolerance_high

    @property
    def correlated_traffic(self):
        if self._correlated_traffic is None:
            self._correlated_traffic = \
                self.get_rfc2544('correlated_traffic', self.DEFAULT_CORRELATED_TRAFFIC)

        return self._correlated_traffic

    @property
    def latency(self):
        if self._latency is None:
            self._latency = self.get_rfc2544('latency', self.DEFAULT_LATENCY)
        return self._latency

    def get_rfc2544(self, name, default=None):
        return self.rfc2544.get(name, default)

    def get_rfc_tolerance(self):
        tolerance_str = self.get_rfc2544('allowed_drop_rate', self.DEFAULT_TOLERANCE)
        tolerance_iter = iter(sorted(float(t.strip()) for t in tolerance_str.split('-')))
        self._tolerance_low = next(tolerance_iter)
        self._tolerance_high = next(tolerance_iter, self.tolerance_low)


class SampleVNFDeployHelper(object):

    SAMPLE_VNF_REPO = 'https://gerrit.opnfv.org/gerrit/samplevnf'
    REPO_NAME = posixpath.basename(SAMPLE_VNF_REPO)
    SAMPLE_REPO_DIR = os.path.join('~/', REPO_NAME)

    def __init__(self, vnfd_helper, ssh_helper):
        super(SampleVNFDeployHelper, self).__init__()
        self.ssh_helper = ssh_helper
        self.vnfd_helper = vnfd_helper

    DISABLE_DEPLOY = True

    def deploy_vnfs(self, app_name):
        # temp disable for now
        if self.DISABLE_DEPLOY:
            return

        vnf_bin = self.ssh_helper.join_bin_path(app_name)
        exit_status = self.ssh_helper.execute("which %s" % vnf_bin)[0]
        if not exit_status:
            return

        subprocess.check_output(["rm", "-rf", self.REPO_NAME])
        subprocess.check_output(["git", "clone", self.SAMPLE_VNF_REPO])
        time.sleep(2)
        self.ssh_helper.execute("rm -rf %s" % self.SAMPLE_REPO_DIR)
        self.ssh_helper.put(self.REPO_NAME, self.SAMPLE_REPO_DIR, True)

        build_script = os.path.join(self.SAMPLE_REPO_DIR, 'tools/vnf_build.sh')
        time.sleep(2)
        http_proxy = os.environ.get('http_proxy', '')
        cmd = "sudo -E %s -s -p='%s'" % (build_script, http_proxy)
        LOG.debug(cmd)
        self.ssh_helper.execute(cmd)
        vnf_bin_loc = os.path.join(self.SAMPLE_REPO_DIR, "VNFs", app_name, "build", app_name)
        self.ssh_helper.execute("sudo mkdir -p %s" % self.ssh_helper.bin_path)
        self.ssh_helper.execute("sudo cp %s %s" % (vnf_bin_loc, vnf_bin))


class ScenarioHelper(object):

    DEFAULT_VNF_CFG = {
        'lb_config': 'SW',
        'lb_count': 1,
        'worker_config': '1C/1T',
        'worker_threads': 1,
    }

    def __init__(self, name):
        self.name = name
        self.scenario_cfg = None

    @property
    def task_path(self):
        return self.scenario_cfg["task_path"]

    @property
    def nodes(self):
        return self.scenario_cfg['nodes']

    @property
    def all_options(self):
        return self.scenario_cfg["options"]

    @property
    def options(self):
        return self.all_options[self.name]

    @property
    def vnf_cfg(self):
        return self.options.get('vnf_config', self.DEFAULT_VNF_CFG)

    @property
    def topology(self):
        return self.scenario_cfg['topology']


class SampleVNF(GenericVNF):
    """ Class providing file-like API for generic VNF implementation """

    VNF_PROMPT = "pipeline>"
    WAIT_TIME = 1

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        super(SampleVNF, self).__init__(name, vnfd)
        self.bin_path = get_nsb_option('bin_path', '')

        self.scenario_helper = ScenarioHelper(self.name)
        self.ssh_helper = VnfSshHelper(self.vnfd_helper.mgmt_interface, self.bin_path)

        if setup_env_helper_type is None:
            setup_env_helper_type = SetupEnvHelper

        self.setup_helper = setup_env_helper_type(self.vnfd_helper,
                                                  self.ssh_helper,
                                                  self.scenario_helper)

        self.deploy_helper = SampleVNFDeployHelper(vnfd, self.ssh_helper)

        if resource_helper_type is None:
            resource_helper_type = ResourceHelper

        self.resource_helper = resource_helper_type(self.setup_helper)

        self.all_ports = None
        self.context_cfg = None
        self.nfvi_context = None
        self.pipeline_kwargs = {}
        self.priv_ports = None
        self.pub_ports = None
        # TODO(esm): make QueueFileWrapper invert-able so that we
        #            never have to manage the queues
        self.q_in = Queue()
        self.q_out = Queue()
        self.queue_wrapper = None
        self.run_kwargs = {}
        self.scenario_cfg = None
        self.tg_port_pairs = None
        self.used_drivers = {}
        self.vnf_port_pairs = None
        self._vnf_process = None

    def _get_route_data(self, route_index, route_type):
        route_iter = iter(self.vnfd_helper.vdu0.get('nd_route_tbl', []))
        for _ in range(route_index):
            next(route_iter, '')
        return next(route_iter, {}).get(route_type, '')

    def _get_port0localip6(self):
        return_value = self._get_route_data(0, 'network')
        LOG.info("_get_port0localip6 : %s", return_value)
        return return_value

    def _get_port1localip6(self):
        return_value = self._get_route_data(1, 'network')
        LOG.info("_get_port1localip6 : %s", return_value)
        return return_value

    def _get_port0prefixlen6(self):
        return_value = self._get_route_data(0, 'netmask')
        LOG.info("_get_port0prefixlen6 : %s", return_value)
        return return_value

    def _get_port1prefixlen6(self):
        return_value = self._get_route_data(1, 'netmask')
        LOG.info("_get_port1prefixlen6 : %s", return_value)
        return return_value

    def _get_port0gateway6(self):
        return_value = self._get_route_data(0, 'network')
        LOG.info("_get_port0gateway6 : %s", return_value)
        return return_value

    def _get_port1gateway6(self):
        return_value = self._get_route_data(1, 'network')
        LOG.info("_get_port1gateway6 : %s", return_value)
        return return_value

    def _start_vnf(self):
        self.queue_wrapper = QueueFileWrapper(self.q_in, self.q_out, self.VNF_PROMPT)
        self._vnf_process = Process(target=self._run)
        self._vnf_process.start()

    def _vnf_up_post(self):
        pass

    def instantiate(self, scenario_cfg, context_cfg):
        self.scenario_helper.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.nfvi_context = Context.get_context_from_server(self.scenario_helper.nodes[self.name])
        # self.nfvi_context = None

        self.deploy_helper.deploy_vnfs(self.APP_NAME)
        self.resource_helper.setup()
        self._start_vnf()

    def wait_for_instantiate(self):
        buf = []
        time.sleep(self.WAIT_TIME)  # Give some time for config to load
        while True:
            if not self._vnf_process.is_alive():
                raise RuntimeError("%s VNF process died." % self.APP_NAME)

            # TODO(esm): move to QueueFileWrapper
            while self.q_out.qsize() > 0:
                buf.append(self.q_out.get())
                message = ''.join(buf)
                if self.VNF_PROMPT in message:
                    LOG.info("%s VNF is up and running.", self.APP_NAME)
                    self._vnf_up_post()
                    self.queue_wrapper.clear()
                    self.resource_helper.start_collect()
                    return self._vnf_process.exitcode

                if "PANIC" in message:
                    raise RuntimeError("Error starting %s VNF." %
                                       self.APP_NAME)

            LOG.info("Waiting for %s VNF to start.. ", self.APP_NAME)
            time.sleep(1)

    def _build_run_kwargs(self):
        self.run_kwargs = {
            'stdin': self.queue_wrapper,
            'stdout': self.queue_wrapper,
            'keep_stdin_open': True,
            'pty': True,
        }

    def _build_config(self):
        return self.setup_helper.build_config()

    def _run(self):
        # we can't share ssh paramiko objects to force new connection
        self.ssh_helper.drop_connection()
        cmd = self._build_config()
        # kill before starting
        self.ssh_helper.execute("pkill {}".format(self.APP_NAME))

        LOG.debug(cmd)
        self._build_run_kwargs()
        self.ssh_helper.run(cmd, **self.run_kwargs)

    def vnf_execute(self, cmd, wait_time=2):
        """ send cmd to vnf process """

        LOG.info("%s command: %s", self.APP_NAME, cmd)
        self.q_in.put("{}\r\n".format(cmd))
        time.sleep(wait_time)
        output = []
        while self.q_out.qsize() > 0:
            output.append(self.q_out.get())
        return "".join(output)

    def _tear_down(self):
        pass

    def terminate(self):
        self.vnf_execute("quit")
        if self._vnf_process:
            self._vnf_process.terminate()
        self.ssh_helper.execute("sudo pkill %s" % self.APP_NAME)
        self._tear_down()
        self.resource_helper.stop_collect()

    def get_stats(self, *args, **kwargs):
        """
        Method for checking the statistics

        :return:
           VNF statistics
        """
        cmd = 'p {0} stats'.format(self.APP_WORD)
        out = self.vnf_execute(cmd)
        return out

    def collect_kpi(self):
        stats = self.get_stats()
        m = re.search(self.COLLECT_KPI, stats, re.MULTILINE)
        if m:
            result = {k: int(m.group(v)) for k, v in self.COLLECT_MAP.items()}
            result["collect_stats"] = self.resource_helper.collect_kpi()
        else:
            result = {
                "packets_in": 0,
                "packets_fwd": 0,
                "packets_dropped": 0,
            }
        LOG.debug("%s collect KPIs %s", self.APP_NAME, result)
        return result


class SampleVNFTrafficGen(GenericTrafficGen):
    """ Class providing file-like API for generic traffic generator """

    APP_NAME = 'Sample'
    RUN_WAIT = 1

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        super(SampleVNFTrafficGen, self).__init__(name, vnfd)
        self.bin_path = get_nsb_option('bin_path', '')
        self.name = "tgen__1"  # name in topology file

        self.scenario_helper = ScenarioHelper(self.name)
        self.ssh_helper = VnfSshHelper(self.vnfd_helper.mgmt_interface, self.bin_path, wait=True)

        if setup_env_helper_type is None:
            setup_env_helper_type = SetupEnvHelper

        self.setup_helper = setup_env_helper_type(self.vnfd_helper,
                                                  self.ssh_helper,
                                                  self.scenario_helper)

        if resource_helper_type is None:
            resource_helper_type = ClientResourceHelper

        self.resource_helper = resource_helper_type(self.setup_helper)

        self.runs_traffic = True
        self.traffic_finished = False
        self.tg_port_pairs = None
        self._tg_process = None
        self._traffic_process = None

    def _start_server(self):
        # we can't share ssh paramiko objects to force new connection
        self.ssh_helper.drop_connection()

    def instantiate(self, scenario_cfg, context_cfg):
        self.scenario_helper.scenario_cfg = scenario_cfg
        self.resource_helper.generate_cfg()
        self.setup_helper.setup_vnf_environment()
        self.resource_helper.setup()

        LOG.info("Starting %s server...", self.APP_NAME)
        self._tg_process = Process(target=self._start_server)
        self._tg_process.start()

    def wait_for_instantiate(self):
        # overridden by subclasses
        return self._wait_for_process()

    def _check_status(self):
        raise NotImplementedError

    def _wait_for_process(self):
        while True:
            if not self._tg_process.is_alive():
                raise RuntimeError("%s traffic generator process died." % self.APP_NAME)
            LOG.info("Waiting for %s TG Server to start.. ", self.APP_NAME)
            time.sleep(1)
            status = self._check_status()
            if status == 0:
                LOG.info("%s TG Server is up and running.", self.APP_NAME)
                return self._tg_process.exitcode

    def _traffic_runner(self, traffic_profile):
        LOG.info("Starting %s client...", self.APP_NAME)
        self.resource_helper.run_traffic(traffic_profile)

    def run_traffic(self, traffic_profile):
        """ Generate traffic on the wire according to the given params.
        Method is non-blocking, returns immediately when traffic process
        is running. Mandatory.

        :param traffic_profile:
        :return: True/False
        """
        self._traffic_process = Process(target=self._traffic_runner,
                                        args=(traffic_profile,))
        self._traffic_process.start()
        # Wait for traffic process to start
        while self.resource_helper.client_started.value == 0:
            time.sleep(self.RUN_WAIT)
            # what if traffic process takes a few seconds to start?
            if not self._traffic_process.is_alive():
                break

        return self._traffic_process.is_alive()

    def listen_traffic(self, traffic_profile):
        """ Listen to traffic with the given parameters.
        Method is non-blocking, returns immediately when traffic process
        is running. Optional.

        :param traffic_profile:
        :return: True/False
        """
        pass

    def verify_traffic(self, traffic_profile):
        """ Verify captured traffic after it has ended. Optional.

        :param traffic_profile:
        :return: dict
        """
        pass

    def collect_kpi(self):
        result = self.resource_helper.collect_kpi()
        LOG.debug("%s collect KPIs %s", self.APP_NAME, result)
        return result

    def terminate(self):
        """ After this method finishes, all traffic processes should stop. Mandatory.

        :return: True/False
        """
        self.traffic_finished = True
        if self._traffic_process is not None:
            self._traffic_process.terminate()
