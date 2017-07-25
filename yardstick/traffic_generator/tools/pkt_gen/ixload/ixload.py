# Copyright 2015-2017 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""IxLoad traffic generator model.

Provides a model for an IxLoad machine and appropriate applications.

This requires the following settings in your config file:

* TRAFFICGEN_IXLOAD_PORT
    IxLoad host port number
* TRAFFICGEN_IXLOAD_USER
    IxLoad host user name
* TRAFFICGEN_IXLOAD_TESTER_RESULT_DIR
    The result directory on the IxLoad computer
* TRAFFICGEN_IXLOAD_DUT_RESULT_DIR
    The result directory on DUT. This needs to map to the same directory
    as the previous one

* TRAFFICGEN_IXLOAD_IXIA_HOST
    IXIA chassis IP address
* TRAFFICGEN_IXLOAD_IXIA_CARD
    IXIA card
* TRAFFICGEN_IXLOAD_IXIA_PORT1
    IXIA Tx port
* TRAFFICGEN_IXLOAD_IXIA_PORT2
    IXIA Rx port

If any of these don't exist, the application will raise an exception
(EAFP).

Debugging:
----------

This method of automation is quite error prone as the IxLoad API
does not give any feedback as to the status of tests. As such, it can
be expected that the user have access to the IxLoad machine should
this trafficgen need to be debugged.
"""
import logging
import os
import re
import csv

from collections import OrderedDict
from yardstick.traffic_generator.tools.pkt_gen import trafficgen
from yardstick.traffic_generator.conf import settings
from yardstick.traffic_generator.conf import merge_spec
from yardstick.traffic_generator.core.results.results_constants import ResultsConstants
from yardstick.common.utils import makedirs
from yardstick.common.constants import YARDSTICK_ROOT_PATH

import time, inspect, os
import os, sys, pprint, time
import logging
import shutil
import json

from subprocess import call
try:
    import requests
except:
    print("The 'requests' module could not be imported.")
    raise sys.exit(1)

try:
        from urllib.parse import urljoin
except ImportError:
         from urlparse import urljoin

#### Disable request info logging
requests_log = logging.getLogger("requests")
requests_log.addHandler(logging.NullHandler())
requests_log.propagate = False

MOUNT_CMD = "mount.cifs //{ip}/Results {RESULTS_MOUNT} -o username={user}," \
                    "password={passwd}"

def getConn(server, port):
    connectionUrl = "http://%s:%s/" % (server, port)
    conn = IxLoadHelper(connectionUrl, "v0")
    return conn

class IxLoadHelper(object):
    def __init__(self, restUrl, apiVersion):
        self._logger = None
        self.httpSession = None
        self.url = IxLoadHelper.urljoin(restUrl, "api")
        self.url = IxLoadHelper.urljoin(self.url, apiVersion)

    @classmethod
    def urljoin(cls, base, end):
        if base and not base.endswith("/"):
            base = base + "/"
        return urljoin(base, str(end))

    def httpRequest(self, method, url="", data="", params={}, headers={}):
        headers["content-type"] = "application/json"

        absUrl = IxLoadHelper.urljoin(self.url, url)
        if self.httpSession is None:
            self.httpSession = requests.Session()            
        result = self.httpSession.request(method, absUrl, data=str(data), params=params, headers=headers)
        return result

    def getrestUrl(self, url):
            resturl = \
                '/'.join(url.split('/')[2:] if 'api' in url else url.split('/'))
            return resturl

    def check_status(self, obj, url):
        ret = True
        if obj["state"] == 'finished':
            if obj["status"] == 'Error':
                raise SystemExit('Failed action "%s" with error "%s"' %
                                 (url, obj.error))
            ret = False

        return ret

    def restGenOp(self, url, payload):
            data = json.dumps(payload)
            replyObj = self.httpRequest("POST", url, data)
            url = replyObj.headers.get('location')
            if url:
                url = self.getrestUrl(url)
                while True:
                    obj = self.genericRestCall("Get", url)
                    if not self.check_status(obj, url):
                        break
                    time.sleep(0.1)
            return replyObj

    def genericRestCall(self, action, actUrl, data={}):
            data = json.dumps(data)
            if action == "Post":
                reply = self.httpRequest("POST", actUrl, data)
                return reply.headers['location'].split('/' )[-1]
            elif action == "Delete":
                return self.httpRequest("DELETE", actUrl, data)
            elif action == "Patch":
                return self.httpRequest("PATCH", actUrl, data)
            elif action == "Get":
                reply = self.httpRequest("GET", actUrl)
                return json.loads(json.dumps(reply.json()))

    def createSession(self, ixLoadVersion):
            sessionsUrl  = "sessions"
            data = {"ixLoadVersion":ixLoadVersion}

            sessionId = self.genericRestCall("Post", sessionsUrl, data)

            newSessionUrl = "%s/%s" % (sessionsUrl, sessionId)
            startSessionUrl = "%s/operations/start" % (newSessionUrl)

            #start the session
            self.restGenOp(startSessionUrl, {})

            self._logger.debug("Created session no %s" % sessionId)

            return newSessionUrl
            
    def deleteSession(self, sessionUrl):
            deleteParams = {}
            self.genericRestCall("Delete", sessionUrl, deleteParams)


    def loadRepository(self, sessionUrl, rxfFilePath):
            loadTestUrl = "%s/ixload/test/operations/loadTest" % (sessionUrl)
            data = {"fullPath":rxfFilePath}
            
            self.restGenOp(loadTestUrl, data)

    def prepare_rxf(self, rxfFilePath, machine, user, passwd):
        script_path = os.path.join(YARDSTICK_ROOT_PATH, "yardstick/traffic_generator/3rd_party/ixload")
        makedirs(settings.getValue("TRAFFICGEN_IXLOAD_DUT_RESULT_DIR"))
        cmd = MOUNT_CMD.format(ip=machine, user=user, passwd=passwd,
                               RESULTS_MOUNT=settings.getValue("TRAFFICGEN_IXLOAD_DUT_RESULT_DIR"))

        if not os.path.ismount(settings.getValue("TRAFFICGEN_IXLOAD_DUT_RESULT_DIR")):
            call(cmd, shell=True)

        ixia_file_name = str(os.path.join(script_path, settings.getValue('TRAFFICGEN_IXLOAD_SCRIPT')))

        shutil.rmtree(settings.getValue("TRAFFICGEN_IXLOAD_DUT_RESULT_DIR"), ignore_errors=True)
        makedirs(settings.getValue("TRAFFICGEN_IXLOAD_DUT_RESULT_DIR"))
        shutil.copy(ixia_file_name, settings.getValue("TRAFFICGEN_IXLOAD_DUT_RESULT_DIR"))

    def runTest(self, sessionUrl):
            startRunUrl = "%s/ixload/test/operations/runTest" % (sessionUrl)
            data = {}

            self.restGenOp(startRunUrl, data)


    def getTestCurrentState(self, sessionUrl):
            activeTestUrl = "%s/ixload/test/activeTest" % (sessionUrl)
            testObj = self.genericRestCall("Get", activeTestUrl)

            return testObj["currentState"]

    def getTestRunError(self, sessionUrl):
            activeTestUrl = "%s/ixload/test/activeTest" % (sessionUrl)
            testObj = self.genericRestCall("Get", activeTestUrl)

            return testObj["testRunError"]

    def waitForTestToReachUnconfiguredState(self, sessionUrl):
            while self.getTestCurrentState(sessionUrl) != 'Unconfigured':
                    time.sleep(0.1)

    def saveResultCsv(self, sessionUrl, resultDir):
        self.genericRestCall("Patch", "%s/ixload/test" % sessionUrl, {"runResultDirFull": "c://Results","outputDir": "true"})

    def parse_http_result(self, results):
        simulated_user = []
        concurrent_connections = []
        http_requests_successful = []
        http_requests_received = []
        tcp_retries = []
        data = {}
        for result in results:
            simulated_user.append(int(result.get("HTTP Simulated Users")))
            concurrent_connections.append(int(result.get("HTTP Concurrent Connections")))
            http_requests_received.append(int(result.get("HTTP Requests Received")))
            http_requests_successful.append(int(result.get("HTTP Requests Successful")))
            tcp_retries.append(int(result.get("TCP Retries")))

        data["HTTP Simulated Users"] = {"min": min(simulated_user),
                "max": max(simulated_user),
                "avg": (sum(simulated_user) / len(simulated_user))}
        data["HTTP Concurrent Connections"] = {
                "min": min(concurrent_connections),
                "max": max(concurrent_connections),
                "avg": (sum(concurrent_connections) / len(concurrent_connections))}
        data["HTTP Requests Received"] = {"min": min(http_requests_received),
                "max": max(http_requests_received),
                "avg": (sum(http_requests_received) / len(http_requests_received))}
        data["HTTP Requests Successful"] = {"min": min(http_requests_successful),
                "max": max(http_requests_successful),
                "avg": (sum(http_requests_successful) / len(http_requests_successful))}
        data["TCP Retries"] = {"min": min(tcp_retries),
                "max": max(tcp_retries),
                "avg": (sum(tcp_retries) / len(tcp_retries))}
        return data

    def pollStats(self, sessionUrl, watchedStatsDict, pollingInterval=4):
            result = []
            collectedTimestamps = {}
            testIsRunning = True

            while testIsRunning:
                time.sleep(pollingInterval)
                runDict = {}
                for statSource in watchedStatsDict.keys():
                    valuesUrl = "%s/ixload/stats/%s/values" % (sessionUrl, statSource)

                    valuesDict = self.genericRestCall("Get", valuesUrl)

                    availableTimeStamps = collectedTimestamps.get(statSource, [])
                    newTimestamps = [int(timestamp) for timestamp in valuesDict.keys() if timestamp not in availableTimeStamps]
                    newTimestamps.sort()

                    for timestamp in newTimestamps:
                        timeStampStr = str(timestamp)

                        collectedTimestamps.setdefault(statSource, []).append(timeStampStr)
                        resultItems = valuesDict[timeStampStr]
                        for caption, value in resultItems.items():
                            if caption in watchedStatsDict[statSource]:
                                self._logger.debug("Timestamp %s - %s -> %s" % (timeStampStr, caption, value))
                                runDict.update({caption: value})
                result.append(runDict)
                                
                testIsRunning = True if self.getTestCurrentState(sessionUrl) == "Running" else False
            self._logger.debug("Stopped receiving stats.")
            return self.parse_http_result(result) 

    def clearChassisList(self, sessionUrl):
            chassisListUrl = "%s/ixload/chassischain/chassisList" % sessionUrl
            deleteParams = {}
            self.genericRestCall("Delete", chassisListUrl, deleteParams)

    def addChassisList(self, sessionUrl, chassisList):
            chassisListUrl = "%s/ixload/chassisChain/chassisList" % (sessionUrl)

            for chassisName in chassisList:
                    data = {"name":chassisName}
                    chassisId = self.genericRestCall("Post", chassisListUrl, data)

                    #refresh the chassis
                    refreshConnectionUrl = "%s/%s/operations/refreshConnection" % (chassisListUrl, chassisId)
                    self.restGenOp(refreshConnectionUrl, {})

    def assignPorts(self, sessionUrl, portListPerCommunity):
            communtiyListUrl = "%s/ixload/test/activeTest/communityList" % sessionUrl
            communityList = self.genericRestCall("Get", communtiyListUrl)
            
            for community in communityList:
                portListForCommunity = portListPerCommunity.get(community["name"])
                portListUrl = "%s/%s/network/portList" % (communtiyListUrl, community["objectID"])

                if portListForCommunity:
                    for portTuple in portListForCommunity:
                        chassisId,cardId,portId = portTuple
                        paramDict = {"chassisId":chassisId, "cardId":cardId, "portId":portId}
                        self.genericRestCall("Post", portListUrl, paramDict)


class IxLoad(trafficgen.ITrafficGenerator):
    """A wrapper around IXIA IxLoad applications.

    Runs different traffic generator tests through an Ixia traffic
    generator chassis by generating TCL scripts from templates.

    Currently only the http_test tests are implemented.
    """

    def __init__(self):
        """Initialize IXLOAD members
        """
        self._script = os.path.join(settings.getValue('TRAFFICGEN_IXIA_3RD_PARTY'),
                                    settings.getValue('TRAFFICGEN_IXNET_TCL_SCRIPT'))
        self._cfg = None
        self._logger = None 
        self._params = None
        self._bidir = None

    def configure(self):
        """Configure system for IxLoad.
        """
        self._cfg = {
            # IxLoad machine configuration
            'machine': settings.getValue('TRAFFICGEN_IXLOAD_MACHINE'),
            'version': settings.getValue('TRAFFICGEN_IXLOAD_VERSION'),
            'port': settings.getValue('TRAFFICGEN_IXLOAD_REST_PORT'),
            'user': settings.getValue('TRAFFICGEN_IXLOAD_USER'),
            'pass': settings.getValue('TRAFFICGEN_IXLOAD_PASSWORD'),
            # IXIA chassis configuration
            'chassis': [settings.getValue('TRAFFICGEN_IXLOAD_IXIA_HOST')],
            'card': settings.getValue('TRAFFICGEN_IXLOAD_IXIA_CARD'),
            'port1': settings.getValue('TRAFFICGEN_IXLOAD_IXIA_PORT1'),
            'port2': settings.getValue('TRAFFICGEN_IXLOAD_IXIA_PORT2'),
            'output_dir':
                settings.getValue('TRAFFICGEN_IXLOAD_TESTER_RESULT_DIR'),

            'rxfpath': os.path.join(settings.getValue('TRAFFICGEN_IXLOAD_TESTER_RESULT_DIR'),
                         settings.getValue("TRAFFICGEN_IXLOAD_SCRIPT"))
        }

        self.stats = {
                "HTTPClient": ["HTTP Simulated Users", "HTTP Concurrent Connections", "HTTP Requests Successful"],
                "HTTPServer": ["HTTP Requests Received", "TCP Retries"]
                }
        self.portList = {
                "HTTP client@client network" : [(1,self._cfg["card"],self._cfg["port1"])],
                "HTTP server@server network" : [(1,self._cfg["card"],self._cfg["port2"])],
                }
        self.IxLoadUtils = getConn(self._cfg['machine'], self._cfg['port'])
        self.IxLoadUtils._logger = self._logger
        self._logger.debug('IXIA configuration configuration : %s', self._cfg)

    def connect(self):
        """Connect to IxLoad - nothing to be done here
        """
        pass

    def disconnect(self):
        """Disconnect from Ixia chassis.
        """
        pass

    def send_cont_traffic(self, traffic=None, duration=30):
        """See ITrafficGenerator for description
        """
        ret = self.start_cont_traffic(traffic, duration)

        return ret

    def start_cont_traffic(self, traffic=None, duration=30):
        """Start transmission.
        """
        return self.start_cont_http_traffic(traffic)

    def stop_cont_traffic(self):
        """See ITrafficGenerator for description
        """
        return NotImplementedError('IxLoad does not implement stop_cont_traffic')

    def send_http_test_throughput(self, traffic=None, tests=1, duration=20,
                                lossrate=0.0):
        """See ITrafficGenerator for description
        """
        return NotImplementedError('IxLoad does not implement send_http_test_throughput')

    def start_cont_http_traffic(self, traffic=None, tests=1, duration=20,
                                lossrate=0.0):
        """See ITrafficGenerator for description
        """

        self.configure()
        
        #create a session
        self._logger.debug("Creating a new session...")
        sessionUrl = self.IxLoadUtils.createSession(self._cfg["version"])
        self._logger.debug("Session created.")

        self._logger.debug("Prepare rxf repository %s..." % (settings.getValue('TRAFFICGEN_IXLOAD_TESTER_RESULT_DIR')))
        self.IxLoadUtils.prepare_rxf(settings.getValue('TRAFFICGEN_IXLOAD_TESTER_RESULT_DIR'), self._cfg["machine"],self._cfg["user"], self._cfg["pass"])
        self._logger.debug("Repository rxf done.")

        #load a repository
        self._logger.debug("Loading reposiory %s..." % self._cfg["rxfpath"])
        self.IxLoadUtils.loadRepository(sessionUrl, self._cfg["rxfpath"])
        self._logger.debug("Repository loaded.")

        self._logger.debug("Clearing chassis list...")
        self.IxLoadUtils.clearChassisList(sessionUrl)
        self._logger.debug("Chassis list cleared.")

        self._logger.debug("Adding chassis %s..." % (self._cfg["chassis"]))
        self.IxLoadUtils.addChassisList(sessionUrl, self._cfg["chassis"])
        self._logger.debug("Chassis added.")

        self._logger.debug("Assigning new ports...")
        self.IxLoadUtils.assignPorts(sessionUrl, self.portList)
        self._logger.debug("Ports assigned.")

        self._logger.debug("Configure outputdir ...") 
        self.IxLoadUtils.saveResultCsv(sessionUrl, settings.getValue('TRAFFICGEN_IXLOAD_TESTER_RESULT_DIR'))
        self._logger.debug("Repository saved.")

        self._logger.debug("Starting the test...")
        self.IxLoadUtils.runTest(sessionUrl)
        self._logger.debug("Test started.")

        self._logger.debug("Polling values for stats %s..." % (self.stats))
        result = self.IxLoadUtils.pollStats(sessionUrl, self.stats)

        self._logger.debug("Test finished.")

        self._logger.debug("Checking test status...")
        testRunError =  self.IxLoadUtils.getTestRunError(sessionUrl)
        if testRunError:
                self._logger.debug("The test exited with the following error: %s" % testRunError)
        else:
                self._logger.debug("The test completed successfully.")

        self._logger.debug("Waiting for test to clean up and reach 'Unconfigured' state...")
        self.IxLoadUtils.waitForTestToReachUnconfiguredState(sessionUrl)
        self._logger.debug("Test is back in 'Unconfigured' state.")

        self._logger.debug("Closing IxLoad session...")
        self.IxLoadUtils.deleteSession(sessionUrl)
        self._logger.debug("IxLoad session closed.")
        return result

    def start_http_test_throughput(self, traffic=None, tests=1, duration=20,
                                 lossrate=0.0):
        """Start transmission.
        """
        return NotImplementedError('IxLoad does not implement start_http_test_throughput')

    def wait_http_test_throughput(self):
        """See ITrafficGenerator for description
        """
        return NotImplementedError('IxLoad does not implement wait_http_test_throughput')

    def send_http_test_back2back(self, traffic=None, tests=1, duration=2,
                               lossrate=0.0):
        """See ITrafficGenerator for description
        """
        self.start_http_test_back2back(traffic, tests, duration, lossrate)

        return self.wait_http_test_back2back()

    def start_http_test_back2back(self, traffic=None, tests=1, duration=2,
                                lossrate=0.0):
        """Start transmission.
        """
        return NotImplementedError('IxLoad does not implement start_http_test_back2back')

    def wait_http_test_back2back(self):
        """Wait for results.
        """
        pass

    def send_burst_traffic(self, traffic=None, numpkts=100, duration=20):
        return NotImplementedError('IxLoad does not implement send_burst_traffic')
