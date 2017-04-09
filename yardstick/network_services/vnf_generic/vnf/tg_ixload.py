#  Copyright (c) 2016-2017 Intel Corporation
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

from __future__ import absolute_import
import csv
import glob
import logging
import os

import shutil

from subprocess import call

from yardstick.common.utils import makedirs
from yardstick.network_services.vnf_generic.vnf.base import GenericTrafficGen

LOG = logging.getLogger(__name__)

VNF_PATH = os.path.dirname(os.path.realpath(__file__))


MOUNT_CMD = "mount.cifs //{ip}/Results {RESULTS_MOUNT} -o username={user}," \
            "password={passwd}"

IXLOAD_CMD = "{ixloadpy} {http_ixload} {args}"


class IxLoadTrafficGen(GenericTrafficGen):
    RESULTS_MOUNT = "/mnt/Results"

    def __init__(self, vnfd):
        super(IxLoadTrafficGen, self).__init__(vnfd)
        self._result = {}
        self._IxiaTrafficGen = None
        self.done = False
        self.tc_file_name = ''
        self.ixia_file_name = ''
        self.data = {}

    def parse_csv_read(self, reader):
        http_throughput = []
        simulated_user = []
        concurrent_connections = []
        connection_rate = []
        transaction_rate = []
        for row in reader:
            try:
                http_throughput.append(
                    int(row['HTTP Total Throughput (Kbps)']))
                simulated_user.append(int(row['HTTP Simulated Users']))
                concurrent_connections.append(
                    int(row['HTTP Concurrent Connections']))
                connection_rate.append(int(row['HTTP Connection Rate']))
                transaction_rate.append(int(row['HTTP Transaction Rate']))
            except ValueError:
                continue
        return [http_throughput, simulated_user, concurrent_connections,
                concurrent_connections, transaction_rate]

    def run_traffic(self, traffic_profile):
        interfaces = self.vnfd["vdu"][0]['external-interface']
        ports = []
        for interface in interfaces:
            card = interface['virtual-interface']["vpci"].split(":")[0]
            ports.append(interface['virtual-interface']["vpci"].split(":")[1])

        shutil.copy(self.ixia_file_name, self.RESULTS_MOUNT)
        try:
            for csv_file in glob.iglob(self.rel_bin_path('*.csv')):
                os.unlink(csv_file)
        except OSError:
            # ignore OSError
            pass
        ixia_config = self.vnfd["mgmt-interface"]["tg-config"]
        ixload_config = \
            '{"ixia_chassis": "%s", "IXIA": {"ports": %s, "card": %s}, ' \
            '"remote_server": "%s", "result_dir": "%s", "ixload_cfg": ' \
            '"C:/Results/%s"}' % (
                ixia_config["ixchassis"], ports, card,
                self.vnfd["mgmt-interface"]["ip"], self.bin_path,
                os.path.basename(self.ixia_file_name))

        http_ixload_path = os.path.join(VNF_PATH, "../../traffic_profile")
        cmd = IXLOAD_CMD.format(
            ixloadpy=os.path.join(ixia_config["py_bin_path"], "ixloadpython"),
            http_ixload=os.path.join(http_ixload_path,
                                     "http_ixload.py"),
            args='\'%s\'' % ixload_config)
        LOG.debug(cmd)
        call(cmd, shell=True)

        # -- collect KPI
        http_throughput = []
        simulated_user = []
        concurrent_connections = []
        connection_rate = []
        transaction_rate = []

        with open(self.rel_bin_path("ixLoad_HTTP_Client.csv")) as csv_file:
            lines = csv_file.readlines()[10:]

        with open(self.rel_bin_path("http_result.csv"), 'wb+') as result_file:
            result_file.writelines(lines[:-1])
            result_file.flush()
            result_file.seek(0)
            reader = csv.DictReader(result_file)
            http_throughput, simulated_user, concurrent_connections, \
                connection_rate, transaction_rate = self.parse_csv_read(reader)

        LOG.debug(http_throughput)
        LOG.debug(simulated_user)
        LOG.debug(connection_rate)
        LOG.debug(concurrent_connections)
        self.data["HTTP Total Throughput (Kbps)"] = {
            "min": min(http_throughput),
            "max": max(http_throughput),
            "avg": (sum(http_throughput) / len(http_throughput))}
        self.data["HTTP Simulated Users"] = {"min": min(simulated_user),
                                             "max": max(simulated_user),
                                             "avg": (sum(simulated_user) / len(
                                                 simulated_user))}
        self.data["HTTP Concurrent Connections"] = {
            "min": min(concurrent_connections),
            "max": max(concurrent_connections),
            "avg": (sum(concurrent_connections) / len(concurrent_connections))}
        self.data["HTTP Connection Rate"] = {"min": min(connection_rate),
                                             "max": max(connection_rate),
                                             "avg": (
                                             sum(connection_rate) / len(
                                                 connection_rate))}
        self.data["HTTP Transaction Rate"] = {"min": min(transaction_rate),
                                              "max": max(transaction_rate),
                                              "avg": (
                                              sum(transaction_rate) / len(
                                                  transaction_rate))}

    def listen_traffic(self, traffic_profile):
        pass

    def instantiate(self, scenario_cfg, context_cfg):

        makedirs(self.RESULTS_MOUNT)
        cmd = MOUNT_CMD.format(ip=self.vnfd["mgmt-interface"]["ip"],
                               user=self.vnfd["mgmt-interface"]["user"],
                               passwd=self.vnfd["mgmt-interface"]["password"],
                               RESULTS_MOUNT=self.RESULTS_MOUNT)
        LOG.debug(cmd)

        if not os.path.ismount(self.RESULTS_MOUNT):
            call(cmd, shell=True)

        self.done = False
        self.tc_file_name = '{0}.yaml'.format(scenario_cfg['tc'])
        self.ixia_file_name = str(scenario_cfg['ixia_profile'])

        shutil.rmtree(self.RESULTS_MOUNT, ignore_errors=True)
        makedirs(self.RESULTS_MOUNT)
        shutil.copy(self.ixia_file_name, self.RESULTS_MOUNT)

    def terminate(self):
        call(["pkill", "-9", "http_ixload.py"])

    def collect_kpi(self):
        result = self.data
        LOG.info("Collecting ixia stats")
        LOG.debug("ixia collect Kpis %s", result)
        return result
