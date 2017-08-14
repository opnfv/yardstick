#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Linus Unnebäck <linus@folkdatorn.se>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
DOCUMENTATION = '''
---
module: my_make
short_description: Run targets in a Makefile
requirements: [ make ]
version_added: "2.1"
author: Linus Unnebäck (@LinusU) <linus@folkdatorn.se>
description:
  - Run targets in a Makefile.
options:
  target:
    description:
      - The target to run
    required: false
    default: none
  params:
    description:
      - Any extra parameters to pass to make
    required: false
    default: none
  extra_args:
    description:
      - Any extra options to pass to make
    required: false
    default: none
  chdir:
    description:
      - cd into this directory before running make
    required: true
'''

EXAMPLES = '''
# Build the default target
- make: chdir=/home/ubuntu/cool-project

# Run `install` target as root
- make: chdir=/home/ubuntu/cool-project target=install
  become: yes

# Pass in extra arguments to build
- make:
    chdir: /home/ubuntu/cool-project
    target: all
    params:
      NUM_THREADS: 4
      BACKEND: lapack
'''

# TODO: Disabled the RETURN as it was breaking docs building. Someone needs to
# fix this
RETURN = '''# '''


def format_params(params):
    return [k + '=' + str(v) for k, v in params.items()]


def push_arguments(cmd, args):
    if args['extra_args'] is not None:
        cmd.extend(shlex.split(args['extra_args']))
    if args['target'] is not None:
        cmd.append(args['target'])
    if args['params'] is not None:
        cmd.extend(format_params(args['params']))
    return cmd


def check_changed(make_path, module, args):
    cmd = push_arguments([make_path, '--question'], args)
    rc, _, __ = module.run_command(cmd, check_rc=False, cwd=args['chdir'])
    return rc != 0


def run_make(make_path, module, args):
    cmd = push_arguments([make_path], args)
    module.run_command(cmd, check_rc=True, cwd=args['chdir'])


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            target=dict(required=False, default=None, type='str'),
            params=dict(required=False, default=None, type='dict'),
            extra_args=dict(required=False, default=None, type='str'),
            chdir=dict(required=True, default=None, type='str'),
        ),
    )
    args = dict(
        changed=False,
        failed=False,
        target=module.params['target'],
        params=module.params['params'],
        extra_args=module.params['extra_args'],
        chdir=module.params['chdir'],
    )
    make_path = module.get_bin_path('make', True)

    # Check if target is up to date
    args['changed'] = check_changed(make_path, module, args)

    # Check only; don't modify
    if module.check_mode:
        module.exit_json(changed=args['changed'])

    # Target is already up to date
    if not args['changed']:
        module.exit_json(**args)

    run_make(make_path, module, args)
    module.exit_json(**args)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
