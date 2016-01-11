#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.networking.iperf3.Iperf

import mock
import unittest

from yardstick.benchmark.scenarios.networking import vtc_throughput


class VtcThroughputTestCase(unittest.TestCase):

    def setUp(self):
        scenario = dict()
        scenario['options'] = dict()
        scenario['options']['default_net_name'] = ''
        scenario['options']['default_subnet_name'] = ''
        scenario['options']['vlan_net_1_name'] = ''
        scenario['options']['vlan_subnet_1_name'] = ''
        scenario['options']['vlan_net_2_name'] = ''
        scenario['options']['vlan_subnet_2_name'] = ''
        scenario['options']['vnic_type'] = ''
        scenario['options']['vtc_flavor'] = ''
        scenario['options']['packet_size'] = ''
        scenario['options']['vlan_sender'] = ''
        scenario['options']['vlan_receiver'] = ''
        scenario['options']['num_of_neighbours'] = '1'
        scenario['options']['amount_of_ram'] = '1G'
        scenario['options']['number_of_cores'] = '1'

        self.vt = vtc_throughput.VtcThroughput(scenario, '')

    def test_run_for_success(self):
        result = {}
        self.vt.run(result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
