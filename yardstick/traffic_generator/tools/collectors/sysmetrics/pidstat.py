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

"""module for statistics collection by pidstat

Provides system statistics collected between calls of start() and stop()
by command line tool pidstat (part of sysstat package)

This requires the following setting in your config:

* PIDSTAT_MONITOR = ['ovs-vswitchd', 'ovsdb-server', 'kvm']
    processes to be monitorred by pidstat

* PIDSTAT_OPTIONS = '-dur'
    options which will be passed to pidstat, i.e. what
    statistics should be collected by pidstat

* LOG_FILE_PIDSTAT = 'pidstat.log'
    log file for pidstat; it defines suffix, which will be added
    to testcase name. Pidstat detailed statistics will be stored separately
    for every testcase.

If this doesn't exist, the application will raise an exception
(EAFP).
"""

import os
import logging
import subprocess
import time
from collections import OrderedDict
from tools import tasks
from tools import systeminfo
from tools.collectors.collector import collector
from conf import settings

_ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

class Pidstat(collector.ICollector):
    """A logger of system statistics based on pidstat

    It collects statistics based on configuration
    """
    _logger = logging.getLogger(__name__)

    def __init__(self, results_dir, test_name):
        """
        Initialize collection of statistics
        """
        self._log = os.path.join(results_dir,
                                 settings.getValue('LOG_FILE_PIDSTAT') +
                                 '_' + test_name + '.log')
        self._results = OrderedDict()
        self._pid = 0

    def start(self):
        """
        Starts collection of statistics by pidstat and stores them
        into the file in directory with test results
        """
        monitor = settings.getValue('PIDSTAT_MONITOR')
        self._logger.info('Statistics are requested for: ' + ', '.join(monitor))
        pids = systeminfo.get_pids(monitor)
        if pids:
            with open(self._log, 'w') as logfile:
                cmd = ['sudo', 'LC_ALL=' + settings.getValue('DEFAULT_CMD_LOCALE'),
                       'pidstat', settings.getValue('PIDSTAT_OPTIONS'),
                       '-p', ','.join(pids),
                       str(settings.getValue('PIDSTAT_SAMPLE_INTERVAL'))]
                self._logger.debug('%s', ' '.join(cmd))
                self._pid = subprocess.Popen(cmd, stdout=logfile, bufsize=0).pid

    def stop(self):
        """
        Stops collection of statistics by pidstat and stores statistic summary
        for each monitored process into self._results dictionary
        """
        if self._pid:
            self._pid = 0
            # in python3.4 it's not possible to send signal through pid of sudo
            # process, so all pidstat processes are interupted instead
            # as a workaround
            tasks.run_task(['sudo', 'pkill', '--signal', '2', 'pidstat'],
                           self._logger)

        self._logger.info(
            'Pidstat log available at %s', self._log)

        # let's give pidstat some time to write down average summary
        time.sleep(2)

        # parse average values from log file and store them to _results dict
        self._results = OrderedDict()
        logfile = open(self._log, 'r')
        with logfile:
            line = logfile.readline()
            while line:
                line = line.strip()
                # process only lines with summary
                if line[0:7] == 'Average':
                    if line[-7:] == 'Command':
                        # store header fields if detected
                        tmp_header = line[8:].split()
                    else:
                        # combine stored header fields with actual values
                        tmp_res = OrderedDict(zip(tmp_header,
                                                  line[8:].split()))
                        # use process's name and its  pid as unique key
                        key = tmp_res.pop('Command') + '_' + tmp_res['PID']
                        # store values for given command into results dict
                        if key in self._results:
                            self._results[key].update(tmp_res)
                        else:
                            self._results[key] = tmp_res

                line = logfile.readline()

    def get_results(self):
        """Returns collected statistics.
        """
        return self._results

    def print_results(self):
        """Logs collected statistics.
        """
        for process in self._results:
            logging.info("Process: " + '_'.join(process.split('_')[:-1]))
            for(key, value) in self._results[process].items():
                logging.info("         Statistic: " + str(key) +
                             ", Value: " + str(value))
