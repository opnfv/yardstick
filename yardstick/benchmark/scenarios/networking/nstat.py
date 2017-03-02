##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import print_function
from __future__ import absolute_import

import time
import logging

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)

PRECISION = 3


class Nstat(base.Scenario):
    """Use nstat to monitor network metrics and measure IP datagram error rate
    and etc.
    """

    __scenario_type__ = "Nstat"

    def __init__(self, scenario_cfg, context_cfg):
        """Scenario construction"""
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        host = self.context_cfg["host"]

        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        self.setup_done = True

    def match(self, key, field, line, results):
        """match data in the output"""
        if key in line:
            results[key] = int(line.split()[field])

    def calculate_error_rate(self, x, y):
        """calculate error rate"""
        try:
            return round(float(x) / float(y), PRECISION)
        except ZeroDivisionError:
            # If incoming Errors is non-zero, but incoming data is zero
            # consider it as 100% error rate
            if x:
                return 1
            else:
                return 0

    def process_output(self, out):
        """process output"""
        results = {}
        for line in out.splitlines():
            self.match('IpInReceives', 1, line, results)
            self.match('IpInHdrErrors', 1, line, results)
            self.match('IpInAddrErrors', 1, line, results)
            self.match('IcmpInMsgs', 1, line, results)
            self.match('IcmpInErrors', 1, line, results)
            self.match('TcpInSegs', 1, line, results)
            self.match('TcpInErrs', 1, line, results)
            self.match('UdpInDatagrams', 1, line, results)
            self.match('UdpInErrors', 1, line, results)
        results['IpErrors'] = \
            results['IpInHdrErrors'] + results['IpInAddrErrors']
        results['IP_datagram_error_rate'] = \
            self.calculate_error_rate(results['IpErrors'],
                                      results['IpInReceives'])
        results['Icmp_message_error_rate'] = \
            self.calculate_error_rate(results['IcmpInErrors'],
                                      results['IcmpInMsgs'])
        results['Tcp_segment_error_rate'] = \
            self.calculate_error_rate(results['TcpInErrs'],
                                      results['TcpInSegs'])
        results['Udp_datagram_error_rate'] = \
            self.calculate_error_rate(results['UdpInErrors'],
                                      results['UdpInDatagrams'])
        return results

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg['options']
        duration = options.get('duration', 60)

        time.sleep(duration)

        cmd = "nstat -z"

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        results = self.process_output(stdout)

        result.update(results)

        if "sla" in self.scenario_cfg:
            sla_error = ""
            for i, rate in result.items():
                if i not in self.scenario_cfg['sla']:
                    continue
                sla_rate = float(self.scenario_cfg['sla'][i])
                rate = float(rate)
                if rate > sla_rate:
                    sla_error += "%s rate %f > sla:%s_rate(%f); " % \
                        (i, rate, i, sla_rate)
            assert sla_error == "", sla_error
