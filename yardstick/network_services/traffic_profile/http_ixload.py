# Copyright (c) 2016-2019 Intel Corporation
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


class InvalidRxfFile(Exception):
    message = 'Loaded rxf file has unexpected format'


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
        raise raise_exc  # pylint: disable=raising-bad-type
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
        self.links_param = None
        self.test_input = jsonutils.loads(test_input)
        self.parse_run_test()
        self.test = None

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

    def update_network_address(self, net_traffic, address, gateway, prefix):
        """Update ip address and gateway for net_traffic object

        This function update field which configure source addresses for
        traffic which is described by net_traffic object.
        Do not return anything

        :param net_traffic: (IxLoadObjectProxy) proxy obj to tcl net_traffic object
        :param address: (str) Ipv4 range start address
        :param gateway: (str) Ipv4 address of gateway
        :param prefix: (int) subnet prefix
        :return:
        """
        try:
            ethernet = net_traffic.network.getL1Plugin()
            ix_net_l2_ethernet_plugin = ethernet.childrenList[0]
            ix_net_ip_v4_v6_plugin = ix_net_l2_ethernet_plugin.childrenList[0]
            ix_net_ip_v4_v6_range = ix_net_ip_v4_v6_plugin.rangeList[0]

            ix_net_ip_v4_v6_range.config(
                prefix=prefix,
                ipAddress=address,
                gatewayAddress=gateway)
        except Exception:
            raise InvalidRxfFile

    def update_network_mac_address(self, net_traffic, mac):
        """Update MACaddress for net_traffic object

        This function update field which configure MACaddresses for
        traffic which is described by net_traffic object.
        If mac == "auto" then will be configured auto generated mac
        Do not return anything.

        :param net_traffic: (IxLoadObjectProxy) proxy obj to tcl net_traffic object
        :param mac: (str) MAC
        :return:
        """
        try:
            ethernet = net_traffic.network.getL1Plugin()
            ix_net_l2_ethernet_plugin = ethernet.childrenList[0]
            ix_net_ip_v4_v6_plugin = ix_net_l2_ethernet_plugin.childrenList[0]
            ix_net_ip_v4_v6_range = ix_net_ip_v4_v6_plugin.rangeList[0]

            if str(mac).lower() == "auto":
                ix_net_ip_v4_v6_range.config(autoMacGeneration=True)
            else:
                ix_net_ip_v4_v6_range.config(autoMacGeneration=False)
                mac_range = ix_net_ip_v4_v6_range.getLowerRelatedRange(
                    "MacRange")
                mac_range.config(mac=mac)
        except Exception:
            raise InvalidRxfFile

    def update_network_param(self, net_traffic, param):
        """Update net_traffic by parameters specified in param"""

        self.update_network_address(net_traffic, param["address"],
                                    param["gateway"], param["subnet_prefix"])

        self.update_network_mac_address(net_traffic, param["mac"])

    def update_config(self):
        """Update some fields by parameters from traffic profile"""

        net_traffics = {}
        # self.test.communityList is a IxLoadObjectProxy to some tcl object
        # which contain all net_traffic objects in scenario.
        # net_traffic item has a name in format "activity_name@item_name"
        try:
            for item in self.test.communityList:
                net_traffics[item.name.split('@')[1]] = item
        except Exception:  # pylint: disable=broad-except
            pass

        for name, net_traffic in net_traffics.items():
            try:
                param = self.links_param[name]
            except KeyError:
                LOG.debug('There is no param for net_traffic %s', name)
                continue

            self.update_network_param(net_traffic, param["ip"])
            if "uplink" in name:
                self.update_http_client_param(net_traffic, param["http_client"])

    def update_http_client_param(self, net_traffic, param):
        """Update http client object in net_traffic

        Update http client object in net_traffic by parameters
        specified in param.
        Do not return anything.

        :param net_traffic: (IxLoadObjectProxy) proxy obj to tcl net_traffic object
        :param param: (dict) http_client section from traffic profile
        :return:
        """
        page = param.get("page_object")
        if page:
            self.update_page_size(net_traffic, page)
        users = param.get("simulated_users")
        if users:
            self.update_user_count(net_traffic, users)

    def update_page_size(self, net_traffic, page_object):
        """Update page_object field in http client object in net_traffic

        This function update field which configure page_object
        which will be loaded from server
        Do not return anything.

        :param net_traffic: (IxLoadObjectProxy) proxy obj to tcl net_traffic object
        :param page_object: (str) path to object on server e.g. "/4k.html"
        :return:
        """
        try:
            activity = net_traffic.activityList[0]
            ix_http_command = activity.agent.actionList[0]
            ix_http_command.config(pageObject=page_object)
        except Exception:
            raise InvalidRxfFile

    def update_user_count(self, net_traffic, user_count):
        """Update userObjectiveValue field in activity object in net_traffic

        This function update field which configure users count
        which will be simulated by client.
        Do not return anything.

        :param net_traffic: (IxLoadObjectProxy) proxy obj to tcl net_traffic object
        :param user_count: (int) number of simulated users
        :return:
        """
        try:
            activity = net_traffic.activityList[0]
            activity.config(userObjectiveValue=user_count)
        except Exception:
            raise InvalidRxfFile

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
        self.test = repository.testList.getItem(test_name)

        self.set_results_dir(test_controller, self.results_on_windows)

        self.test.config(statsRequired=1, enableResetPorts=1, csvInterval=2,
                         enableForceOwnership=True)

        self.update_config()

        #  ---- Remap ports ----
        try:
            self.reassign_ports(self.test, repository, self.ports_to_reassign)
        except Exception:  # pylint: disable=broad-except
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

        test_controller.run(self.test)
        self.ix_load.waitForTestFinish()

        test_controller.releaseConfigWaitFinish()

        # Stop the collector (running in the tcl event loop)
        self.stat_utils.StopCollector()

        # Cleanup
        test_controller.generateReport(detailedReport=1, format="PDF;HTML")
        test_controller.releaseConfigWaitFinish()

        self.ix_load.delete(self.test)
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

        self.links_param = self.test_input["links_param"]
        LOG.debug("Links param to be applied: %s", self.links_param)


def main(args):
    # Get the args from cmdline and parse and run the test
    test_input = "".join(args[1:])
    if test_input:
        ixload_obj = IXLOADHttpTest(test_input)
        ixload_obj.start_http_test()

if __name__ == '__main__':
    LOG.info("Start http_ixload test")
    main(sys.argv)
