# Copyright (c) 2016-2018 Intel Corporation
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

from collections import Mapping
import logging
from multiprocessing import Queue, Value, Process

import os
import posixpath
import re
import subprocess
import time

import six

from trex_stl_lib.trex_stl_client import LoggerApi
from trex_stl_lib.trex_stl_client import STLClient
from trex_stl_lib.trex_stl_exceptions import STLError
from yardstick.benchmark.contexts.base import Context
from yardstick.common import exceptions as y_exceptions
from yardstick.common import messaging
from yardstick.common.messaging import payloads
from yardstick.common.process import check_if_process_failed
from yardstick.common import utils
from yardstick.network_services import constants
from yardstick.network_services.helpers.dpdkbindnic_helper import DpdkBindHelper, DpdkNode
from yardstick.network_services.helpers.samplevnf_helper import MultiPortConfig
from yardstick.network_services.helpers.samplevnf_helper import PortPairs
from yardstick.network_services.nfvi.resource import ResourceProfile
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.vnf_generic.vnf.base import GenericTrafficGen
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper
from yardstick.network_services.vnf_generic.vnf.vnf_ssh_helper import VnfSshHelper


LOG = logging.getLogger(__name__)


class SetupEnvHelper(object):

    CFG_CONFIG = os.path.join(constants.REMOTE_TMP, "sample_config")
    CFG_SCRIPT = os.path.join(constants.REMOTE_TMP, "sample_script")
    DEFAULT_CONFIG_TPL_CFG = "sample.cfg"
    PIPELINE_COMMAND = ''
    VNF_TYPE = "SAMPLE"

    def __init__(self, vnfd_helper, ssh_helper, scenario_helper):
        super(SetupEnvHelper, self).__init__()
        self.vnfd_helper = vnfd_helper
        self.ssh_helper = ssh_helper
        self.scenario_helper = scenario_helper

    def build_config(self):
        raise NotImplementedError

    def setup_vnf_environment(self):
        pass

    def kill_vnf(self):
        pass

    def tear_down(self):
        raise NotImplementedError


