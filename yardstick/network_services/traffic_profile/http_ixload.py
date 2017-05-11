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

from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import logging

from oslo_serialization import jsonutils

LOG = logging.getLogger(__name__)
CSV_FILEPATH_NAME = 'IxL_statResults.csv'

STATS_TO_GET = (
    'HTTP_Client.csv',
    'HTTP_Server.csv',
    'L2-3 Stats for Client Ports.csv',
    'L2-3 Stats for Server Ports.csv',
    'IxLoad Detailed Report.html',
    'IxLoad Detailed Report.pdf'
)

HTTP_CLIENT_STATS = [
    ["HTTP Client", "TCP Connections Established", "kSum"],
    ["HTTP Client", "TCP Connection Requests Failed", "kSum"],
    ["HTTP Client", "HTTP Simulated Users", "kSum"],
    ["HTTP Client", "HTTP Concurrent Connections", "kSum"],
    ["HTTP Client", "HTTP Connections", "kSum"],
    ["HTTP Client", "HTTP Transactions", "kSum"],
    ["HTTP Client", "HTTP Connection Attempts", "kSum"]
]

HTTP_SERVER_STATS = [
    ["HTTP Server", "TCP Connections Established", "kSum"],
    ["HTTP Server", "TCP Connection Requests Failed", "kSum"]
]


