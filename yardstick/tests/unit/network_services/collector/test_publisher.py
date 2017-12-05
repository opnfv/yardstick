#!/usr/bin/env python

# Copyright (c) 2016-2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Unittest for yardstick.network_services.collector.publisher

from __future__ import absolute_import
import unittest

from yardstick.network_services.collector import publisher


class PublisherTestCase(unittest.TestCase):

    def setUp(self):
        self.test_publisher = publisher.Publisher()

    def test_successful_init(self):
        pass

    def test_unsuccessful_init(self):
        pass

    def test_start(self):
        self.assertIsNone(self.test_publisher.start())

    def test_stop(self):
        self.assertIsNone(self.test_publisher.stop())
