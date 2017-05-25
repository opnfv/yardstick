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
""" VsperfDPDK specific scenario definition """

from __future__ import absolute_import
import pkg_resources
import logging
import os
import subprocess
import csv
import time

import yardstick.ssh as ssh
import yardstick.common.utils as utils
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class VsperfDPDK(base.Scenario):
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
    __scenario_type__ = "VsperfDPDK"

    TESTPMD_SCRIPT = 'testpmd_vsperf.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.moongen_host_ip = \
            scenario_cfg['options'].get('moongen_host_ip', "127.0.0.1")
        self.moongen_port1_mac = \
            scenario_cfg['options'].get('moongen_port1_mac', None)
        self.moongen_port2_mac = \
            scenario_cfg['options'].get('moongen_port2_mac', None)
        self.dpdk_setup_done = False
        self.setup_done = False
        self.client = None
        self.tg_port1 = \
            self.scenario_cfg['options'].get('trafficgen_port1', None)
        self.tg_port2 = \
            self.scenario_cfg['options'].get('trafficgen_port2', None)
        self.tgen_port1_mac = None
        self.tgen_port2_mac = None
        self.br_ex = self.scenario_cfg['options'].get('external_bridge',
                                                      'br-ex')
        self.vsperf_conf = self.scenario_cfg['options'].get('conf_file', None)
        if self.vsperf_conf:
            self.vsperf_conf = os.path.expanduser(self.vsperf_conf)

        self.moongen_helper = \
            self.scenario_cfg['options'].get('moongen_helper_file', None)
        if self.moongen_helper:
            self.moongen_helper = os.path.expanduser(self.moongen_helper)

        self.setup_script = self.scenario_cfg['options'].get('setup_script',
                                                             None)
        if self.setup_script:
            self.setup_script = os.path.expanduser(self.setup_script)

        self.test_params = self.scenario_cfg['options'].get('test-params',
                                                            None)

    def setup(self):
        """scenario setup"""
        vsperf = self.context_cfg['host']

        task_id = self.scenario_cfg['task_id']
        context_number = task_id.split('-')[0]
        self.tg_port1_nw = vsperf.get('name', 'demo') + \
            "-" + context_number + "-" + \
            self.scenario_cfg['options'].get('trafficgen_port1_nw', 'test2')
        self.tg_port2_nw = vsperf.get('name', 'demo') + \
            "-" + context_number + "-" + \
            self.scenario_cfg['options'].get('trafficgen_port2_nw', 'test3')

        # copy vsperf conf to VM
        self.client = ssh.SSH.from_node(vsperf, defaults={
            "user": "ubuntu", "password": "ubuntu"
        })
        # traffic generation could last long
        self.client.wait(timeout=1800)

        # copy script to host
        self.client._put_file_shell(self.vsperf_conf, '~/vsperf.conf')

        self.client._put_file_shell(
            self.moongen_helper,
            '~/vswitchperf/tools/pkt_gen/moongen/moongen.py')

        # execute external setup script
        if self.setup_script:
            cmd = "%s setup" % (self.setup_script)
            LOG.info("Execute setup script \"%s\"", cmd)
            subprocess.call(cmd, shell=True)

        self.setup_done = True

    def dpdk_setup(self):
        """dpdk setup"""

        # setup dpdk loopback in VM
        self.testpmd_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            VsperfDPDK.TESTPMD_SCRIPT)

        self.client._put_file_shell(self.testpmd_script,
                                    '~/testpmd_vsperf.sh')

        # disable Address Space Layout Randomization (ASLR)
        cmd = "echo 0 | sudo tee /proc/sys/kernel/randomize_va_space"
        self.client.send_command(cmd)

        if not self._is_dpdk_setup():
            self.tgen_port1_ip = \
                utils.get_port_ip(self.client, self.tg_port1)
            self.tgen_port1_mac = \
                utils.get_port_mac(self.client, self.tg_port1)
            self.client.run("tee ~/.testpmd.ipaddr.port1 > /dev/null",
                            stdin=self.tgen_port1_ip)
            self.client.run("tee ~/.testpmd.macaddr.port1 > /dev/null",
                            stdin=self.tgen_port1_mac)
            self.tgen_port2_ip = \
                utils.get_port_ip(self.client, self.tg_port2)
            self.tgen_port2_mac = \
                utils.get_port_mac(self.client, self.tg_port2)
            self.client.run("tee ~/.testpmd.ipaddr.port2 > /dev/null",
                            stdin=self.tgen_port2_ip)
            self.client.run("tee ~/.testpmd.macaddr.port2 > /dev/null",
                            stdin=self.tgen_port2_mac)
            cmd = "ip link set %s down" % (self.tg_port1)
            LOG.debug("Executing command: %s", cmd)
            self.client.send_command(cmd)
            cmd = "ip link set %s down" % (self.tg_port2)
            LOG.debug("Executing command: %s", cmd)
            self.client.send_command(cmd)
        else:
            cmd = "cat ~/.testpmd.macaddr.port1"
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)
            self.tgen_port1_mac = stdout
            cmd = "cat ~/.testpmd.macaddr.port2"
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)
            self.tgen_port2_mac = stdout

        cmd = "screen -d -m sudo -E bash ~/testpmd_vsperf.sh %s %s" % \
            (self.moongen_port1_mac, self.moongen_port2_mac)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        time.sleep(1)

        self.dpdk_setup_done = True

    def _is_dpdk_setup(self):
        """Is dpdk already setup in the host?"""
        is_run = True
        cmd = "ip a | grep %s 2>/dev/null" % (self.tg_port1)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if stdout:
            is_run = False
        return is_run

    def run(self, result):
        """ execute the vsperf benchmark and return test results
            within result dictionary
        """

        if not self.setup_done:
            self.setup()

        # remove results from previous tests
        self.client.execute("rm -rf /tmp/results*")

        # get vsperf options
        options = self.scenario_cfg['options']
        test_params = []
        traffic_type = self.scenario_cfg['options'].\
            get("traffic_type", "rfc2544_throughput")
        multistream = self.scenario_cfg['options'].get("multistream", 1)

        if not self.dpdk_setup_done:
            self.dpdk_setup()

        if 'frame_size' in options:
            test_params.append("%s=(%s,)" % ('TRAFFICGEN_PKT_SIZES',
                                             options['frame_size']))

        cmd = "openstack network show %s | grep segmentation_id | " \
              "cut -d '|' -f 3" % (self.tg_port1_nw)
        LOG.debug("Executing command: %s", cmd)
        tg_port1_vlan = subprocess.check_output(cmd, shell=True)

        cmd = "openstack network show %s | grep segmentation_id | " \
              "cut -d '|' -f 3" % (self.tg_port2_nw)
        LOG.debug("Executing command: %s", cmd)
        tg_port2_vlan = subprocess.check_output(cmd, shell=True)

        additional_params = \
            'TRAFFIC={"traffic_type":"%s", "multistream":%d, ' \
            '"l2":{"srcmac":"{\'%s\',\'%s\'}", "dstmac":"{\'%s\',\'%s\'}"}, ' \
            '"vlan":{"enabled":"True", "id":"{%d,%d}"}}' \
            % (traffic_type, multistream,
               self.moongen_port1_mac, self.moongen_port2_mac,
               self.tgen_port1_mac, self.tgen_port2_mac,
               int(tg_port1_vlan), int(tg_port2_vlan))

        if 'test_params' in options:
            test_params.append(options['test_params'] + additional_params)

        # filter empty parameters and escape quotes and double quotes
        test_params = [tp.replace('"', '\\"').replace("'", "\\'")
                       for tp in test_params if tp]

        # Set password less access to MoonGen
        cmd = "sshpass -p yardstick ssh-copy-id -o StrictHostKeyChecking=no " \
              "root@%s -p 22" % (self.moongen_host_ip)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

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
        result['nrFlows'] = multistream

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

        # execute external setup script
        if self.setup_script:
            cmd = "%s teardown" % (self.setup_script)
            LOG.info("Execute setup script \"%s\"", cmd)
            subprocess.call(cmd, shell=True)

        self.setup_done = False
