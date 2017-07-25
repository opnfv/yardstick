# Copyright 2015 Intel Corporation.
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

"""Module with implementation of wrapper around the stress tool
"""

import logging
import subprocess
import copy
import time
from tools import tasks
from tools import systeminfo
from tools.load_gen.load_gen import ILoadGenerator

class Stress(ILoadGenerator):
    """Wrapper around stress tool, which generates load based on testcase
    configuration parameter 'load'
    """
    _process_args = {
        'cmd': ['sudo', 'stress'],
        'timeout': 5,
        'logfile': '/tmp/stress.log',
        'expect': r'stress: info:',
        'name': 'stress'
    }
    _logger = logging.getLogger(__name__)

    def __init__(self, stress_config):
        self._running = False
        # copy stress process setings before its modification
        process_args = copy.deepcopy(self._process_args)
        # check if load is requested and correctly configured
        if not (stress_config and 'load' in stress_config and
                'pattern' in stress_config and stress_config['load'] > 0):
            self._logger.error('stress test is not enabled')
            return

        if stress_config['load'] < 0 or stress_config['load'] > 100:
            self._logger.error('defined load %s is out of range 0-100',
                               stress_config['load'])
            return

        # check if load tool binary is available
        if not ('tool' in stress_config) or subprocess.call("which " + stress_config['tool'], shell=True) > 0:
            self._logger.error("stress tool binary '%s' is not available", stress_config['tool'])
            return

        # calculate requested load details and load split among different
        # types of workers
        cpus = systeminfo.get_cpu_cores()
        if 'reserved' in stress_config:
            cpus = cpus - int(stress_config['reserved'])
            if cpus < 1:
                cpus = 1

        workers = round(cpus/100 * int(stress_config['load']))
        cmd_dict = {}
        p_types = {}
        p_total = 0
        for p_type in ('c', 'i', 'm'):
            p_count = stress_config['pattern'].lower().count(p_type)
            if p_count > 0:
                p_types[p_type] = p_count
                p_total += p_count
        if p_total < 1:
            self._logger.error('stress test pattern does not contain any of ' \
                               'c, i or m pattern types')
            return
        for p_type in p_types:
            cmd_dict['-'+p_type] = round(workers* p_types[p_type] / p_total)

        # check for memory load in case that memory workers are detected
        # in case of error or 0%, memory size is not specified and default
        # amount of memory will be used by stress tool
        if '-m' in cmd_dict and cmd_dict['-m'] > 0:
            if 'load_memory' in stress_config and \
                stress_config['load_memory'] > 0 and \
                stress_config['load_memory'] <= 100:

                mem = systeminfo.get_memory_bytes()
                if mem:
                    cmd_dict['--vm-bytes'] = round(int(mem) / 100 * \
                        stress_config['load_memory'] / cmd_dict['-m'])

        # append stress arguments to cmd list used by parent class Process
        for key, value in cmd_dict.items():
            process_args['cmd'].append(key)
            process_args['cmd'].append(str(value))

        # append load generator options if specified
        if 'options' in stress_config:
            process_args['cmd'].append(stress_config['options'])

        # initialize load generator and remember it
        super(Stress, self).__init__(**process_args)
        self._running = True

    def start(self):
        """Start stress load if it was requested
        """
        if self._running:
            super(Stress, self).start()

    def kill(self, signal='-15', sleep=2):
        """
        Kill stress load if it is active
        """
        if self._running and self._child and self._child.isalive():
            tasks.run_task(['sudo', 'pkill', signal, self._proc_name], self._logger)
        time.sleep(sleep)

        self._logger.info(
            'Log available at %s', self._logfile)
        self._running = False
