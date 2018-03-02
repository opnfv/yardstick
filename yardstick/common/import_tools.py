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

import sys

from yardstick.common import exceptions


BANNED_MODULES = {'ansible': 'Module with GPLv3 license'}


def decorator_banned_modules(cls):
    def _class(*args, **kwargs):
        for module in sys.modules:
            for banned_module, reason in BANNED_MODULES.items():
                if module.startswith(banned_module):
                    raise exceptions.YardstickBannedModuleImported(
                        module=banned_module, reason=reason)
        return cls(*args, **kwargs)
    return _class