class DpdkVnfSetupEnvHelper(SetupEnvHelper):

    APP_NAME = 'DpdkVnf'
    FIND_NET_CMD = "find /sys/class/net -lname '*{}*' -printf '%f'"
    NR_HUGEPAGES_PATH = '/proc/sys/vm/nr_hugepages'

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
        self.socket = None
        self.used_drivers = None
        self.dpdk_bind_helper = DpdkBindHelper(ssh_helper)

    def _setup_hugepages(self):
        meminfo = utils.read_meminfo(self.ssh_helper)
        hp_size_kb = int(meminfo['Hugepagesize'])
        hugepages_gb = self.scenario_helper.all_options.get('hugepages_gb', 16)
        nr_hugepages = int(abs(hugepages_gb * 1024 * 1024 / hp_size_kb))
        self.ssh_helper.execute('echo %s | sudo tee %s' %
                                (nr_hugepages, self.NR_HUGEPAGES_PATH))
        hp = six.BytesIO()
        self.ssh_helper.get_file_obj(self.NR_HUGEPAGES_PATH, hp)
        nr_hugepages_set = int(hp.getvalue().decode('utf-8').splitlines()[0])
        LOG.info('Hugepages size (kB): %s, number claimed: %s, number set: %s',
                 hp_size_kb, nr_hugepages, nr_hugepages_set)

    def build_config(self):
        vnf_cfg = self.scenario_helper.vnf_cfg
        task_path = self.scenario_helper.task_path

        config_file = vnf_cfg.get('file')
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

        config_tpl_cfg = utils.find_relative_file(self.DEFAULT_CONFIG_TPL_CFG,
                                                  task_path)
        config_basename = posixpath.basename(self.CFG_CONFIG)
        script_basename = posixpath.basename(self.CFG_SCRIPT)
        multiport = MultiPortConfig(self.scenario_helper.topology,
                                    config_tpl_cfg,
                                    config_basename,
                                    self.vnfd_helper,
                                    self.VNF_TYPE,
                                    lb_count,
                                    worker_threads,
                                    worker_config,
                                    lb_config,
                                    self.socket)

        multiport.generate_config()
        if config_file:
            with utils.open_relative_file(config_file, task_path) as infile:
                new_config = ['[EAL]']
                vpci = []
                for port in self.vnfd_helper.port_pairs.all_ports:
                    interface = self.vnfd_helper.find_interface(name=port)
                    vpci.append(interface['virtual-interface']["vpci"])
                new_config.extend('w = {0}'.format(item) for item in vpci)
                new_config = '\n'.join(new_config) + '\n' + infile.read()
        else:
            with open(self.CFG_CONFIG) as handle:
                new_config = handle.read()
            new_config = self._update_traffic_type(new_config, traffic_options)
            new_config = self._update_packet_type(new_config, traffic_options)
        self.ssh_helper.upload_config_file(config_basename, new_config)
        self.ssh_helper.upload_config_file(script_basename,
                                           multiport.generate_script(self.vnfd_helper))

        LOG.info("Provision and start the %s", self.APP_NAME)
        self._build_pipeline_kwargs()
        return self.PIPELINE_COMMAND.format(**self.pipeline_kwargs)

    def _build_pipeline_kwargs(self):
        tool_path = self.ssh_helper.provision_tool(tool_file=self.APP_NAME)
        # count the number of actual ports in the list of pairs
        # remove duplicate ports
        # this is really a mapping from LINK ID to DPDK PMD ID
        # e.g. 0x110 maps LINK0 -> PMD_ID_1, LINK1 -> PMD_ID_2
        #      0x1010 maps LINK0 -> PMD_ID_1, LINK1 -> PMD_ID_3
        ports = self.vnfd_helper.port_pairs.all_ports
        port_nums = self.vnfd_helper.port_nums(ports)
        # create mask from all the dpdk port numbers
        ports_mask_hex = hex(sum(2 ** num for num in port_nums))
        self.pipeline_kwargs = {
            'cfg_file': self.CFG_CONFIG,
            'script': self.CFG_SCRIPT,
            'port_mask_hex': ports_mask_hex,
            'tool_path': tool_path,
        }

    def setup_vnf_environment(self):
        self._setup_dpdk()
        self.kill_vnf()
        # bind before _setup_resources so we can use dpdk_port_num
        self._detect_and_bind_drivers()
        resource = self._setup_resources()
        return resource

    def kill_vnf(self):
        # pkill is not matching, debug with pgrep
        self.ssh_helper.execute("sudo pgrep -lax  %s" % self.APP_NAME)
        self.ssh_helper.execute("sudo ps aux | grep -i %s" % self.APP_NAME)
        # have to use exact match
        # try using killall to match
        self.ssh_helper.execute("sudo killall %s" % self.APP_NAME)

    def _setup_dpdk(self):
        """Setup DPDK environment needed for VNF to run"""
        self._setup_hugepages()
        self.dpdk_bind_helper.load_dpdk_driver()

        exit_status = self.dpdk_bind_helper.check_dpdk_driver()
        if exit_status == 0:
            return

    def get_collectd_options(self):
        options = self.scenario_helper.all_options.get("collectd", {})
        # override with specific node settings
        options.update(self.scenario_helper.options.get("collectd", {}))
        return options

    def _setup_resources(self):
        # what is this magic?  how do we know which socket is for which port?
        # what about quad-socket?
        if any(v[5] == "0" for v in self.bound_pci):
            self.socket = 0
        else:
            self.socket = 1

        # implicit ordering, presumably by DPDK port num, so pre-sort by port_num
        # this won't work because we don't have DPDK port numbers yet
        ports = sorted(self.vnfd_helper.interfaces, key=self.vnfd_helper.port_num)
        port_names = (intf["name"] for intf in ports)
        collectd_options = self.get_collectd_options()
        plugins = collectd_options.get("plugins", {})
        # we must set timeout to be the same as the VNF otherwise KPIs will die before VNF
        return ResourceProfile(self.vnfd_helper.mgmt_interface, port_names=port_names,
                               plugins=plugins, interval=collectd_options.get("interval"),
                               timeout=self.scenario_helper.timeout)

    def _check_interface_fields(self):
        num_nodes = len(self.scenario_helper.nodes)
        # OpenStack instance creation time is probably proportional to the number
        # of instances
        timeout = 120 * num_nodes
        dpdk_node = DpdkNode(self.scenario_helper.name, self.vnfd_helper.interfaces,
                             self.ssh_helper, timeout)
        dpdk_node.check()

    def _detect_and_bind_drivers(self):
        interfaces = self.vnfd_helper.interfaces

        self._check_interface_fields()
        # check for bound after probe
        self.bound_pci = [v['virtual-interface']["vpci"] for v in interfaces]

        self.dpdk_bind_helper.read_status()
        self.dpdk_bind_helper.save_used_drivers()

        self.dpdk_bind_helper.bind(self.bound_pci, 'igb_uio')

        sorted_dpdk_pci_addresses = sorted(self.dpdk_bind_helper.dpdk_bound_pci_addresses)
        for dpdk_port_num, vpci in enumerate(sorted_dpdk_pci_addresses):
            try:
                intf = next(v for v in interfaces
                            if vpci == v['virtual-interface']['vpci'])
                # force to int
                intf['virtual-interface']['dpdk_port_num'] = int(dpdk_port_num)
            except:  # pylint: disable=bare-except
                pass
        time.sleep(2)

    def get_local_iface_name_by_vpci(self, vpci):
        find_net_cmd = self.FIND_NET_CMD.format(vpci)
        exit_status, stdout, _ = self.ssh_helper.execute(find_net_cmd)
        if exit_status == 0:
            return stdout
        return None

    def tear_down(self):
        self.dpdk_bind_helper.rebind_drivers()


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
        status = self.resource.check_if_system_agent_running("collectd")[0]
        if status == 0:
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
        self.all_ports = None
        self._queue = Queue()
        self._result = {}
        self._terminated = Value('i', 0)

    def _build_ports(self):
        self.networks = self.vnfd_helper.port_pairs.networks
        self.uplink_ports = self.vnfd_helper.port_nums(self.vnfd_helper.port_pairs.uplink_ports)
        self.downlink_ports = \
            self.vnfd_helper.port_nums(self.vnfd_helper.port_pairs.downlink_ports)
        self.all_ports = self.vnfd_helper.port_nums(self.vnfd_helper.port_pairs.all_ports)

    def port_num(self, intf):
        # by default return port num
        return self.vnfd_helper.port_num(intf)

    def get_stats(self, *args, **kwargs):
        try:
            return self.client.get_stats(*args, **kwargs)
        except STLError:
            LOG.error('TRex client not connected')
            return {}

    def generate_samples(self, ports, key=None, default=None):
        # needs to be used ports
        last_result = self.get_stats(ports)
        key_value = last_result.get(key, default)

        if not isinstance(last_result, Mapping):  # added for mock unit test
            self._terminated.value = 1
            return {}

        samples = {}
        # recalculate port for interface and see if it matches ports provided
        for intf in self.vnfd_helper.interfaces:
            name = intf["name"]
            port = self.vnfd_helper.port_num(name)
            if port in ports:
                xe_value = last_result.get(port, {})
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
        traffic_profile.execute_traffic(self)
        self.client_started.value = 1
        time.sleep(self.RUN_DURATION)
        samples = self.generate_samples(traffic_profile.ports)
        time.sleep(self.QUEUE_WAIT_TIME)
        self._queue.put(samples)

    def run_traffic(self, traffic_profile, mq_producer):
        # if we don't do this we can hang waiting for the queue to drain
        # have to do this in the subprocess
        self._queue.cancel_join_thread()
        # fixme: fix passing correct trex config file,
        # instead of searching the default path
        mq_producer.send_message(
            messaging.TG_METHOD_STARTED,
            payloads.TrafficGeneratorPayload(version=1, iteration=0, kpi={}))

        try:
            self._build_ports()
            self.client = self._connect()
            self.client.reset(ports=self.all_ports)
            self.client.remove_all_streams(self.all_ports)  # remove all streams
            traffic_profile.register_generator(self)

            iteration_index = 0
            while self._terminated.value == 0:
                iteration_index += 1
                self._run_traffic_once(traffic_profile)
                mq_producer.send_message(
                    messaging.TG_METHOD_ITERATION,
                    payloads.TrafficGeneratorPayload(
                        version=1, iteration=iteration_index, kpi={}))

            self.client.stop(self.all_ports)
            self.client.disconnect()
            self._terminated.value = 0
            mq_producer.send_message(
                messaging.TG_METHOD_FINISHED,
                payloads.TrafficGeneratorPayload(
                    version=1, iteration=0, kpi={}))
        except STLError:
            if self._terminated.value:
                LOG.debug("traffic generator is stopped")
                return  # return if trex/tg server is stopped.
            raise

    def terminate(self):
        self._terminated.value = 1  # stop client

    def clear_stats(self, ports=None):
        if ports is None:
            ports = self.all_ports
        self.client.clear_stats(ports=ports)

    def start(self, ports=None, *args, **kwargs):
        # pylint: disable=keyword-arg-before-vararg
        # NOTE(ralonsoh): defining keyworded arguments before variable
        # positional arguments is a bug. This function definition doesn't work
        # in Python 2, although it works in Python 3. Reference:
        # https://www.python.org/dev/peps/pep-3102/
        if ports is None:
            ports = self.all_ports
        self.client.start(ports=ports, *args, **kwargs)

    def collect_kpi(self):
        if not self._queue.empty():
            kpi = self._queue.get()
            self._result.update(kpi)
            LOG.debug('Got KPIs from _queue for %s %s',
                      self.scenario_helper.name, self.RESOURCE_WORD)
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

    def deploy_vnfs(self, app_name):
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
        return self.scenario_cfg['task_path']

    @property
    def nodes(self):
        return self.scenario_cfg.get('nodes')

    @property
    def all_options(self):
        return self.scenario_cfg.get('options', {})

    @property
    def options(self):
        return self.all_options.get(self.name, {})

    @property
    def vnf_cfg(self):
        return self.options.get('vnf_config', self.DEFAULT_VNF_CFG)

    @property
    def topology(self):
        return self.scenario_cfg['topology']

    @property
    def timeout(self):
        test_duration = self.scenario_cfg.get('runner', {}).get('duration',
            self.options.get('timeout', constants.DEFAULT_VNF_TIMEOUT))
        test_timeout = self.options.get('timeout', constants.DEFAULT_VNF_TIMEOUT)
        return test_duration if test_duration > test_timeout else test_timeout

