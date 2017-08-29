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
""" Resource collection definitions """

from __future__ import absolute_import
from __future__ import print_function
import tempfile
import logging
import os
import os.path
import re
import multiprocessing
from collections import Sequence

from oslo_config import cfg

from yardstick import ssh
from yardstick.network_services.nfvi.collectd import AmqpConsumer
from yardstick.network_services.utils import get_nsb_option

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
ZMQ_OVS_PORT = 5567
ZMQ_POLLING_TIME = 12000
LIST_PLUGINS_ENABLED = ["amqp", "cpu", "cpufreq", "intel_rdt", "memory",
                        "hugepages", "dpdkstat", "virt", "ovs_stats"]


class ResourceProfile(object):
    """
    This profile adds a resource at the beginning of the test session
    """

    def __init__(self, mgmt, interfaces=None, cores=None):
        self.enable = True
        self.connection = None
        self.cores = cores if isinstance(cores, Sequence) else []
        self._queue = multiprocessing.Queue()
        self.amqp_client = None
        self.interfaces = interfaces if isinstance(interfaces, Sequence) else []

        # why the host or ip?
        self.vnfip = mgmt.get("host", mgmt["ip"])
        self.connection = ssh.SSH.from_node(mgmt, overrides={"ip": self.vnfip})

        self.connection.wait()

    def check_if_sa_running(self, process):
        """ verify if system agent is running """
        err, pid, _ = self.connection.execute("pgrep -f %s" % process)
        return [err == 0, pid]

    def run_collectd_amqp(self):
        """ run amqp consumer to collect the NFVi data """
        amqp_url = 'amqp://admin:admin@{}:5672/%2F'.format(self.vnfip)
        amqp = AmqpConsumer(amqp_url, self._queue)
        try:
            amqp.run()
        except (AttributeError, RuntimeError, KeyboardInterrupt):
            amqp.stop()

    @classmethod
    def parse_simple_resource(cls, key, value):
        reskey = "/".join(rkey for rkey in key if "nsb_stats" not in rkey)
        return {reskey: value.split(":")[1]}

    @classmethod
    def get_cpu_data(cls, res_key0, res_key1, value):
        """ Get cpu topology of the host """
        pattern = r"-(\d+)"

        if 'cpufreq' in res_key0:
            metric, source = res_key0, res_key1
        else:
            metric, source = res_key1, res_key0

        match = re.search(pattern, source, re.MULTILINE)
        if not match:
            return "error", "Invalid", "", ""

        time, value = value.split(":")
        return str(match.group(1)), metric, value, time

    @classmethod
    def parse_hugepages(cls, key, value):
        return cls.parse_simple_resource(key, value)

    @classmethod
    def parse_dpdkstat(cls, key, value):
        return cls.parse_simple_resource(key, value)

    @classmethod
    def parse_virt(cls, key, value):
        return cls.parse_simple_resource(key, value)

    @classmethod
    def parse_ovs_stats(cls, key, value):
        return cls.parse_simple_resource(key, value)

    def parse_collectd_result(self, metrics, core_list):
        """ convert collectd data into json"""
        result = {
            "cpu": {},
            "memory": {},
            "hugepages": {},
            "dpdkstat": {},
            "virt": {},
            "ovs_stats": {},
        }
        testcase = ""

        for key, value in metrics.items():
            key_split = key.split("/")
            res_key_iter = (key for key in key_split if "nsb_stats" not in key)
            res_key0 = next(res_key_iter)
            res_key1 = next(res_key_iter)

            if "cpu" in res_key0 or "intel_rdt" in res_key0:
                cpu_key, name, metric, testcase = \
                    self.get_cpu_data(res_key0, res_key1, value)
                if cpu_key in core_list:
                    result["cpu"].setdefault(cpu_key, {}).update({name: metric})

            elif "memory" in res_key0:
                result["memory"].update({res_key1: value.split(":")[0]})

            elif "hugepages" in res_key0:
                result["hugepages"].update(self.parse_hugepages(key_split, value))

            elif "dpdkstat" in res_key0:
                result["dpdkstat"].update(self.parse_dpdkstat(key_split, value))

            elif "virt" in res_key1:
                result["virt"].update(self.parse_virt(key_split, value))

            elif "ovs_stats" in res_key0:
                result["ovs_stats"].update(self.parse_ovs_stats(key_split, value))

        result["timestamp"] = testcase

        return result

    def amqp_process_for_nfvi_kpi(self):
        """ amqp collect and return nfvi kpis """
        if self.amqp_client is None and self.enable:
            self.amqp_client = \
                multiprocessing.Process(target=self.run_collectd_amqp)
            self.amqp_client.start()

    def amqp_collect_nfvi_kpi(self):
        """ amqp collect and return nfvi kpis """
        if not self.enable:
            return {}

        metric = {}
        while not self._queue.empty():
            metric.update(self._queue.get())
        msg = self.parse_collectd_result(metric, self.cores)
        return msg

    def _provide_config_file(self, bin_path, nfvi_cfg, kwargs):
        with open(os.path.join(bin_path, nfvi_cfg), 'r') as cfg:
            template = cfg.read()
        cfg, cfg_content = tempfile.mkstemp()
        with os.fdopen(cfg, "w+") as cfg:
            cfg.write(template.format(**kwargs))
        cfg_file = os.path.join(bin_path, nfvi_cfg)
        self.connection.put(cfg_content, cfg_file)

    def _prepare_collectd_conf(self, bin_path):
        """ Prepare collectd conf """
        loadplugin = "\n".join("LoadPlugin {0}".format(plugin)
                               for plugin in LIST_PLUGINS_ENABLED)

        interfaces = "\n".join("PortName '{0[name]}'".format(interface)
                               for interface in self.interfaces)

        kwargs = {
            "interval": '25',
            "loadplugin": loadplugin,
            "dpdk_interface": interfaces,
        }

        self._provide_config_file(bin_path, 'collectd.conf', kwargs)

    def _start_collectd(self, connection, bin_path):
        connection.execute('sudo pkill -9 collectd')
        bin_path = get_nsb_option("bin_path")
        collectd_path = os.path.join(bin_path, "collectd", "collectd")
        exit_status = connection.execute("which %s > /dev/null 2>&1" % collectd_path)[0]
        if exit_status != 0:
            LOG.warning("%s is not present disabling", collectd_path)
            # disable auto-provisioning because it requires Internet access
            # collectd_installer = os.path.join(bin_path, "collectd.sh")
            # provision_tool(connection, collectd)
            # http_proxy = os.environ.get('http_proxy', '')
            # https_proxy = os.environ.get('https_proxy', '')
            # connection.execute("sudo %s '%s' '%s'" % (
            #     collectd_installer, http_proxy, https_proxy))
            return
        LOG.debug("Starting collectd to collect NFVi stats")
        self._prepare_collectd_conf(bin_path)

        # Reset amqp queue
        LOG.debug("reset and setup amqp to collect data from collectd")
        connection.execute("sudo rm -rf /var/lib/rabbitmq/mnesia/rabbit*")
        connection.execute("sudo service rabbitmq-server start")
        connection.execute("sudo rabbitmqctl stop_app")
        connection.execute("sudo rabbitmqctl reset")
        connection.execute("sudo rabbitmqctl start_app")
        connection.execute("sudo service rabbitmq-server restart")

        LOG.debug("Creating amdin user for rabbitmq in order to collect data from collectd")
        connection.execute("sudo rabbitmqctl delete_user guest")
        connection.execute("sudo rabbitmqctl add_user admin admin")
        connection.execute("sudo rabbitmqctl authenticate_user admin admin")
        connection.execute("sudo rabbitmqctl set_permissions -p / admin \".*\" \".*\" \".*\"")

        LOG.debug("Start collectd service.....")
        connection.execute("sudo %s" % collectd_path)
        LOG.debug("Done")

    def initiate_systemagent(self, bin_path):
        """ Start system agent for NFVi collection on host """
        if self.enable:
            self._start_collectd(self.connection, bin_path)

    def start(self):
        """ start nfvi collection """
        if self.enable:
            LOG.debug("Start NVFi metric collection...")

    def stop(self):
        """ stop nfvi collection """
        if not self.enable:
            return

        agent = "collectd"
        LOG.debug("Stop resource monitor...")

        if self.amqp_client is not None:
            self.amqp_client.terminate()

        status, pid = self.check_if_sa_running(agent)
        if status == 0:
            return

        self.connection.execute('sudo kill -9 %s' % pid)
        self.connection.execute('sudo pkill -9 %s' % agent)
        self.connection.execute('sudo service rabbitmq-server stop')
        self.connection.execute("sudo rabbitmqctl stop_app")
