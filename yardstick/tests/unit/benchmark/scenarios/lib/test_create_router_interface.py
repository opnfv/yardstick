##############################################################################
# Copyright (c) 2018 Intel.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest
import mock

from yardstick.benchmark.scenarios.lib import create_router_interface
from yardstick.common import exceptions
from yardstick.common import openstack_utils


class CreateRouterInterfaceTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_get_shade_client = mock.patch.object(openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()

        self.addCleanup(self.stop_mocks)

        self.scenario_cfg = {
            "options": {
                "router_id": "my-router-name-or-id",
                "subnet_id": "my-subnet-name-or-id",
                "port_id": "my-port-id"
            }
        }
        context_cfg = {}

        self.scenario = create_router_interface.CreateRouterInterface(
            self.scenario_cfg, context_cfg)

    def stop_mocks(self):
        self._mock_get_shade_client.stop()

    def test__init__(self):

        self.assertEqual(self.scenario_cfg["options"], self.scenario.options)
        self.assertEqual("my-router-name-or-id", self.scenario.router_id)
        self.assertEqual("my-subnet-name-or-id", self.scenario.subnet_id)
        self.assertEqual("my-port-id", self.scenario.port_id)
        self.assertFalse(self.scenario.setup_done)

    def test__init__no_params(self):

        self.assertRaises(KeyError,
                          create_router_interface.CreateRouterInterface,
                          {}, {})

    def test__init__router_id_only(self):
        scenario_cfg = {"options": {"router_id": "my-router-name-or-id"}}
        scenario = create_router_interface.CreateRouterInterface(scenario_cfg, {})

        self.assertEqual(scenario_cfg["options"], scenario.options)
        self.assertEqual("my-router-name-or-id", scenario.router_id)
        self.assertIsNone(scenario.subnet_id)
        self.assertIsNone(scenario.port_id)
        self.assertFalse(scenario.setup_done)

    def test_setup(self):
        self.assertFalse(self.scenario.setup_done)
        self.scenario.setup()
        self.assertTrue(self.scenario.setup_done)

    @mock.patch.object(create_router_interface, 'LOG')
    @mock.patch.object(openstack_utils, 'create_router_interface')
    def test_run(self, mock_create_router_interface, mock_log):
        mock_create_router_interface.return_value = "some-interface-id"

        result = {}
        self.scenario.run(result)

        self.assertEqual({"create_router_interface": 1}, result)
        mock_log.info.assert_called_once()


    @mock.patch.object(openstack_utils, 'create_router_interface')
    def test_run_error(self, mock_create_router_interface):
        mock_create_router_interface.return_value = None
        result = {}
        self.assertRaises(exceptions.ScenarioCreateRouterIntError,
                          self.scenario.run,
                          result)
        self.assertEqual({"create_router_interface": 0}, result)

    @mock.patch.object(openstack_utils, 'create_router_interface')
    def test_run_outputs_requested(self, mock_create_router_interface):
        scenario_cfg = {
            "options": {
                "router_id": "my-router-name-or-id",
                "subnet_id": "my-subnet-name-or-id",
                "port_id": "my-port-id"
            },
            "output": "interface_id",
        }
        result = {}
        mock_create_router_interface.return_value = "my-interface_id"

        scenario = create_router_interface.CreateRouterInterface(scenario_cfg, {})
        output = scenario.run(result)
        self.assertEqual({"interface_id": "my-interface_id"}, output)
        self.assertEqual({"create_router_interface": 1}, result)

    @mock.patch.object(openstack_utils, 'create_router_interface')
    def test_run_wrong_outputs_requested(self, mock_create_router_interface):
        # incorrect outputs requested
        scenario_cfg = {
            "options": {
                "router_id": "my-router-name-or-id",
                "subnet_id": "my-subnet-name-or-id",
                "port_id": "my-port-id"
            },
            "output": "interface_id other_output",
        }
        result = {}
        mock_create_router_interface.return_value = "my-interface_id"

        scenario = create_router_interface.CreateRouterInterface(scenario_cfg, {})
        output = scenario.run(result)
        self.assertEqual({"interface_id": "my-interface_id"}, output)
        self.assertEqual({"create_router_interface": 1}, result)
