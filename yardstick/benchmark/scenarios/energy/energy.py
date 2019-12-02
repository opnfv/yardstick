##############################################################################
# Copyright (c) 2019 Lenovo Group Limited Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import print_function
from __future__ import absolute_import
import logging
import sys
import time
import traceback
import json
import yardstick.ssh as ssh
from yardstick.common import utils
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)
logging.captureWarnings(True)
#requests.packages.urllib3.disable_warnings()


class Energy(base.Scenario):
    """Get current energy consumption of target host

    This scenario sends a REDFISH request to a host BMC
    to request current energy consumption.
    The answers return a number of Watts.
    Usually this is an average of a rolling windows
    taken from server internal sensor.
    This is dependant of the server provider.

    This scenario should be use with node context

    If requests error, energy consumption  will be set to -1

  Parameters
    None
    """

    __scenario_type__ = "Energy"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.target = self.context_cfg['target']
        self.client = ssh.SSH.from_node(self.target, defaults={"root": "passw0rd"})
        self.client.wait(timeout=600)
        self.target_ip = self.target['redfish_ip']
        self.target_user = self.target['redfish_user']
        self.target_pwd = self.target['redfish_pwd']

    def _execute_command(self, cmd):
        """Execute a command on server."""
        LOG.info("Executing: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status != 0:
            raise RuntimeError("Failed executing command: ",
                               cmd, stderr)
        return stdout

    def load_chassis_list(self):
        """Get Chassis List for server Redfish API."""
        chassis_list = []
        # Get Chassis list
        cmd = "curl -k -X GET -H 'Content-Type: application/json'\
        -L -u {}:{} https://{}/redfish/v1/Chassis/"\
        .format(self.target_user, self.target_pwd, self.target_ip)
        # pylint: disable=locally-disabled,broad-except
        chassis_data = json.loads(self._execute_command(cmd))
        for chassis in chassis_data['Members']:
            chassis_list.append(chassis["@odata.id"])
        return chassis_list

    def get_power(self, chassis_uri):
        """Get PowerMetter values from Redfish API."""
        if chassis_uri[-1:] != '/':
            chassis_uri += '/'
        rqt_url = "https://" + self.target_ip
        rqt_url += chassis_uri
        rqt_url += "Power/"
        cmd = "curl -k -X GET -H 'Content-Type: application/json'\
        -L -u {}:{} {}".format(self.target_user, self.target_pwd, rqt_url)
        power_metrics = json.loads(self._execute_command(cmd))
        power = power_metrics["PowerControl"][0]["PowerConsumedWatts"]
        return power

    def run(self, result):
        """execute the benchmark"""
        chassis_list = self.load_chassis_list()
        destination = self.target.get('redfish_ip', '127.0.0.1')
        dest_list = [s.strip() for s in destination.split(',')]
        for pos, dest in enumerate(dest_list):
            for chassis in chassis_list:
                power = self.get_power(chassis)
                data = {
                    "power": power,
                }
                result.update(utils.flatten_dict_key(data))


# def _test():    # pragma: no cover
#     """internal test function"""
#     ctx = {
#         "host": {
#             "ip": "10.240.217.163",
#             "user": "root",
#             "passw0rd": "passw0rd"
#         },
#         "target": {
#             "ipaddr": "10.240.217.181",
#         }
#     }

#     args = {}
#     result = {}
#     p = Energy(args, ctx)
#     p.run(result)
#     print(result)


# if __name__ == '__main__':    # pragma: no cover
#     _test()
