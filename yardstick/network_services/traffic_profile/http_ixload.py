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
import collections

# ixload uses its own py2. So importing jsonutils fails. So adding below
# workaround to support call from yardstick
try:
    from oslo_serialization import jsonutils
except ImportError:
    import json as jsonutils


class ErrorClass(object):

    def __init__(self, *args, **kwargs):
        if 'test' not in kwargs:
            raise RuntimeError

    def __getattr__(self, item):
        raise AttributeError


try:
    from IxLoad import IxLoad, StatCollectorUtils
except ImportError:
    IxLoad = ErrorClass
    StatCollectorUtils = ErrorClass

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


INCOMING_STAT_RECORD_TEMPLATE = """
=====================================
INCOMING STAT RECORD >>> %s
Len = %s
%s
%s
=====================================
"""

INCOMING_STAT_INTERVAL_TEMPLATE = """
=====================================
Incoming stats: Time interval: %s
Incoming stats: Time interval: %s
=====================================
"""


def validate_non_string_sequence(value, default=None, raise_exc=None):
    if isinstance(value, collections.Sequence) and not isinstance(value, str):
        return value
    if raise_exc:
        raise raise_exc
    return default


def join_non_strings(separator, *non_strings):
    try:
        non_strings = validate_non_string_sequence(non_strings[0], raise_exc=RuntimeError)
    except (IndexError, RuntimeError):
        pass
    return str(separator).join(str(non_string) for non_string in non_strings)


