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
"""IxNetwork traffic generator model.

Provides a model for an IxNetwork machine and appropriate applications.

This requires the following settings in your config file:

* TRAFFICGEN_IXNET_LIB_PATH
    IxNetwork libraries path
* TRAFFICGEN_IXNET_PORT
    IxNetwork host port number
* TRAFFICGEN_IXNET_USER
    IxNetwork host user name
* TRAFFICGEN_IXNET_TESTER_RESULT_DIR
    The result directory on the IxNetwork computer
* TRAFFICGEN_IXNET_DUT_RESULT_DIR
    The result directory on DUT. This needs to map to the same directory
    as the previous one

The following settings are also required. These can likely be shared
with an 'Ixia' traffic generator instance:

* TRAFFICGEN_IXIA_HOST
    IXIA chassis IP address
* TRAFFICGEN_IXIA_CARD
    IXIA card
* TRAFFICGEN_IXIA_PORT1
    IXIA Tx port
* TRAFFICGEN_IXIA_PORT2
    IXIA Rx port

If any of these don't exist, the application will raise an exception
(EAFP).

Additional Configuration:
-------------------------

You will also need to configure the IxNetwork machine to start the IXIA
IxNetworkTclServer. This can be started like so:

1. Connect to the IxNetwork machine using RDP
2. Go to:

    Start->
      Programs ->
        Ixia ->
          IxNetwork ->
            IxNetwork 7.21.893.14 GA ->
              IxNetworkTclServer

   Pin a shortcut to this application to the taskbar.
3. Before running it right click the pinned shortcut  and go to
   "Properties". Here change the port number to your own port number.
   This will be the same value as "TRAFFICGEN_IXNET_PORT" above.
4. You will find this on the shortcut tab under the heading "Target"
5. Finally run it. If you see the following error check that you
   followed the above steps exactly:

       ERROR: couldn't open socket : connection refused

Debugging:
----------

This method of automation is quite error prone as the IxNetwork API
does not give any feedback as to the status of tests. As such, it can
be expected that the user have access to the IxNetwork machine should
this trafficgen need to be debugged.
"""
try:
  # for Python2
  import Tkinter as tkinter ## notice capitalized T in Tkinter 
except ImportError:
  # for Python3
  import tkinter   ## notice lowercase 't' in tkinter here

import logging
import os
import re
import csv

from collections import OrderedDict
from yardstick.traffic_generator.tools.pkt_gen import trafficgen
from yardstick.traffic_generator.conf import settings
from yardstick.traffic_generator.conf import merge_spec
from yardstick.traffic_generator.core.results.results_constants import ResultsConstants

_ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

_RESULT_RE = r'(?:\{kString,result\},\{kString,)(\w+)(?:\})'
_RESULTPATH_RE = r'(?:\{kString,resultPath\},\{kString,)([\\\w\.\-\:]+)(?:\})'


def _build_set_cmds(values, prefix='dict set'):
    """Generate a list of 'dict set' args for Tcl.

    Parse a dictionary and recursively build the arguments for the
    'dict set' Tcl command, given that this is of the format:

        dict set [name...] [key] [value]

    For example, for a non-nested dict (i.e. a non-dict element):

        dict set mydict mykey myvalue

    For a nested dict (i.e. a dict element):

        dict set mydict mysubdict mykey myvalue

    :param values: Dictionary to yield values for
    :param prefix: Prefix to append to output string. Generally the
        already generated part of the command.

    :yields: Output strings to be passed to a `Tcl` instance.
    """
    for key in values:
        value = values[key]

        if isinstance(value, dict):
            _prefix = ' '.join([prefix, key]).strip()
            for subkey in _build_set_cmds(value, _prefix):
                yield subkey
            continue

        # tcl doesn't recognise the strings "True" or "False", only "1"
        # or "0". Special case to convert them
        if isinstance(value, bool):
            value = str(int(value))
        else:
            value = str(value)

        if prefix:
            yield ' '.join([prefix, key, value]).strip()
        else:
            yield ' '.join([key, value]).strip()


