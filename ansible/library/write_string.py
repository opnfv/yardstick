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
            'val': {'required': True, 'type': 'str'},
            'mode': {'required': False, 'default': "w", 'type': 'str',
                     'choices': ['w', 'wb', 'a', 'ab']}}
    )
    params = module.params
    path = params['path']
    mode = params['mode']
    val = params['val']
    with open(path, mode) as file_object:
        file_object.write(val)

    module.exit_json(changed=True)


# <<INCLUDE_ANSIBLE_MODULE_COMMON>>
from ansible.module_utils.basic import *  # noqa

if __name__ == '__main__':
    main()
