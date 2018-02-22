# Copyright 2017 Intel Corporation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import fixtures
import mock
import six

from yardstick.common import task_template


class PluginParserFixture(fixtures.Fixture):
    """PluginParser fixture.

    This class is intended to be used as a fixture within unit tests and
    therefore consumers must register it using useFixture() within their
    unit test class.
    """

    def __init__(self, rendered_plugin):
        super(PluginParserFixture, self).__init__()
        self._rendered_plugin = rendered_plugin

    def _setUp(self):
        self.addCleanup(self._restore)
        self._mock_tasktemplate_render = mock.patch.object(
            task_template.TaskTemplate, 'render')
        self.mock_tasktemplate_render = self._mock_tasktemplate_render.start()
        self.mock_tasktemplate_render.return_value = self._rendered_plugin
        self._mock_open = mock.patch.object(six.moves.builtins, 'open', create=True)
        self.mock_open = self._mock_open.start()
        self.mock_open.side_effect = mock.mock_open()

    def _restore(self):
        self._mock_tasktemplate_render.stop()
        self._mock_open.stop()
