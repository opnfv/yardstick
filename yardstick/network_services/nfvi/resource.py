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
import logging
import os.path
import re
import multiprocessing
from oslo_config import cfg

from yardstick import ssh
from yardstick.network_services.nfvi.collectd import AmqpConsumer
from yardstick.network_services.utils import provision_tool

LOGGING = logging.getLogger(__name__)

CONF = cfg.CONF
ZMQ_OVS_PORT = 5567
ZMQ_POLLING_TIME = 12000


class ResourceProfile(object):
    """
    This profile adds a resource at the beginning of the test session
    """

    def __init__(self, vnfd, cores):
        self.enable = True
        self.connection = None
        self.cores = cores

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
        if "cpufreq" in reskey[1]:
            match = re.search(pattern, reskey[2], re.MULTILINE)
            metric = reskey[1]
        else:
            match = re.search(pattern, reskey[1], re.MULTILINE)
            metric = reskey[2]

        time, val = re.split(":", value)
        if match:
            return [str(match.group(1)), metric, val, time]

        return ["error", "Invalid", ""]

    def parse_collectd_result(self, metrics, listcores):
        """ convert collectd data into json"""
        res = {"cpu": {}, "memory": {}}
        testcase = ""

        for key, value in metrics.items():
            reskey = key.rsplit("/")
            if "cpu" in reskey[1] or "intel_rdt" in reskey[1]:
                cpu_key, name, metric, testcase = \
                    self.get_cpu_data(reskey, value)
                if cpu_key in listcores:
                    res["cpu"].setdefault(cpu_key, {}).update({name: metric})
            elif "memory" in reskey[1]:
                val = re.split(":", value)[1]
                res["memory"].update({reskey[2]: val})
        res["timestamp"] = testcase

        return res

    def amqp_collect_nfvi_kpi(self, _queue=multiprocessing.Queue()):
        """ amqp collect and return nfvi kpis """
        try:
            metric = {}
            amqp_client = \
                multiprocessing.Process(target=self.run_collectd_amqp,
                                        args=(_queue,))
            amqp_client.start()
            amqp_client.join(7)
            amqp_client.terminate()

            while not _queue.empty():
                metric.update(_queue.get())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            LOGGING.debug("Failed to get NFVi stats...")
            msg = {}
        else:
            msg = self.parse_collectd_result(metric, self.cores)

        return msg

    @classmethod
    def _start_collectd(cls, connection, bin_path):
        LOGGING.debug("Starting collectd to collect NFVi stats")
        connection.execute('sudo pkill -9 collectd')
        collectd = os.path.join(bin_path, "collectd.sh")
        provision_tool(connection, collectd)

        # Reset amqp queue
        LOGGING.debug("reset and setup amqp to collect data from collectd")
        connection.execute("sudo service rabbitmq-server start")
        connection.execute("sudo rabbitmqctl stop_app")
        connection.execute("sudo rabbitmqctl reset")
        connection.execute("sudo rabbitmqctl start_app")
        connection.execute("sudo service rabbitmq-server restart")

        # Run collectd

        connection.execute("sudo %s" % collectd)
        LOGGING.debug("Start collectd service.....")
        connection.execute(os.path.join(bin_path, "collectd", "collectd"))
        LOGGING.debug("Done")

    def initiate_systemagent(self, bin_path):
        """ Start system agent for NFVi collection on host """
        if self.enable:
            self._start_collectd(self.connection, bin_path)

    def start(self):
        """ start nfvi collection """
        if self.enable:
            logging.debug("Start NVFi metric collection...")

    def stop(self):
        """ stop nfvi collection """
        if self.enable:
            agent = "collectd"
            logging.debug("Stop resource monitor...")
            status, pid = self.check_if_sa_running(agent)
            if status:
                self.connection.execute('sudo kill -9 %s' % pid)
                self.connection.execute('sudo pkill -9 %s' % agent)
                self.connection.execute('sudo service rabbitmq-server stop')
                self.connection.execute("sudo rabbitmqctl stop_app")
