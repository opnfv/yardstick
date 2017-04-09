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

import tempfile
from multiprocessing import Queue
import multiprocessing
import time
import os
import logging
import re
import ipaddress
import paramiko
import yaml
import ConfigParser
import csv
import json
from yardstick import ssh
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.vnf_generic.vnf.base import GenericTrafficGen
from yardstick.network_services.utils import provision_tool

log = logging.getLogger(__name__)

VNF_PATH = os.path.dirname(os.path.realpath(__file__))

MOUNT_CMD = "mount.cifs //{ip}/Results /mnt/Results/ -o username={user},password={passwd}"

IXLOAD_CMD = "{ixloadpy} {http_ixload} {args}"

class QueueFileWrapper(object):
    """ Class providing file-like API for talking with SSH connection """

    def __init__(self, q_in, q_out):
        self.q_in = q_in
        self.q_out = q_out
        self.closed = False

    def read(self, size):
        if self.q_in.qsize() > 0:
            in_data = self.q_in.get()
            log.debug("IN: %s" % in_data)
            return in_data
        else:
            return "\n"  # We need to keep sending something to keep stdin open TODO: fix in ssh.py library

    def write(self, chunk):
        #log.debug("OUT: %s" % chunk)
        self.q_out.put(chunk)

    def close(self):
        pass

    def clear(self):
	while self.q_out.qsize() > 0:
            self.q_out.get()

class IxLoadTrafficGen(GenericTrafficGen):
    def __init__(self, vnfd):
        super(IxLoadTrafficGen, self).__init__(vnfd)
        self._result = {}
	self._IxiaTrafficGen = None
        self.done = False
        self.tc_file_name = ''
        self.ixia_file_name = ''
        self.data = {}

    def run_traffic(self, traffic_profile):
        interfaces = self.vnfd["vdu"][0]['external-interface']
        ports = []
        for interface in interfaces:
          card = interface['virtual-interface']["vpci"].split(":")[0]
          ports.append(interface['virtual-interface']["vpci"].split(":")[1])

        my_port = " ".join(str(item) for item in ports)
        os.system("cp %s /mnt/Results" % self.ixia_file_name) 
        os.system("rm -rf %s/*.csv" % self.bin_path)
        ixia_config = self.vnfd["mgmt-interface"]["tg-config"]
        ixload_config  = \
            '{"ixia_chassis": "%s", "IXIA": {"ports": %s, "card": %s}, "remote_server": "%s", "result_dir": "%s", "ixload_cfg": "C:/Results/%s"}' % (ixia_config["ixchassis"], ports, card, self.vnfd["mgmt-interface"]["ip"], self.bin_path, os.path.basename(self.ixia_file_name))

        http_ixload_path = os.path.join(VNF_PATH, "../../traffic_profile")
        cmd = IXLOAD_CMD.format(ixloadpy=os.path.join(ixia_config["py_bin_path"], "ixloadpython"),
                                http_ixload=os.path.join(http_ixload_path,
                                                         "http_ixload.py"),
                                args='\'%s\'' % ixload_config)
        log.debug(cmd)
        os.system(cmd)

        #-- collect KPI
        http_throughput = []
        simulated_user = []
        concurrent_connections = []
        connection_rate = []
        transaction_rate = []

        readFile = open("%s/ixLoad_HTTP_Client.csv" % self.bin_path)
        lines = readFile.readlines()
        del lines[:10]
        readFile.close()
        w = open("%s/http_result.csv" % self.bin_path, 'w')
        w.writelines([item for item in lines[:-1]])
        w.close()

        with open('%s/http_result.csv' % self.bin_path) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
			http_throughput.append(int(row['HTTP Total Throughput (Kbps)']))
			simulated_user.append(int(row['HTTP Simulated Users']))
			concurrent_connections.append(int(row['HTTP Concurrent Connections']))
			connection_rate.append(int(row['HTTP Connection Rate']))
			transaction_rate.append(int(row['HTTP Transaction Rate']))
		except ValueError:
			continue

        log.debug(http_throughput)
        log.debug(simulated_user)
        log.debug(connection_rate)
        log.debug(concurrent_connections)
        self.data["HTTP Total Throughput (Kbps)"] = {"min": min(http_throughput),
                                                     "max": max(http_throughput),
                                                     "avg": (sum(http_throughput)/len(http_throughput))}
        self.data["HTTP Simulated Users"] = {"min": min(simulated_user),
                                             "max": max(simulated_user),
                                             "avg": (sum(simulated_user)/len(simulated_user))}
        self.data["HTTP Concurrent Connections"] = {"min": min(concurrent_connections),
                                                    "max": max(concurrent_connections),
                                                    "avg": (sum(concurrent_connections)/len(concurrent_connections))}
        self.data["HTTP Connection Rate"] = {"min": min(connection_rate),
                                             "max": max(connection_rate),
                                             "avg": (sum(connection_rate)/len(connection_rate))}
        self.data["HTTP Transaction Rate"] = {"min": min(transaction_rate),
                                              "max": max(transaction_rate),
                                              "avg": (sum(transaction_rate)/len(transaction_rate))}
    def listen_traffic(self, traffic_profile):
        pass

    def instantiate(self, scenario_cfg, context_cfg):

        os.system("mkdir -p /mnt/Results")
        cmd = MOUNT_CMD.format(ip=self.vnfd["mgmt-interface"]["ip"],
                             user=self.vnfd["mgmt-interface"]["user"],
                             passwd=self.vnfd["mgmt-interface"]["password"])
        log.debug(cmd)
        if os.system("mount | grep -i results"):
           os.system(cmd)

        self.done = False
        self.tc_file_name = '{0}.yaml'.format(scenario_cfg['tc'])
        self.ixia_file_name = '{0}'.format(scenario_cfg['ixia_profile'])

        os.system("rm -rf /mnt/Results/*")
        os.system("cp -r %s /mnt/Results" % self.ixia_file_name)

    def terminate(self):
	os.system("pkill -9 http_ixload.py")

    def collect_kpi(self):
        result = self.data
	log.info("Collecting ixia stats")
	log.debug("ixia collect Kpis {0}".format(result))
        return result
