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
from oslo_config import cfg

from yardstick import ssh
from yardstick.network_services.nfvi.collectd import AmqpConsumer
from yardstick.network_services.utils import provision_tool

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

    def __init__(self, vnfd, cores, nfvi_type="baremetal"):
        self.enable = True
        self.connection = None
        self.cores = cores
        self._queue = multiprocessing.Queue()
        self.amqp_client = None
        self.nfvi_type = nfvi_type
        self.vnfd = vnfd

        mgmt_interface = vnfd.get("mgmt-interface")
        # why the host or ip?
        self.vnfip = mgmt_interface.get("host", mgmt_interface["ip"])
        self.connection = ssh.SSH.from_node(mgmt_interface,
                                            overrides={"ip": self.vnfip})

        self.connection.wait()

    def check_if_sa_running(self, process):
        """ verify if system agent is running """
        err, pid, _ = self.connection.execute("pgrep -f %s" % process)
        return [err == 0, pid]

    def run_collectd_amqp(self, queue):
        """ run amqp consumer to collect the NFVi data """
        amqp = \
            AmqpConsumer('amqp://admin:admin@{}:5672/%2F'.format(self.vnfip),
                         queue)
        try:
            amqp.run()
        except (AttributeError, RuntimeError, KeyboardInterrupt):
            amqp.stop()

    @classmethod
    def get_cpu_data(cls, reskey, value):
        """ Get cpu topology of the host """
        pattern = r"-(\d+)"
        if "cpufreq" in reskey[0]:
            match = re.search(pattern, reskey[1], re.MULTILINE)
            metric = reskey[0]
        else:
            match = re.search(pattern, reskey[0], re.MULTILINE)
            metric = reskey[1]

        time, val = re.split(":", value)
        if match:
            return [str(match.group(1)), metric, val, time]

        return ["error", "Invalid", "", ""]

    @classmethod
    def _parse_hugepages(cls, reskey, value):
        key = '/'.join(reskey)
        val = re.split(":", value)[1]
        return {key: val}

    @classmethod
    def _parse_dpdkstat(cls, reskey, value):
        key = '/'.join(reskey)
        val = re.split(":", value)[1]
        return {key: val}

    @classmethod
    def _parse_virt(cls, reskey, value):
        key = '/'.join(reskey)
        val = re.split(":", value)[1]
        return {key: val}

    @classmethod
    def _parse_ovs_stats(cls, reskey, value):
        key = '/'.join(reskey)
        val = re.split(":", value)[1]
        return {key: val}

    def parse_collectd_result(self, metrics, listcores):
        """ convert collectd data into json"""
        res = {"cpu": {}, "memory": {}, "hugepages": {},
               "dpdkstat": {}, "virt": {}, "ovs_stats": {}}
        testcase = ""

        for key, value in metrics.items():
            reskey = key.rsplit("/")
            reskey = [rkey for rkey in reskey if "nsb_stats" not in rkey]

            if "cpu" in reskey[0] or "intel_rdt" in reskey[0]:
                cpu_key, name, metric, testcase = \
                    self.get_cpu_data(reskey, value)
                if cpu_key in listcores:
                    res["cpu"].setdefault(cpu_key, {}).update({name: metric})
            elif "memory" in reskey[0]:
                val = re.split(":", value)[0]
                res["memory"].update({reskey[1]: val})
            elif "hugepages" in reskey[0]:
                res["hugepages"].update(self._parse_hugepages(reskey, value))
            elif "dpdkstat" in reskey[0]:
                res["dpdkstat"].update(self._parse_dpdkstat(reskey, value))
            elif "virt" in reskey[1]:
                res["virt"].update(self._parse_virt(reskey, value))
            elif "ovs_stats" in reskey[0]:
                res["ovs_stats"].update(self._parse_ovs_stats(reskey, value))

        res["timestamp"] = testcase

        return res

    def amqp_process_for_nfvi_kpi(self):
        """ amqp collect and return nfvi kpis """
        if self.amqp_client is None:
            self.amqp_client = \
                multiprocessing.Process(target=self.run_collectd_amqp,
                                        args=(self._queue,))
            self.amqp_client.start()

    def amqp_collect_nfvi_kpi(self):
        """ amqp collect and return nfvi kpis """
        metric = {}
        while not self._queue.empty():
            metric.update(self._queue.get())
        msg = self.parse_collectd_result(metric, self.cores)
        return msg

    def _provide_config_file(self, bin_path, nfvi_cfg, vars):
        template = ""
        with open(os.path.join(bin_path, nfvi_cfg), 'r') as cfg:
            template = cfg.read()
        cfg, cfg_content = tempfile.mkstemp()
        cfg = os.fdopen(cfg, "w+")
        cfg.write(template.format(**vars))
        cfg.close()
        cfg_file = os.path.join(bin_path, nfvi_cfg)
        self.connection.put(cfg_content, cfg_file)

    def _prepare_collectd_conf(self, bin_path):
        """ Prepare collectd conf based on the nfvi_type """
        loadplugin = ""
        for plugin in LIST_PLUGINS_ENABLED:
            loadplugin += "LoadPlugin %s\n" % plugin

        interfaces = self.vnfd["vdu"][0]['external-interface']
        intrf = ""
        for interface in interfaces:
            intrf += "PortName '%s'\n" % interface["name"]

        args = {"interval": '25',
                "loadplugin": loadplugin,
                "dpdk_interface": intrf}

        self._provide_config_file(bin_path, 'collectd.conf', args)

    def _start_collectd(self, connection, bin_path):
        LOG.debug("Starting collectd to collect NFVi stats")
        connection.execute('sudo pkill -9 collectd')
        collectd = os.path.join(bin_path, "collectd.sh")
        provision_tool(connection, collectd)
        self._prepare_collectd_conf(bin_path)

        # Reset amqp queue
        LOG.debug("reset and setup amqp to collect data from collectd")
        connection.execute("sudo rm -rf /var/lib/rabbitmq/mnesia/rabbit*")
        connection.execute("sudo service rabbitmq-server start")
        connection.execute("sudo rabbitmqctl stop_app")
        connection.execute("sudo rabbitmqctl reset")
        connection.execute("sudo rabbitmqctl start_app")
        connection.execute("sudo service rabbitmq-server restart")

        # Run collectd

        http_proxy = os.environ.get('http_proxy', '')
        https_proxy = os.environ.get('https_proxy', '')
        connection.execute("sudo %s '%s' '%s'" %
                           (collectd, http_proxy, https_proxy))
        LOG.debug("Start collectd service.....")
        connection.execute(
            "sudo %s" % os.path.join(bin_path, "collectd", "collectd"))
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
        if self.enable:
            agent = "collectd"
            LOG.debug("Stop resource monitor...")

            if self.amqp_client is not None:
                self.amqp_client.terminate()

            status, pid = self.check_if_sa_running(agent)
            if status:
                self.connection.execute('sudo kill -9 %s' % pid)
                self.connection.execute('sudo pkill -9 %s' % agent)
                self.connection.execute('sudo service rabbitmq-server stop')
                self.connection.execute("sudo rabbitmqctl stop_app")
