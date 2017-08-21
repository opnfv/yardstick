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

# yardstick: this file is copied from python-heatclient and slightly modified

from __future__ import absolute_import

import yaml


if hasattr(yaml, 'CSafeLoader'):
    # make a dynamic subclass so we don't override global yaml Loader
    yaml_loader = type('CustomLoader', (yaml.CSafeLoader,), {})
else:
    yaml_loader = type('CustomLoader', (yaml.SafeLoader,), {})

if hasattr(yaml, 'CSafeDumper'):
    yaml_dumper = yaml.CSafeDumper
else:
    yaml_dumper = yaml.SafeDumper


def yaml_load(tmpl_str):
    return yaml.load(tmpl_str, Loader=yaml_loader)
