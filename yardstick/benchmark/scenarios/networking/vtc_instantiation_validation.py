#############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
import logging
import os

from yardstick.benchmark.scenarios import base
import experimental_framework.api as api

LOG = logging.getLogger(__name__)


class VtcInstantiationValidation(base.Scenario):
    """Execute Instantiation Validation TC on the vTC
    """
    __scenario_type__ = "vtc_instantiation_validation"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = None
        self.setup_done = False

    def setup(self):
        '''scenario setup'''

        self.options = self.scenario_cfg['options']
        self.setup_done = True

    def run(self, result):
        """execute test"""

        if not self.setup_done:
            self.setup()

        heat_template = 'vTC.yaml'
        iterations = 1

        openstack_credentials = {
            'ip_controller': '0.0.0.0',
            'heat_url': '***',
            'auth_uri': os.environ.get('OS_AUTH_URL'),
            'user': os.environ.get('OS_USERNAME'),
            'password': os.environ.get('OS_PASSWORD'),
            'project': os.environ.get('OS_TENANT_NAME')
        }
        heat_template_parameters = {
            'default_net': self.options['default_net_name'],
            'default_subnet': self.options['default_subnet_name'],
            'source_net': self.options['vlan_net_1_name'],
            'source_subnet': self.options['vlan_subnet_1_name'],
            'destination_net': self.options['vlan_net_2_name'],
            'destination_subnet': self.options['vlan_subnet_2_name']
        }
        deployment_configuration = {
            'vnic_type': [self.options['vnic_type']],
            'vtc_flavor': [self.options['vtc_flavor']]
        }

        test_case = dict()
        test_case['name'] = 'instantiation_validation_benchmark.' \
                            'InstantiationValidationBenchmark'
        test_case['params'] = dict()
        test_case['params']['throughput'] = '1'
        test_case['params']['vlan_sender'] = str(self.options['vlan_sender'])
        test_case['params']['vlan_receiver'] = \
            str(self.options['vlan_receiver'])

        res = dict()
        try:
            res = api.FrameworkApi.execute_framework(
                [test_case],
                iterations,
                heat_template,
                heat_template_parameters,
                deployment_configuration,
                openstack_credentials)
        except Exception:
            LOG.exception('Exception')
        LOG.info('Got output: %s', res)
        result.update(res)
