#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.common.openstack_utils

from __future__ import absolute_import
import unittest
import mock

from yardstick.common import openstack_utils


class GetCredentialsTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.os')
    def test_get_credentials(self, mock_os):
        mock_os.getenv.return_value = ('2')
        openstack_utils.get_credentials()


class GetHeatApiVersionTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.os')
    def test_get_heat_api_version(self, mock_os):
        API = 'HEAT_API_VERSION'
        openstack_utils.get_heat_api_version()
        mock_os.getenv.assert_called_with(API)

    @mock.patch('yardstick.common.openstack_utils.os')
    def test_get_heat_api_version(self, mock_os):
        mock_os.getenv.return_value = ('2')
        expected_result = '2'
        api_version = openstack_utils.get_heat_api_version()
        self.assertEqual(api_version, expected_result)
