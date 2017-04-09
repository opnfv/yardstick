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

import sys
import os
import logging
import json

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

HTTP_CLIENT_STATS = [["HTTP Client", "TCP Connections Established", "kSum"],
                     ["HTTP Client", "TCP Connection Requests Failed", "kSum"],
                     ["HTTP Client", "HTTP Simulated Users", "kSum"],
                     ["HTTP Client", "HTTP Concurrent Connections", "kSum"],
                     ["HTTP Client", "HTTP Connections", "kSum"],
                     ["HTTP Client", "HTTP Transactions", "kSum"],
                     ["HTTP Client", "HTTP Connection Attempts", "kSum"]
                     ]

HTTP_SERVER_STATS = [["HTTP Server", "TCP Connections Established", "kSum"],
                     ["HTTP Server", "TCP Connection Requests Failed", "kSum"]
                     ]


class IXLOADHttpTest(object):
    def __init__(self, testinput):
        self.testinput = json.loads(testinput)
        self.parse_run_test()

    def get_ports_reassign(self, ports):
        formattedDestination = []
        for currentDestination in ports:
            LOG.debug('\nfor client ports:%s', currentDestination)
            currentDestinationChassis = currentDestination[0]
            currentDestinationCard = currentDestination[1]
            currentDestinationPort = currentDestination[2]
            formattedDestination.append("%s;%s;%s" %
                                        (currentDestinationChassis,
                                         currentDestinationCard,
                                         currentDestinationPort))
        return formattedDestination

    def ReassignPorts(self, test, repository, portsToReassign):
        print '\nReassignPorts:', test, repository

        chassisChain = repository.cget('chassisChain')
        print '\nchassischain:', chassisChain
        clientports = portsToReassign[0::2]
        serverports = portsToReassign[1::2]

        portsToSet = []
        client_ports = self.get_ports_reassign(clientports)
        print '\nReassigning client ports:', client_ports
        portsToSet.extend(client_ports)
        server_ports = self.get_ports_reassign(serverports)
        print '\nReassigning server ports:', server_ports
        portsToSet.extend(server_ports)

        try:
            print '\nReassigning ports:', portsToSet
            print '\nReassigning ports:', portsToSet
            print '\nReassigning ports:', portsToSet
            print '\nReassigning ports:', portsToSet
            print '\nReassigning ports:', portsToSet
            test.setPorts(portsToSet)
        except:
            print '\Error: Could not remap port assignment for:', portsToSet
            self.ixLoad.delete(repository)
            self.ixLoad.disconnect()

    def stat_collector(self, *args):
        print "====================================="
        print "INCOMING STAT RECORD >>> %s" % (args, )
        print "Len = %s" % len(args)
        print args[0]
        print args[1]
        print "====================================="

    def IxL_StatCollectorCommand(self, *args):
        stats = args[1][3]
        timestamp = args[1][1]
        print '====================================='
        print 'Incoming stats: Time interval:', timestamp
        print 'Incoming stats: Time interval:', stats
        print '====================================='

        for index in range(0, len(stats)):
            pass

    def set_results_dir(self, test_controller, results_on_windows):
        """
        If the folder doesn't exists on the Windows Client PC,
        IxLoad will automatically create it.
        """
        try:
            test_controller.setResultDir(results_on_windows)
        except:
            print '\nError creating results dir on Win: ', results_on_windows
            print '\nActual error message: ', sys.exc_info()[0]
            sys.exit()

    def load_config_file(self, config_file):
        try:
            print config_file
            repository = self.ixLoad.new("ixRepository", name=config_file)
            return repository
        except:
            print '\nError: IxLoad config file not found: ', config_file
            sys.exit()

    def start_http_test(self):
        from IxLoad import IxLoad, StatCollectorUtils
        self.ixLoad = IxLoad()
        print '\n--- ixLoad obj:', self.ixLoad
        try:
            self.ixLoad.connect(self.remote_server)
        except:
            sys.exit('Failed to connect to: %s' % self.remote_server)

        log_tag = "IxLoad-api"
        log_name = "reprun"
        logger = self.ixLoad.new("ixLogger", log_tag, 1)
        logEngine = logger.getEngine()
        logEngine.setLevels(self.ixLoad.ixLogger.kLevelDebug,
                            self.ixLoad.ixLogger.kLevelInfo)
        logEngine.setFile(log_name, 2, 256, 1)

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
            self.ReassignPorts(test, repository, self.portsToReassign)
        except:
            pass

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
        self.ixLoad.delete(logEngine)

        print '\nRetrieving CSV stats from Windows Client PC ...'
        for stat_file in STATS_TO_GET:
            enhanced_stat_file = stat_file.replace('-', '')
            enhanced_stat_file = enhanced_stat_file.replace(' ', '_')
            enhanced_stat_file = enhanced_stat_file.replace('__', '_')

            print 'Getting csv stat file: %s' % (stat_file)
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

        self.portsToReassign = []
        self.card = self.testinput["IXIA"]["card"]
        for port in self.testinput["IXIA"]["ports"]:
            self.portsToReassign.append([self.chassis, self.card, port])

        LOG.debug("Ports to be reassigned: %s", self.portsToReassign)

if __name__ == '__main__':
    # Get the args from cmdline and parse and run the test
    testinput = sys.argv
    testinput.pop(0)
    testinput = "".join(testinput)
    if testinput:
        ixload_obj = IXLOADHttpTest(testinput)
        ixload_obj.start_http_test()
