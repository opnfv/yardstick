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
import requests
import time
import json
import yardstick.ssh as ssh
from yardstick.common import utils
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)
logging.captureWarnings(True)


class Energy(base.Scenario):
    """Get current energy consumption of target host

    This scenario sends a REDFISH request to a host BMC
    to request current energy consumption.
    The response returns a number of Watts.
    Usually this is an average of a rolling windows
    taken from server internal sensor.
    This is dependant of the server provider.

    This scenario should be used with node context

    As this scenario usually run background with other scenarios,
    error of api query or data parse will not terminate task runner.
    If any error occured, energy consumption will be set to -1.

    Parameters
        None
    """

    __scenario_type__ = "Energy"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.target = self.context_cfg['target']
        self.setup_done = False
        self.get_response = False

    def _send_request(self, url):
        LOG.info("Send request to {}".format(url))
        pod_auth = (self.target["redfish_user"], self.target["redfish_pwd"])
        response = requests.get(url, auth=pod_auth, verify=False)
        return response

    def setup(self):
        url = "https://{}/redfish/v1/".format(self.target["redfish_ip"])
        response = self._send_request(url)
        if response.status_code != 200:
            LOG.info("Don't get right response from {}".format(url))
            self.get_response = False
        else:
            LOG.info("Get response from {}".format(url))
            self.get_response = True

        self.setup_done = True

    def load_chassis_list(self):
        chassis_list = []

        # Get Chassis list
        request_url = "https://" + self.target["redfish_ip"]
        request_url += "/redfish/v1/Chassis/"
        response = self._send_request(request_url)
        if response.status_code != 200:
            LOG.info("Do not get proper response from {}".format(request_url))
            return chassis_list

        try:
            chassis_data = json.loads(response.text)
        except(TypeError, ValueError) as e:
            LOG.info("Invalid response data, {}".format(e))
            return chassis_list

        try:
            for chassis in chassis_data['Members']:
                chassis_list.append(chassis["@odata.id"])
        except KeyError as e:
            LOG.info("Error data format of chassis data or invalid key.")

        return chassis_list

    def get_power(self, chassis_uri):
        """Get PowerMetter values from Redfish API."""
        if chassis_uri[-1:] != '/':
            chassis_uri += '/'
        request_url = "https://" + self.target['redfish_ip']
        request_url += chassis_uri
        request_url += "Power/"
        response = self._send_request(request_url)
        if response.status_code != 200:
            LOG.info("Do not get proper response from {}".format(request_url))
            power = -1
            return power

        try:
            power_metrics = json.loads(response.text)
        except(TypeError, ValueError) as e:
            LOG.info("Invalid response data, {}".format(e))
            power = -1
            return power

        try:
            power = power_metrics["PowerControl"][0]["PowerConsumedWatts"]
        except KeyError as e:
            LOG.info("Error data format of power metrics or invalid key.")
            power = -1

        return power

    def run(self, result):
        """execute the benchmark"""
        if not self.setup_done:
            self.setup()
        chassis_list = self.load_chassis_list()
        destination = self.target.get('redfish_ip', '127.0.0.1')
        dest_list = [s.strip() for s in destination.split(',')]
        if not self.get_response or not chassis_list:
            for pos, dest in enumerate(dest_list):
                power = -1
                data = {
                    "power": power,
                }
                result.update(data)
        else:
            for pos, dest in enumerate(dest_list):
                for chassis in chassis_list:
                    power = self.get_power(chassis)
                    data = {
                        "power": power,
                    }
                result.update(data)