class IxNet(trafficgen.ITrafficGenerator):
    """A wrapper around IXIA IxNetwork applications.

    Runs different traffic generator tests through an Ixia traffic
    generator chassis by generating TCL scripts from templates.

    Currently only the RFC2544 tests are implemented.
    """

    def __init__(self):
        """Initialize IXNET members
        """
        super().__init__()
        self._script = os.path.join(settings.getValue('TRAFFICGEN_IXIA_3RD_PARTY'),
                                    settings.getValue('TRAFFICGEN_IXNET_TCL_SCRIPT'))
        self._tclsh = tkinter.Tcl()
        self._cfg = None
        self._logger = logging.getLogger(__name__)
        self._params = None
        self._bidir = None

    def run_tcl(self, cmd):
        """Run a TCL script using the TCL interpreter found in ``tkinter``.

        :param cmd: Command to execute

        :returns: Output of command, where applicable.
        """
        self._logger.debug('%s%s', trafficgen.CMD_PREFIX, cmd)

        output = self._tclsh.eval(cmd)

        return output.split()

    def configure(self):
        """Configure system for IxNetwork.
        """
        self._cfg = {
            'lib_path': settings.getValue('TRAFFICGEN_IXNET_LIB_PATH'),
            # IxNetwork machine configuration
            'machine': settings.getValue('TRAFFICGEN_IXNET_MACHINE'),
            'port': settings.getValue('TRAFFICGEN_IXNET_PORT'),
            'user': settings.getValue('TRAFFICGEN_IXNET_USER'),
            # IXIA chassis configuration
            'chassis': settings.getValue('TRAFFICGEN_IXIA_HOST'),
            'card': settings.getValue('TRAFFICGEN_IXIA_CARD'),
            'port1': settings.getValue('TRAFFICGEN_IXIA_PORT1'),
            'port2': settings.getValue('TRAFFICGEN_IXIA_PORT2'),
            'output_dir':
                settings.getValue('TRAFFICGEN_IXNET_TESTER_RESULT_DIR'),
        }

        self._logger.debug('IXIA configuration configuration : %s', self._cfg)

    def connect(self):
        """Connect to IxNetwork - nothing to be done here
        """
        pass

    def disconnect(self):
        """Disconnect from Ixia chassis.
        """
        pass

    def send_cont_traffic(self, traffic=None, duration=30):
        """See ITrafficGenerator for description
        """
        self.start_cont_traffic(traffic, duration)

        return self.stop_cont_traffic()

    def start_cont_traffic(self, traffic=None, duration=30):
        """Start transmission.
        """
        self.configure()
        self._bidir = traffic['bidir']
        self._params = {}

        self._params['config'] = {
            'binary': False,  # don't do binary search and send one stream
            'duration': duration,
            'framerate': traffic['frame_rate'],
            'multipleStreams': traffic['multistream'],
            'streamType': traffic['stream_type'],
            'rfc2544TestType': 'throughput',
        }
        self._params['traffic'] = self.traffic_defaults.copy()

        if traffic:
            self._params['traffic'] = merge_spec(
                self._params['traffic'], traffic)
        self._cfg['bidir'] = self._bidir

        for cmd in _build_set_cmds(self._cfg, prefix='set'):
            self.run_tcl(cmd)

        for cmd in _build_set_cmds(self._params):
            self.run_tcl(cmd)

        output = self.run_tcl('source {%s}' % self._script)
        if output:
            self._logger.critical(
                'An error occured when connecting to IxNetwork machine...')
            raise RuntimeError('Ixia failed to initialise.')

        self.run_tcl('startRfc2544Test $config $traffic')
        if output:
            self._logger.critical(
                'Failed to start continuous traffic test')
            raise RuntimeError('Continuous traffic test failed to start.')

    def stop_cont_traffic(self):
        """See ITrafficGenerator for description
        """
        return self._wait_result()

    def send_rfc2544_throughput(self, traffic=None, tests=1, duration=20,
                                lossrate=0.0):
        """See ITrafficGenerator for description
        """
        self.start_rfc2544_throughput(traffic, tests, duration, lossrate)

        return self.wait_rfc2544_throughput()

    def start_rfc2544_throughput(self, traffic=None, tests=1, duration=20,
                                 lossrate=0.0):
        """Start transmission.
        """
        self.configure()
        self._bidir = traffic['bidir']
        self._params = {}

        self._params['config'] = {
            'binary': True,
            'tests': tests,
            'duration': duration,
            'lossrate': lossrate,
            'multipleStreams': traffic['multistream'],
            'streamType': traffic['stream_type'],
            'rfc2544TestType': 'throughput',
        }
        self._params['traffic'] = self.traffic_defaults.copy()

        if traffic:
            self._params['traffic'] = merge_spec(
                self._params['traffic'], traffic)
        self._cfg['bidir'] = self._bidir

        for cmd in _build_set_cmds(self._cfg, prefix='set'):
            self.run_tcl(cmd)

        for cmd in _build_set_cmds(self._params):
            self.run_tcl(cmd)

        output = self.run_tcl('source {%s}' % self._script)
        if output:
            self._logger.critical(
                'An error occured when connecting to IxNetwork machine...')
            raise RuntimeError('Ixia failed to initialise.')

        self.run_tcl('startRfc2544Test $config $traffic')
        if output:
            self._logger.critical(
                'Failed to start RFC2544 test')
            raise RuntimeError('RFC2544 test failed to start.')

    def wait_rfc2544_throughput(self):
        """See ITrafficGenerator for description
        """
        return self._wait_result()

    def _wait_result(self):
        """Wait for results.
        """
        def parse_result_string(results):
            """Get path to results file from output

            Check for related errors

            :param results: Text stream from test.

            :returns: Path to results file.
            """
            result_status = re.search(_RESULT_RE, results)
            result_path = re.search(_RESULTPATH_RE, results)

            if not result_status or not result_path:
                self._logger.critical(
                    'Could not parse results from IxNetwork machine...')
                raise ValueError('Failed to parse output.')

            if result_status.group(1) != 'pass':
                self._logger.critical(
                    'An error occured when running tests...')
                raise RuntimeError('Ixia failed to initialise.')

            # transform path into someting useful

            path = result_path.group(1).replace('\\', '/')
            path = os.path.join(path, 'AggregateResults.csv')
            path = path.replace(
                settings.getValue('TRAFFICGEN_IXNET_TESTER_RESULT_DIR'),
                settings.getValue('TRAFFICGEN_IXNET_DUT_RESULT_DIR'))
            return path

        def parse_ixnet_rfc_results(path):
            """Parse CSV output of IxNet RFC2544 test run.

            :param path: Input file path
            """
            results = OrderedDict()

            with open(path, 'r') as in_file:
                reader = csv.reader(in_file, delimiter=',')
                next(reader)
                for row in reader:
                    #Replace null entries added by Ixia with 0s.
                    row = [entry if len(entry) > 0 else '0' for entry in row]

                    # tx_fps and tx_mps cannot be reliably calculated
                    # as the DUT may be modifying the frame size
                    tx_fps = 'Unknown'
                    tx_mbps = 'Unknown'

                    if bool(results.get(ResultsConstants.THROUGHPUT_RX_FPS)) \
                                                                is False:
                        prev_percent_rx = 0.0
                    else:
                        prev_percent_rx = \
                        float(results.get(ResultsConstants.THROUGHPUT_RX_FPS))
                    if float(row[5]) >= prev_percent_rx:
                        results[ResultsConstants.TX_RATE_FPS] = tx_fps
                        results[ResultsConstants.THROUGHPUT_RX_FPS] = row[5]
                        results[ResultsConstants.TX_RATE_MBPS] = tx_mbps
                        results[ResultsConstants.THROUGHPUT_RX_MBPS] = row[6]
                        results[ResultsConstants.TX_RATE_PERCENT] = row[3]
                        results[ResultsConstants.THROUGHPUT_RX_PERCENT] = row[4]
                        results[ResultsConstants.FRAME_LOSS_PERCENT] = row[10]
                        results[ResultsConstants.MIN_LATENCY_NS] = row[11]
                        results[ResultsConstants.MAX_LATENCY_NS] = row[12]
                        results[ResultsConstants.AVG_LATENCY_NS] = row[13]
            return results

        output = self.run_tcl('waitForRfc2544Test')

        # the run_tcl function will return a list with one element. We extract
        # that one element (a string representation of an IXIA-specific Tcl
        # datatype), parse it to find the path of the results file then parse
        # the results file
        return parse_ixnet_rfc_results(parse_result_string(output[0]))

    def send_rfc2544_back2back(self, traffic=None, tests=1, duration=2,
                               lossrate=0.0):
        """See ITrafficGenerator for description
        """
        # NOTE 2 seconds is the recommended duration for a back 2 back
        # test in RFC2544. 50 trials is the recommended number from the
        # RFC also.
        self.start_rfc2544_back2back(traffic, tests, duration, lossrate)

        return self.wait_rfc2544_back2back()

    def start_rfc2544_back2back(self, traffic=None, tests=1, duration=2,
                                lossrate=0.0):
        """Start transmission.
        """
        self.configure()
        self._bidir = traffic['bidir']
        self._params = {}

        self._params['config'] = {
            'binary': True,
            'tests': tests,
            'duration': duration,
            'lossrate': lossrate,
            'multipleStreams': traffic['multistream'],
            'streamType': traffic['stream_type'],
            'rfc2544TestType': 'back2back',
        }
        self._params['traffic'] = self.traffic_defaults.copy()

        if traffic:
            self._params['traffic'] = merge_spec(
                self._params['traffic'], traffic)
        self._cfg['bidir'] = self._bidir

        for cmd in _build_set_cmds(self._cfg, prefix='set'):
            self.run_tcl(cmd)

        for cmd in _build_set_cmds(self._params):
            self.run_tcl(cmd)

        output = self.run_tcl('source {%s}' % self._script)
        if output:
            self._logger.critical(
                'An error occured when connecting to IxNetwork machine...')
            raise RuntimeError('Ixia failed to initialise.')

        self.run_tcl('startRfc2544Test $config $traffic')
        if output:
            self._logger.critical(
                'Failed to start RFC2544 test')
            raise RuntimeError('RFC2544 test failed to start.')

    def wait_rfc2544_back2back(self):
        """Wait for results.
        """
        def parse_result_string(results):
            """Get path to results file from output

            Check for related errors

            :param results: Text stream from test.

            :returns: Path to results file.
            """
            result_status = re.search(_RESULT_RE, results)
            result_path = re.search(_RESULTPATH_RE, results)

            if not result_status or not result_path:
                self._logger.critical(
                    'Could not parse results from IxNetwork machine...')
                raise ValueError('Failed to parse output.')

            if result_status.group(1) != 'pass':
                self._logger.critical(
                    'An error occured when running tests...')
                raise RuntimeError('Ixia failed to initialise.')

            # transform path into something useful

            path = result_path.group(1).replace('\\', '/')
            path = os.path.join(path, 'iteration.csv')
            path = path.replace(
                settings.getValue('TRAFFICGEN_IXNET_TESTER_RESULT_DIR'),
                settings.getValue('TRAFFICGEN_IXNET_DUT_RESULT_DIR'))

            return path

        def parse_ixnet_rfc_results(path):
            """Parse CSV output of IxNet RFC2544 Back2Back test run.

            :param path: Input file path

            :returns: Best parsed result from CSV file.
            """
            results = OrderedDict()
            results[ResultsConstants.B2B_FRAMES] = 0
            results[ResultsConstants.B2B_FRAME_LOSS_PERCENT] = 100

            with open(path, 'r') as in_file:
                reader = csv.reader(in_file, delimiter=',')
                next(reader)
                for row in reader:
                    # if back2back count higher than previously found, store it
                    # Note: row[N] here refers to the Nth column of a row
                    if float(row[14]) <= self._params['config']['lossrate']:
                        if int(row[12]) > \
                         int(results[ResultsConstants.B2B_FRAMES]):
                            results[ResultsConstants.B2B_FRAMES] = int(row[12])
                            results[ResultsConstants.B2B_FRAME_LOSS_PERCENT] = float(row[14])

            return results

        output = self.run_tcl('waitForRfc2544Test')

        # the run_tcl function will return a list with one element. We extract
        # that one element (a string representation of an IXIA-specific Tcl
        # datatype), parse it to find the path of the results file then parse
        # the results file

        return parse_ixnet_rfc_results(parse_result_string(output[0]))

    def send_burst_traffic(self, traffic=None, numpkts=100, duration=20):
        return NotImplementedError('IxNet does not implement send_burst_traffic')

if __name__ == '__main__':
    TRAFFIC = {
        'l3': {
            'proto': 'udp',
            'srcip': '10.1.1.1',
            'dstip': '10.1.1.254',
        },
    }

    with IxNet() as dev:
        print(dev.send_cont_traffic())
        print(dev.send_rfc2544_throughput())