class IXLOADHttpTest(object):
    def __init__(self, testinput):
        self.testinput = jsonutils.loads(testinput)
        self.parse_run_test()

    @staticmethod
    def get_ports_reassign(ports):
        formatted_destination = ["{};{};{}".format(*currentDestination) for
                                 currentDestination in ports]
        LOG.debug('for client ports:%s',
                  os.linesep.join(formatted_destination))
        return formatted_destination

    def reassign_ports(self, test, repository, ports_to_reassign):
        LOG.debug('ReassignPorts: %s %s', test, repository)

        chassis_chain = repository.cget('chassisChain')
        LOG.debug('chassischain: %s', chassis_chain)
        clientports = ports_to_reassign[0::2]
        serverports = ports_to_reassign[1::2]

        client_ports = self.get_ports_reassign(clientports)
        LOG.debug('Reassigning client ports: %s', client_ports)
        server_ports = self.get_ports_reassign(serverports)
        LOG.debug('Reassigning server ports: %s', server_ports)
        ports_to_set = client_ports + server_ports

        try:
            LOG.debug('Reassigning ports: %s', ports_to_set)
            test.setPorts(ports_to_set)
        except Exception:
            LOG.error('Error: Could not remap port assignment for: %s',
                      ports_to_set)
            self.ixLoad.delete(repository)
            self.ixLoad.disconnect()

    @staticmethod
    def stat_collector(*args):
        LOG.debug("""
=====================================
INCOMING STAT RECORD >>> %s
Len = %s
%s
%s
=====================================
""", args, len(args), args[0], args[1])

    @staticmethod
    def IxL_StatCollectorCommand(*args):
        stats = args[1][3]
        timestamp = args[1][1]
        LOG.debug("""
=====================================
Incoming stats: Time interval: %s
Incoming stats: Time interval: %s
=====================================
""", timestamp, stats)

    @staticmethod
    def set_results_dir(test_controller, results_on_windows):
        """
        If the folder doesn't exists on the Windows Client PC,
        IxLoad will automatically create it.
        """
        try:
            test_controller.setResultDir(results_on_windows)
        except Exception:
            LOG.error('Error creating results dir on Win: %s',
                      results_on_windows)
            raise

    def load_config_file(self, config_file):
        try:
            LOG.debug(config_file)
            repository = self.ixLoad.new("ixRepository", name=config_file)
            return repository
        except Exception:
            LOG.error('Error: IxLoad config file not found: %s', config_file)
            raise

    def start_http_test(self):
        from IxLoad import IxLoad, StatCollectorUtils
        self.ixLoad = IxLoad()
        LOG.debug('--- ixLoad obj: %s', self.ixLoad)
        try:
            self.ixLoad.connect(self.remote_server)
        except:
            LOG.exception('Failed to connect to: %s', self.remote_server)
            raise

        log_tag = "IxLoad-api"
        log_name = "reprun"
        logger = self.ixLoad.new("ixLogger", log_tag, 1)
        log_engine = logger.getEngine()
        log_engine.setLevels(self.ixLoad.ixLogger.kLevelDebug,
                             self.ixLoad.ixLogger.kLevelInfo)
        log_engine.setFile(log_name, 2, 256, 1)

        # Initialize stat collection utilities
        stat_utils = StatCollectorUtils()

        test_controller = self.ixLoad.new("ixTestController", outputDir=1)

        repository = self.load_config_file(self.config_file)

        # Get the first test on the testList
        test_name = repository.testList[0].cget("name")
        test = repository.testList.getItem(test_name)

        self.set_results_dir(test_controller, self.results_on_windows)

        test.config(statsRequired=1, enableResetPorts=1, csvInterval=2,
                    enableForceOwnership=True)
        #  ---- Remap ports ----
        try:
            self.reassign_ports(test, repository, self.ports_to_reassign)
        except Exception:
            LOG.exception("Exception occured during reassign_ports")

        # -----------------------------------------------------------------------
        # Set up stat Collection
        # -----------------------------------------------------------------------
        test_server_handle = test_controller.getTestServerHandle()
        stat_utils.Initialize(test_server_handle)

        # Clear any stats that may have been registered previously
        stat_utils.ClearStats()

        # Define the stats we would like to collect
        stat_utils.AddStat(caption="Watch_Stat_1",
                           statSourceType="HTTP Client",
                           statName="TCP Connections Established",
                           aggregationType="kSum",
                           filterList={})

        stat_utils.AddStat(caption="Watch_Stat_2",
                           statSourceType="HTTP Client",
                           statName="TCP Connection Requests Failed",
                           aggregationType="kSum",
                           filterList={})

        stat_utils.AddStat(caption="Watch_Stat_3",
                           statSourceType="HTTP Server",
                           statName="TCP Connections Established",
                           aggregationType="kSum",
                           filterList={})

        stat_utils.AddStat(caption="Watch_Stat_4",
                           statSourceType="HTTP Server",
                           statName="TCP Connection Requests Failed",
                           aggregationType="kSum",
                           filterList={})

        stat_utils.StartCollector(self.IxL_StatCollectorCommand)

        test_controller.run(test)
        self.ixLoad.waitForTestFinish()

        test_controller.releaseConfigWaitFinish()

        # Stop the collector (running in the tcl event loop)
        stat_utils.StopCollector()

        # Cleanup
        test_controller.generateReport(detailedReport=1, format="PDF;HTML")
        test_controller.releaseConfigWaitFinish()

        self.ixLoad.delete(test)
        self.ixLoad.delete(test_controller)
        self.ixLoad.delete(logger)
        self.ixLoad.delete(log_engine)

        LOG.debug('Retrieving CSV stats from Windows Client PC ...')
        for stat_file in STATS_TO_GET:
            enhanced_stat_file = stat_file.replace('-', '')
            enhanced_stat_file = enhanced_stat_file.replace(' ', '_')
            enhanced_stat_file = enhanced_stat_file.replace('__', '_')

            LOG.debug('Getting csv stat file: %s', (stat_file))
            self.ixLoad.retrieveFileCopy('%s/%s' %
                                         (self.results_on_windows,
                                          stat_file),
                                         os.path.join(
                                             self.result_dir,
                                             'ixLoad_%s' % enhanced_stat_file))
        self.ixLoad.disconnect()

    def parse_run_test(self):
        self.remote_server = self.testinput["remote_server"]
        LOG.debug("remote tcl server: %s", self.remote_server)

        self.config_file = self.testinput["ixload_cfg"]
        LOG.debug("ixload config: %s", self.remote_server)

        self.results_on_windows = 'C:/Results'
        self.result_dir = self.testinput["result_dir"]
        self.chassis = self.testinput["ixia_chassis"]
        LOG.debug("remote ixia chassis: %s", self.chassis)

        self.card = self.testinput["IXIA"]["card"]
        self.ports_to_reassign = [
            [self.chassis, self.card, port] for port in
            self.testinput["IXIA"]["ports"]
        ]

        LOG.debug("Ports to be reassigned: %s", self.ports_to_reassign)


if __name__ == '__main__':
    # Get the args from cmdline and parse and run the test
    testinput = "".join(sys.argv[1:])
    if testinput:
        ixload_obj = IXLOADHttpTest(testinput)
        ixload_obj.start_http_test()
