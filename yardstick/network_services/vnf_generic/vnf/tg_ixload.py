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

from collections import OrderedDict
from subprocess import call

from yardstick.common import utils
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ClientResourceHelper


LOG = logging.getLogger(__name__)

VNF_PATH = os.path.dirname(os.path.realpath(__file__))

MOUNT_CMD = """\
mount.cifs //{0[ip]}/Results {1.RESULTS_MOUNT} \
-o username={0[user]},password={0[password]}\
"""

IXLOAD_CONFIG_TEMPLATE = '''\
{
    "ixia_chassis": "%s",
    "IXIA": {
        "ports": %s,
        "card": %s
    },
    "remote_server": "%s",
    "result_dir": "%s",
    "ixload_cfg": "C:/Results/%s"
}'''

IXLOAD_CMD = "{ixloadpy} {http_ixload} {args}"


class ResourceDataHelper(list):

    def get_aggregates(self):
        return {
            "min": min(self),
            "max": max(self),
            "avg": sum(self) / len(self),
        }


class IxLoadResourceHelper(ClientResourceHelper):

    RESULTS_MOUNT = "/mnt/Results"

    KPI_LIST = OrderedDict((
        ('http_throughput', 'HTTP Total Throughput (Kbps)'),
        ('simulated_users', 'HTTP Simulated Users'),
        ('concurrent_connections', 'HTTP Concurrent Connections'),
        ('connection_rate', 'HTTP Connection Rate'),
        ('transaction_rate', 'HTTP Transaction Rate'),
    ))

    def __init__(self, setup_helper):
        super(IxLoadResourceHelper, self).__init__(setup_helper)
        self.result = OrderedDict((key, ResourceDataHelper()) for key in self.KPI_LIST)
        self.resource_file_name = ''
        self.data = None

    def parse_csv_read(self, reader):
        for row in reader:
            try:
                new_data = {key_left: int(row[key_right])
                            for key_left, key_right in self.KPI_LIST.items()}
            except (TypeError, ValueError):
                continue
            else:
                for key, value in new_data.items():
                    self.result[key].append(value)

    def setup(self):
        # NOTE: fixup scenario_helper to hanlde ixia
        self.resource_file_name = \
            utils.find_relative_file(
                self.scenario_helper.scenario_cfg['ixia_profile'],
                self.scenario_helper.scenario_cfg["task_path"])
        utils.makedirs(self.RESULTS_MOUNT)
        cmd = MOUNT_CMD.format(self.vnfd_helper.mgmt_interface, self)
        LOG.debug(cmd)

        if not os.path.ismount(self.RESULTS_MOUNT):
            call(cmd, shell=True)

        shutil.rmtree(self.RESULTS_MOUNT, ignore_errors=True)
        utils.makedirs(self.RESULTS_MOUNT)
        shutil.copy(self.resource_file_name, self.RESULTS_MOUNT)

    def make_aggregates(self):
        return {key_right: self.result[key_left].get_aggregates()
                for key_left, key_right in self.KPI_LIST.items()}

    def collect_kpi(self):
        if self.data:
            self._result.update(self.data)
        LOG.info("Collect %s KPIs %s", self.RESOURCE_WORD, self._result)
        return self._result

    def log(self):
        for key in self.KPI_LIST:
            LOG.debug(self.result[key])


class IxLoadTrafficGen(SampleVNFTrafficGen):

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = IxLoadResourceHelper

        super(IxLoadTrafficGen, self).__init__(name, vnfd, setup_env_helper_type,
                                               resource_helper_type)
        self._result = {}

    def run_traffic(self, traffic_profile):
        ports = []
        card = None
        for interface in self.vnfd_helper.interfaces:
            vpci_list = interface['virtual-interface']["vpci"].split(":")
            card = vpci_list[0]
            ports.append(str(vpci_list[1]))

        for csv_file in glob.iglob(self.ssh_helper.join_bin_path('*.csv')):
            os.unlink(csv_file)

        ixia_config = self.vnfd_helper.mgmt_interface["tg-config"]
        ixload_config = IXLOAD_CONFIG_TEMPLATE % (
            ixia_config["ixchassis"], ports, card,
            self.vnfd_helper.mgmt_interface["ip"], self.ssh_helper.bin_path,
            os.path.basename(self.resource_helper.resource_file_name))

        http_ixload_path = os.path.join(VNF_PATH, "../../traffic_profile")

        cmd = IXLOAD_CMD.format(
            ixloadpy=os.path.join(ixia_config["py_bin_path"], "ixloadpython"),
            http_ixload=os.path.join(http_ixload_path, "http_ixload.py"),
            args="'%s'" % ixload_config)

        LOG.debug(cmd)
        call(cmd, shell=True)

        with open(self.ssh_helper.join_bin_path("ixLoad_HTTP_Client.csv")) as csv_file:
            lines = csv_file.readlines()[10:]
        with open(self.ssh_helper.join_bin_path("http_result.csv"), 'wb+') as result_file:
            result_file.writelines(lines[:-1])
            result_file.flush()
            result_file.seek(0)
            reader = csv.DictReader(result_file)
            self.resource_helper.parse_csv_read(reader)

        self.resource_helper.log()
        self.resource_helper.data = self.resource_helper.make_aggregates()

    def terminate(self):
        call(["pkill", "-9", "http_ixload.py"])
        super(IxLoadTrafficGen, self).terminate()
