##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import logging

from yardstick.benchmark.scenarios import base
from yardstick.common import openstack_utils
from yardstick.common import exceptions


LOG = logging.getLogger(__name__)


class CreateSubnet(base.Scenario):
    """Create an OpenStack flavor"""

    __scenario_type__ = "CreateSubnet"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.network_name_or_id = self.options['network_name_or_id']
        self.cidr = self.options.get('cidr')
        self.ip_version = self.options.get('ip_version', 4)
        self.enable_dhcp = self.options.get('enable_dhcp', False)
        self.subnet_name = self.options.get('subnet_name')
        self.tenant_id = self.options.get('tenant_id')
        self.allocation_pools = self.options.get('allocation_pools')
        self.gateway_ip = self.options.get('gateway_ip')
        self.disable_gateway_ip = self.options.get('disable_gateway_ip', False)
        self.dns_nameservers = self.options.get('dns_nameservers')
        self.host_routes = self.options.get('host_routes')
        self.ipv6_ra_mode = self.options.get('ipv6_ra_mode')
        self.ipv6_address_mode = self.options.get('ipv6_address_mode')
        self.use_default_subnetpool = self.options.get(
            'use_default_subnetpool', False)

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        subnet_id = openstack_utils.create_neutron_subnet(
            self.shade_client, self.network_name_or_id, cidr=self.cidr,
            ip_version=self.ip_version, enable_dhcp=self.enable_dhcp,
            subnet_name=self.subnet_name, tenant_id=self.tenant_id,
            allocation_pools=self.allocation_pools, gateway_ip=self.gateway_ip,
            disable_gateway_ip=self.disable_gateway_ip,
            dns_nameservers=self.dns_nameservers, host_routes=self.host_routes,
            ipv6_ra_mode=self.ipv6_ra_mode,
            ipv6_address_mode=self.ipv6_address_mode,
            use_default_subnetpool=self.use_default_subnetpool)
        if not subnet_id:
            result.update({"subnet_create": 0})
            LOG.error("Create subnet failed!")
            raise exceptions.ScenarioCreateSubnetError

        result.update({"subnet_create": 1})
        LOG.info("Create subnet successful!")
        keys = self.scenario_cfg.get('output', '').split()
        values = [subnet_id]
        return self._push_to_outputs(keys, values)
