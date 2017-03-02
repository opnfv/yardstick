##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import logging
import re

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base
from six.moves import zip

LOG = logging.getLogger(__name__)


class NetUtilization(base.Scenario):
    """Collect network utilization statistics.

    This scenario reads statistics from the network devices on a Linux host.
    Network utilization statistics are read using the utility 'sar'.

    The following values are displayed:

    IFACE: Name of the network interface for which statistics are reported.

    rxpck/s: Total number of packets received per second.

    txpck/s: Total number of packets transmitted per second.

    rxkB/s: Total number of kilobytes received per second.

    txkB/s: Total number of kilobytes transmitted per second.

    rxcmp/s: Number of compressed packets received per second (for cslip etc.).

    txcmp/s: Number of compressed packets transmitted per second.

    rxmcst/s: Number of multicast packets received per second.

    %ifutil: Utilization percentage of the network interface. For half-duplex
    interfaces, utilization is calculated using the sum of rxkB/s and txkB/s
    as a percentage of the interface speed. For full-duplex, this is the
    greater  of rxkB/S or txkB/s.

    Parameters
        interval - Time interval to measure network utilization.
            type:       [int]
            unit:       seconds
            default:    1

        count - Number of times to measure network utilization.
            type:       [int]
            unit:       N/A
            default:    1
    """

    __scenario_type__ = "NetUtilization"

    NET_UTILIZATION_FIELD_SIZE = 8

    def __init__(self, scenario_cfg, context_cfg):
        """Scenario construction."""
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """Scenario setup."""
        host = self.context_cfg['host']

        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        self.setup_done = True

    def _execute_command(self, cmd):
        """Execute a command on target."""
        LOG.info("Executing: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError("Failed executing command: ",
                               cmd, stderr)
        return stdout

    def _filtrate_result(self, raw_result):
        """Filtrate network utilization statistics."""
        fields = []
        maximum = {}
        minimum = {}
        average = {}

        time_marker = re.compile("^([0-9]+):([0-9]+):([0-9]+)$")

        # Parse network utilization stats
        for row in raw_result.splitlines():
            line = row.split()

            if line and re.match(time_marker, line[0]):

                try:
                    index = line.index('IFACE')
                except ValueError:
                    del line[:index]
                    net_interface = line[0]
                    values = line[1:]

                    if values and len(values) == len(fields):
                        temp_dict = dict(zip(fields, values))
                        if net_interface not in maximum:
                            maximum[net_interface] = temp_dict
                        else:
                            for item in temp_dict:
                                if float(maximum[net_interface][item]) <\
                                   float(temp_dict[item]):
                                    maximum[net_interface][item] = \
                                        temp_dict[item]

                        if net_interface not in minimum:
                            minimum[net_interface] = temp_dict
                        else:
                            for item in temp_dict:
                                if float(minimum[net_interface][item]) >\
                                   float(temp_dict[item]):
                                    minimum[net_interface][item] = \
                                        temp_dict[item]
                    else:
                        raise RuntimeError("network_utilization: parse error",
                                           fields, line)
                else:
                    del line[:index]
                    fields = line[1:]
                    if len(fields) != NetUtilization.\
                            NET_UTILIZATION_FIELD_SIZE:
                        raise RuntimeError("network_utilization: unexpected\
                                           field size", fields)

            elif line and line[0] == 'Average:':
                del line[:1]

                if line[0] == 'IFACE':
                    # header fields
                    fields = line[1:]
                    if len(fields) != NetUtilization.\
                            NET_UTILIZATION_FIELD_SIZE:
                        raise RuntimeError("network_utilization average: \
                                           unexpected field size", fields)
                else:
                    # value fields
                    net_interface = line[0]
                    values = line[1:]
                    if values and len(values) == len(fields):
                        average[net_interface] = dict(
                            zip(fields, values))
                    else:
                        raise RuntimeError("network_utilization average: \
                                           parse error", fields, line)

        return {'network_utilization_maximun': maximum,
                'network_utilization_minimum': minimum,
                'network_utilization_average': average}

    def _get_network_utilization(self):
        """Get network utilization statistics using sar."""
        options = self.scenario_cfg["options"]
        interval = options.get('interval', 1)
        count = options.get('count', 1)

        cmd = "sudo sar -n DEV %d %d" % (interval, count)

        raw_result = self._execute_command(cmd)
        result = self._filtrate_result(raw_result)

        return result

    def run(self, result):
        """Read statistics."""
        if not self.setup_done:
            self.setup()

        result.update(self._get_network_utilization())
