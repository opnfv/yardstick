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

from __future__ import absolute_import
import logging

log = logging.getLogger(__name__)


class IxConfig:
    def _get_config(self, tg_cfg):
        external_interface = tg_cfg["vdu"][0]["external-interface"]
        card0 = external_interface[0]["virtual-interface"]["vpci"]
        card1 = external_interface[1]["virtual-interface"]["vpci"]
        _cfg = {'py_lib_path':
                tg_cfg["mgmt-interface"]["tg-config"]["py_lib_path"],
                'machine': tg_cfg["mgmt-interface"]["ip"],
                'port': tg_cfg["mgmt-interface"]["tg-config"]["tcl_port"],
                'chassis': tg_cfg["mgmt-interface"]["tg-config"]["ixchassis"],
                'card1': card0.split(":")[0],
                'port1': card0.split(":")[1],
                'card2': card1.split(":")[0],
                'port2': card1.split(":")[1],
                'output_dir':
                tg_cfg["mgmt-interface"]["tg-config"]["dut_result_dir"],
                'version': tg_cfg["mgmt-interface"]["tg-config"]["version"],
                'bidir': True}
        return _cfg