class IXLOADHttpTest(object):

    def __init__(self, test_input):
        self.ix_load = None
        self.stat_utils = None
        self.remote_server = None
        self.config_file = None
        self.results_on_windows = None
        self.result_dir = None
        self.chassis = None
        self.card = None
        self.ports_to_reassign = None
        self.test_input = jsonutils.loads(test_input)
        self.parse_run_test()

    @staticmethod
    def format_ports_for_reassignment(ports):
        formatted = [join_non_strings(';', p) for p in ports if len(p) == 3]
        LOG.debug('for client ports:%s', os.linesep.join(formatted))
        return formatted

    def reassign_ports(self, test, repository, ports_to_reassign):
        LOG.debug('ReassignPorts: %s %s', test, repository)

        chassis_chain = repository.cget('chassisChain')
        LOG.debug('chassischain: %s', chassis_chain)
        client_ports = ports_to_reassign[0::2]
        server_ports = ports_to_reassign[1::2]

        client_ports = self.format_ports_for_reassignment(client_ports)
        LOG.debug('Reassigning client ports: %s', client_ports)
        server_ports = self.format_ports_for_reassignment(server_ports)
        LOG.debug('Reassigning server ports: %s', server_ports)
        ports_to_set = client_ports + server_ports

        try:
            LOG.debug('Reassigning ports: %s', ports_to_set)
            test.setPorts(ports_to_set)
        except Exception:
            LOG.error('Error: Could not remap port assignment for: %s',
                      ports_to_set)
            self.ix_load.delete(repository)
            self.ix_load.disconnect()
            raise

    @staticmethod
    def stat_collector(*args):
        LOG.debug(INCOMING_STAT_RECORD_TEMPLATE, args, len(args), args[0], args[1])

    @staticmethod
    def IxL_StatCollectorCommand(*args):
        stats = args[1][3]
        timestamp = args[1][1]
        LOG.debug(INCOMING_STAT_INTERVAL_TEMPLATE, timestamp, stats)

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
            repository = self.ix_load.new("ixRepository", name=config_file)
            return repository
        except Exception:
            LOG.error('Error: IxLoad config file not found: %s', config_file)
            raise

    def start_http_test(self):
        self.ix_load = IxLoad()

        LOG.debug('--- ixLoad obj: %s', self.ix_load)
        try:
            self.ix_load.connect(self.remote_server)
        except Exception:
            raise

        log_tag = "IxLoad-api"
        log_name = "reprun"
        logger = self.ix_load.new("ixLogger", log_tag, 1)
        log_engine = logger.getEngine()
        log_engine.setLevels(self.ix_load.ixLogger.kLevelDebug,
                             self.ix_load.ixLogger.kLevelInfo)
        log_engine.setFile(log_name, 2, 256, 1)

        # Initialize stat collection utilities
        self.stat_utils = StatCollectorUtils()

        test_controller = self.ix_load.new("ixTestController", outputDir=1)

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
            LOG.exception("Exception occurred during reassign_ports")

        # -----------------------------------------------------------------------
        # Set up stat Collection
        # -----------------------------------------------------------------------
        test_server_handle = test_controller.getTestServerHandle()
        self.stat_utils.Initialize(test_server_handle)

        # Clear any stats that may have been registered previously
        self.stat_utils.ClearStats()

        # Define the stats we would like to collect
        self.stat_utils.AddStat(caption="Watch_Stat_1",
                                statSourceType="HTTP Client",
                                statName="TCP Connections Established",
                                aggregationType="kSum",
                                filterList={})

        self.stat_utils.AddStat(caption="Watch_Stat_2",
                                statSourceType="HTTP Client",
                                statName="TCP Connection Requests Failed",
                                aggregationType="kSum",
                                filterList={})

        self.stat_utils.AddStat(caption="Watch_Stat_3",
                                statSourceType="HTTP Server",
                                statName="TCP Connections Established",
                                aggregationType="kSum",
                                filterList={})

        self.stat_utils.AddStat(caption="Watch_Stat_4",
                                statSourceType="HTTP Server",
                                statName="TCP Connection Requests Failed",
                                aggregationType="kSum",
                                filterList={})

        self.stat_utils.StartCollector(self.IxL_StatCollectorCommand)

        test_controller.run(test)
        self.ix_load.waitForTestFinish()

        test_controller.releaseConfigWaitFinish()

        # Stop the collector (running in the tcl event loop)
        self.stat_utils.StopCollector()

        # Cleanup
        test_controller.generateReport(detailedReport=1, format="PDF;HTML")
        test_controller.releaseConfigWaitFinish()

        self.ix_load.delete(test)
        self.ix_load.delete(test_controller)
        self.ix_load.delete(logger)
        self.ix_load.delete(log_engine)

        LOG.debug('Retrieving CSV stats from Windows Client PC ...')
        for stat_file in STATS_TO_GET:
            enhanced_stat_file = stat_file.replace('-', '')
            enhanced_stat_file = enhanced_stat_file.replace(' ', '_')
            enhanced_stat_file = enhanced_stat_file.replace('__', '_')

            LOG.debug('Getting csv stat file: %s', stat_file)
            src_file = os.path.join(self.results_on_windows, stat_file)
            dst_file = os.path.join(self.result_dir, '_'.join(['ixLoad', enhanced_stat_file]))
            self.ix_load.retrieveFileCopy(src_file, dst_file)

        self.ix_load.disconnect()

    def parse_run_test(self):
        self.remote_server = self.test_input["remote_server"]
        LOG.debug("remote tcl server: %s", self.remote_server)

        self.config_file = self.test_input["ixload_cfg"]
        LOG.debug("ixload config: %s", self.remote_server)

        self.results_on_windows = 'C:/Results'
        self.result_dir = self.test_input["result_dir"]
        self.chassis = self.test_input["ixia_chassis"]
        LOG.debug("remote ixia chassis: %s", self.chassis)

        self.card = self.test_input["IXIA"]["card"]
        self.ports_to_reassign = [
            [self.chassis, self.card, port] for port in
            self.test_input["IXIA"]["ports"]
        ]

        LOG.debug("Ports to be reassigned: %s", self.ports_to_reassign)


def main(args):
    # Get the args from cmdline and parse and run the test
    test_input = "".join(args[1:])
    if test_input:
        ixload_obj = IXLOADHttpTest(test_input)
        ixload_obj.start_http_test()

if __name__ == '__main__':
    LOG.info("Start http_ixload test")
    main(sys.argv)