class SampleVNF(GenericVNF):
    """ Class providing file-like API for generic VNF implementation """

    VNF_PROMPT = "pipeline>"
    WAIT_TIME = 1
    WAIT_TIME_FOR_SCRIPT = 10
    APP_NAME = "SampleVNF"
    # we run the VNF interactively, so the ssh command will timeout after this long

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

        self.context_cfg = None
        self.nfvi_context = None
        self.pipeline_kwargs = {}
        self.uplink_ports = None
        self.downlink_ports = None
        # NOTE(esm): make QueueFileWrapper invert-able so that we
        #            never have to manage the queues
        self.q_in = Queue()
        self.q_out = Queue()
        self.queue_wrapper = None
        self.run_kwargs = {}
        self.used_drivers = {}
        self.vnf_port_pairs = None
        self._vnf_process = None

    def _build_ports(self):
        self._port_pairs = PortPairs(self.vnfd_helper.interfaces)
        self.networks = self._port_pairs.networks
        self.uplink_ports = self.vnfd_helper.port_nums(self._port_pairs.uplink_ports)
        self.downlink_ports = self.vnfd_helper.port_nums(self._port_pairs.downlink_ports)
        self.my_ports = self.vnfd_helper.port_nums(self._port_pairs.all_ports)

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
        name = "{}-{}-{}".format(self.name, self.APP_NAME, os.getpid())
        self._vnf_process = Process(name=name, target=self._run)
        self._vnf_process.start()

    def _vnf_up_post(self):
        pass

    def instantiate(self, scenario_cfg, context_cfg):
        self.scenario_helper.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.nfvi_context = Context.get_context_from_server(self.scenario_helper.nodes[self.name])
        # self.nfvi_context = None

        # vnf deploy is unsupported, use ansible playbooks
        if self.scenario_helper.options.get("vnf_deploy", False):
            self.deploy_helper.deploy_vnfs(self.APP_NAME)
        self.resource_helper.setup()
        self._start_vnf()

    def wait_for_instantiate(self):
        buf = []
        time.sleep(self.WAIT_TIME)  # Give some time for config to load
        while True:
            if not self._vnf_process.is_alive():
                raise RuntimeError("%s VNF process died." % self.APP_NAME)

            # NOTE(esm): move to QueueFileWrapper
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
            time.sleep(self.WAIT_TIME_FOR_SCRIPT)
            # Send ENTER to display a new prompt in case the prompt text was corrupted
            # by other VNF output
            self.q_in.put('\r\n')

    def _build_run_kwargs(self):
        self.run_kwargs = {
            'stdin': self.queue_wrapper,
            'stdout': self.queue_wrapper,
            'keep_stdin_open': True,
            'pty': True,
            'timeout': self.scenario_helper.timeout,
        }

    def _build_config(self):
        return self.setup_helper.build_config()

    def _run(self):
        # we can't share ssh paramiko objects to force new connection
        self.ssh_helper.drop_connection()
        cmd = self._build_config()
        # kill before starting
        self.setup_helper.kill_vnf()

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
        self.setup_helper.kill_vnf()
        self._tear_down()
        self.resource_helper.stop_collect()
        if self._vnf_process is not None:
            # be proper and join first before we kill
            LOG.debug("joining before terminate %s", self._vnf_process.name)
            self._vnf_process.join(constants.PROCESS_JOIN_TIMEOUT)
            self._vnf_process.terminate()
        # no terminate children here because we share processes with tg

    def get_stats(self, *args, **kwargs):  # pylint: disable=unused-argument
        """Method for checking the statistics

        This method could be overridden in children classes.

        :return: VNF statistics
        """
        cmd = 'p {0} stats'.format(self.APP_WORD)
        out = self.vnf_execute(cmd)
        return out

    def collect_kpi(self):
        # we can't get KPIs if the VNF is down
        check_if_process_failed(self._vnf_process)
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

    def scale(self, flavor=""):
        """The SampleVNF base class doesn't provide the 'scale' feature"""
        raise y_exceptions.FunctionNotImplemented(
            function_name='scale', class_name='SampleVNFTrafficGen')


