#!/usr/bin/env python
# Copyright (c) 2017 Intel Corporation
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

DOCUMENTATION = '''
---
module: write_string
short_description: write a string to a file
description:
    - write a string to a file without using temp files
options:
  path: path to write to
  val: string to write
  mode: python file mode (w, wb, a, ab)
'''


def main():
    module = AnsibleModule(
        argument_spec={
            'path': {'required': True, 'type': 'path', 'aliases': ['dest']},
            'fact_name': {'required': True},
        }
    )
    params = module.params
    path = params['path']
    fact_name = params['fact_name']
    with open(path) as file_object:
        script = file_object.read()
    variables = dict(l.split('=') for l in shlex.split(script) if '=' in l)
    module.exit_json(changed=True, ansible_facts={fact_name: variables})


# <<INCLUDE_ANSIBLE_MODULE_COMMON>>
from ansible.module_utils.basic import *  # noqa

if __name__ == '__main__':
    main()
