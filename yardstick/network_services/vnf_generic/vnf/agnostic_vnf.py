# Copyright (c) 2018 Intel Corporation
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

import logging

from yardstick.network_services.vnf_generic.vnf import base

LOG = logging.getLogger(__name__)


class AgnosticVnf(base.GenericVNF):
    def __init__(self, name, vnfd, task_id):
        super(AgnosticVnf, self).__init__(name, vnfd, task_id)

    def instantiate(self, scenario_cfg, context_cfg):
        pass

    def wait_for_instantiate(self):
        pass

    def terminate(self):
        pass

    def scale(self, flavor=""):
        pass

    def collect_kpi(self):
        pass

    def start_collect(self):
        pass

    def stop_collect(self):
        pass
