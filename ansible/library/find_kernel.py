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

import os

DOCUMENTATION = '''
---
module: find_kernel
short_description: Look for the system kernel on the filesystem
description:
    - We need to find the kernel on non-booted systems, disk images, chroots, etc.
    To do this we check /lib/modules and look for the kernel that matches the running
    kernle, or failing that we look for the highest-numbered kernel
options:
  kernel: starting kernel to check
  module_dir: Override kernel module dir, default /lib/modules
'''

LIB_MODULES = "/lib/modules"


def try_int(s, *args):
    """Convert to integer if possible."""
    try:
        return int(s)
    except (TypeError, ValueError):
        return args[0] if args else s


def convert_ints(fields, orig):
    return tuple((try_int(f) for f in fields)), orig


def main():
    module = AnsibleModule(
        argument_spec={
            'kernel': {'required': True, 'type': 'str'},
            'module_dir': {'required': False, 'type': 'str', 'default': LIB_MODULES},
        }
    )
    params = module.params
    kernel = params['kernel']
    module_dir = params['module_dir']

    if os.path.isdir(os.path.join(module_dir, kernel)):
        module.exit_json(changed=False, kernel=kernel)

    kernel_dirs = os.listdir(module_dir)
    kernels = sorted((convert_ints(re.split('[-.]', k), k) for k in kernel_dirs), reverse=True)
    try:
        newest_kernel = kernels[0][-1]
    except IndexError:
        module.fail_json(msg="Unable to find kernels in {}".format(module_dir))

    if os.path.isdir(os.path.join(module_dir, newest_kernel)):
        module.exit_json(changed=False, kernel=newest_kernel)
    else:
        return kernel

    module.fail_json(msg="Unable to kernel other than {}".format(kernel))


# <<INCLUDE_ANSIBLE_MODULE_COMMON>>
from ansible.module_utils.basic import *  # noqa

if __name__ == '__main__':
    main()

"""

get kernel from uname,  ansible_kernel
look for that kernel in /lib/modules
if that kernel doens't exist
sort lib/modules
use latest

parse grub



"""
