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


class CreateServer(base.Scenario):
    """Create an OpenStack server"""

    __scenario_type__ = "CreateServer"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]

        self.name = self.options["name"]
        self.image = self.options["image"]
        self.flavor = self.options["flavor"]
        self.auto_ip = self.options.get("auto_ip", True)
        self.ips = self.options.get("ips")
        self.ip_pool = self.options.get("ip_pool")
        self.root_volume = self.options.get("root_volume")
        self.terminate_volume = self.options.get("terminate_volume", False)
        self.wait = self.options.get("wait", True)
        self.timeout = self.options.get("timeout", 180)
        self.reuse_ips = self.options.get("reuse_ips", True)
        self.network = self.options.get("network")
        self.boot_from_volume = self.options.get("boot_from_volume", False)
        self.volume_size = self.options.get("volume_size", '20')
        self.boot_volume = self.options.get("boot_volume")
        self.volumes = self.options.get("volumes")
        self.nat_destination = self.options.get("nat_destination")

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        server = openstack_utils.create_instance_and_wait_for_active(
            self.shade_client, self.name, self.image,
            self.flavor, auto_ip=self.auto_ip, ips=self.ips,
            ip_pool=self.ip_pool, root_volume=self.root_volume,
            terminate_volume=self.terminate_volume, wait=self.wait,
            timeout=self.timeout, reuse_ips=self.reuse_ips,
            network=self.network, boot_from_volume=self.boot_from_volume,
            volume_size=self.volume_size, boot_volume=self.boot_volume,
            volumes=self.volumes, nat_destination=self.nat_destination)

        if not server:
            result.update({"instance_create": 0})
            LOG.error("Create server failed!")
            raise exceptions.ScenarioCreateServerError

        result.update({"instance_create": 1})
        LOG.info("Create instance successful!")
        keys = self.scenario_cfg.get("output", '').split()
        server_id = server["id"]
        values = [server_id]
        return self._push_to_outputs(keys, values)
