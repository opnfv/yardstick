# Copyright 2016 Intel Corporation.
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
""" Vsperf specific scenario definition """

from __future__ import absolute_import
import logging
import os
import subprocess
import csv

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Vsperf(base.Scenario):
    """Execute vsperf with defined parameters

  Parameters:
    traffic_type - to specify the type of traffic executed by traffic generator
    the valid values are "rfc2544", "continuous", "back2back"
        type:    string
        default: "rfc2544"
    frame_size - a frame size for which test should be executed;
        Multiple frame sizes can be tested by modification of sequence runner
        section inside TC YAML definition.
        type:    string
        default: "64"
    bidirectional - speficies if traffic will be uni (False) or bi-directional
        (True)
        type:    string
        default: False
    iload - specifies frame rate
        type:    string
        default: 100
    multistream - the number of simulated streams
        type:    string
        default: 0 (disabled)
    stream_type - specifies network layer used for multistream simulation
        the valid values are "L4", "L3" and "L2"
        type:    string
        default: "L4"
    test_params - specifies a string with a list of vsperf configuration
        parameters, which will be passed to the '--test-params' CLI argument;
        Parameters should be stated in the form of 'param=value' and separated
        by a semicolon. Please check VSPERF documentation for details about
        available configuration parameters and their data types.
        In case that both 'test_params' and 'conf_file' are specified,
        then values from 'test_params' will override values defined
        in the configuration file.
        type:    string
        default: NA
    conf_file - path to the vsperf configuration file, which will be uploaded
        to the VM;
        In case that both 'test_params' and 'conf_file' are specified,
        then values from 'test_params' will override values defined
        in configuration file.
        type:   string
        default: NA
    setup_script - path to the setup script, which will be executed during
        setup and teardown phases
        type:   string
        default: NA
    trafficgen_port1 - specifies device name of 1st interface connected to
        the trafficgen
        type:   string
        default: NA
    trafficgen_port2 - specifies device name of 2nd interface connected to
        the trafficgen
        type:   string
        default: NA
    external_bridge - specifies name of external bridge configured in OVS
        type:   string
        default: "br-ex"

    """
    __scenario_type__ = "Vsperf"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False
        self.client = None
        self.tg_port1 = self.scenario_cfg['options'].get('trafficgen_port1',
                                                         None)
        self.tg_port2 = self.scenario_cfg['options'].get('trafficgen_port2',
                                                         None)
        self.br_ex = self.scenario_cfg['options'].get('external_bridge',
                                                      'br-ex')
        self.vsperf_conf = self.scenario_cfg['options'].get('conf_file', None)
        if self.vsperf_conf:
            self.vsperf_conf = os.path.expanduser(self.vsperf_conf)

        self.setup_script = self.scenario_cfg['options'].get('setup_script',
                                                             None)
        if self.setup_script:
            self.setup_script = os.path.expanduser(self.setup_script)

        self.test_params = self.scenario_cfg['options'].get('test-params',
                                                            None)

    def setup(self):
        """scenario setup"""
        vsperf = self.context_cfg['host']

        # add trafficgen interfaces to the external bridge
        if self.tg_port1:
            subprocess.call('sudo bash -c "ovs-vsctl add-port %s %s"' %
                            (self.br_ex, self.tg_port1), shell=True)
        if self.tg_port2:
            subprocess.call('sudo bash -c "ovs-vsctl add-port %s %s"' %
                            (self.br_ex, self.tg_port2), shell=True)

        # copy vsperf conf to VM
        self.client = ssh.SSH.from_node(vsperf, defaults={
            "user": "ubuntu", "password": "ubuntu"
        })
        # traffic generation could last long
        self.client.wait(timeout=1800)

        # copy script to host
        self.client._put_file_shell(self.vsperf_conf, '~/vsperf.conf')

        # execute external setup script
        if self.setup_script:
            cmd = "%s setup" % (self.setup_script)
            LOG.info("Execute setup script \"%s\"", cmd)
            subprocess.call(cmd, shell=True)

        self.setup_done = True

    def run(self, result):
        """ execute the vsperf benchmark and return test results
            within result dictionary
        """
        def add_test_params(options, option, default_value):
            """return parameter and its value as a string to be passed
               to the VSPERF inside --test-params argument

               Parameters:
                options - dictionary with scenario options
                option  - a name of option to be added to the string
                default_value - value to be used in case that option
                    is not defined inside scenario options
            """
            if option in options:
                return "%s=%s" % (option, options[option])
            elif default_value is not None:
                return "%s=%s" % (option, default_value)
            else:
                return None

        if not self.setup_done:
            self.setup()

        # remove results from previous tests
        self.client.execute("rm -rf /tmp/results*")

        # get vsperf options
        options = self.scenario_cfg['options']
        test_params = []
        test_params.append(add_test_params(options, "traffic_type", "rfc2544"))
        test_params.append(add_test_params(options, "bidirectional", "False"))
        test_params.append(add_test_params(options, "iload", 100))
        test_params.append(add_test_params(options, "multistream", None))
        test_params.append(add_test_params(options, "stream_type", None))
        if 'frame_size' in options:
            test_params.append("%s=(%s,)" % ('TRAFFICGEN_PKT_SIZES',
                                             options['frame_size']))
        if 'test_params' in options:
            test_params.append(options['test_params'])

        # filter empty parameters and escape quotes and double quotes
        test_params = [tp.replace('"', '\\"').replace("'", "\\'")
                       for tp in test_params if tp]

        # execute vsperf
        cmd = "source ~/vsperfenv/bin/activate ; cd vswitchperf ; "
        cmd += "./vsperf --mode trafficgen "
        if self.vsperf_conf:
            cmd += "--conf-file ~/vsperf.conf "
        cmd += "--test-params=\"%s\"" % (';'.join(test_params))
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        # get test results
        cmd = "cat /tmp/results*/result.csv"
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        # convert result.csv to JSON format
        reader = csv.DictReader(stdout.split('\r\n'))
        result.update(next(reader))

        # sla check; go through all defined SLAs and check if values measured
        # by VSPERF are higher then those defined by SLAs
        if 'sla' in self.scenario_cfg and \
           'metrics' in self.scenario_cfg['sla']:
            for metric in self.scenario_cfg['sla']['metrics'].split(','):
                assert metric in result, \
                    '%s is not collected by VSPERF' % (metric)
                assert metric in self.scenario_cfg['sla'], \
                    '%s is not defined in SLA' % (metric)
                vs_res = float(result[metric])
                sla_res = float(self.scenario_cfg['sla'][metric])
                assert vs_res >= sla_res, \
                    'VSPERF_%s(%f) < SLA_%s(%f)' % \
                    (metric, vs_res, metric, sla_res)

    def teardown(self):
        """cleanup after the test execution"""
        # remove trafficgen interfaces from the external bridge
        if self.tg_port1:
            subprocess.call('sudo bash -c "ovs-vsctl del-port %s %s"' %
                            (self.br_ex, self.tg_port1), shell=True)
        if self.tg_port2:
            subprocess.call('sudo bash -c "ovs-vsctl del-port %s %s"' %
                            (self.br_ex, self.tg_port2), shell=True)

        # execute external setup script
        if self.setup_script:
            cmd = "%s teardown" % (self.setup_script)
            LOG.info("Execute setup script \"%s\"", cmd)
            subprocess.call(cmd, shell=True)

        self.setup_done = False