class SampleVNFTrafficGen(GenericTrafficGen):
    """ Class providing file-like API for generic traffic generator """

    APP_NAME = 'Sample'
    RUN_WAIT = 1

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        super(SampleVNFTrafficGen, self).__init__(name, vnfd)
        self.bin_path = get_nsb_option('bin_path', '')

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
        self._tg_process = None
        self._traffic_process = None

    def _start_server(self):
        # we can't share ssh paramiko objects to force new connection
        self.ssh_helper.drop_connection()

    def instantiate(self, scenario_cfg, context_cfg):
        self.scenario_helper.scenario_cfg = scenario_cfg
        self.resource_helper.setup()
        # must generate_cfg after DPDK bind because we need port number
        self.resource_helper.generate_cfg()

        LOG.info("Starting %s server...", self.APP_NAME)
        name = "{}-{}-{}".format(self.name, self.APP_NAME, os.getpid())
        self._tg_process = Process(name=name, target=self._start_server)
        self._tg_process.start()

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
        # always drop connections first thing in new processes
        # so we don't get paramiko errors
        self.ssh_helper.drop_connection()
        LOG.info("Starting %s client...", self.APP_NAME)
        self._mq_producer = self._setup_mq_producer()
        self.resource_helper.run_traffic(traffic_profile, self._mq_producer)

    def run_traffic(self, traffic_profile):
        """ Generate traffic on the wire according to the given params.
        Method is non-blocking, returns immediately when traffic process
        is running. Mandatory.

        :param traffic_profile:
        :return: True/False
        """
        name = "{}-{}-{}-{}".format(self.name, self.APP_NAME, traffic_profile.__class__.__name__,
                                    os.getpid())
        self._traffic_process = Process(name=name, target=self._traffic_runner,
                                        args=(traffic_profile,))
        self._traffic_process.start()
        # Wait for traffic process to start
        while self.resource_helper.client_started.value == 0:
            time.sleep(self.RUN_WAIT)
            # what if traffic process takes a few seconds to start?
            if not self._traffic_process.is_alive():
                break

        return self._traffic_process.ident

    def collect_kpi(self):
        # check if the tg processes have exited
        for proc in (self._tg_process, self._traffic_process):
            check_if_process_failed(proc)
        result = self.resource_helper.collect_kpi()
        LOG.debug("%s collect KPIs %s", self.APP_NAME, result)
        return result

    def terminate(self):
        """ After this method finishes, all traffic processes should stop. Mandatory.

        :return: True/False
        """
        self.traffic_finished = True
        # we must kill client before we kill the server, or the client will raise exception
        if self._traffic_process is not None:
            # be proper and try to join before terminating
            LOG.debug("joining before terminate %s", self._traffic_process.name)
            self._traffic_process.join(constants.PROCESS_JOIN_TIMEOUT)
            self._traffic_process.terminate()
        if self._tg_process is not None:
            # be proper and try to join before terminating
            LOG.debug("joining before terminate %s", self._tg_process.name)
            self._tg_process.join(constants.PROCESS_JOIN_TIMEOUT)
            self._tg_process.terminate()
        # no terminate children here because we share processes with vnf

    def scale(self, flavor=""):
        """A traffic generator VFN doesn't provide the 'scale' feature"""
        raise y_exceptions.FunctionNotImplemented(
            function_name='scale', class_name='SampleVNFTrafficGen')
