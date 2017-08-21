#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
module: os_stack_facts
short_description: Retrieve facts about an stack within OpenStack.
version_added: "2.0"
author: "Originally: Davide Agnello (@dagnello); modified"
description:
    - Retrieve facts about a stack from OpenStack.
notes:
    - Facts are placed in the C(openstack) variable.
requirements:
    - "python >= 2.6"
    - "shade"
options:
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather facts about a previously created stack named stack1
- os_stack_facts:
    auth:
      auth_url: https://your_api_url.com:9000/v2.0
      username: user
      password: password
      project_name: someproject
- debug: var=openstack_stacks
'''

RETURN = '''
openstack_stack:
    description: has all the openstack facts about the stack
    returned: always, but can be null
    type: complex
'''


def main():

    argument_spec = openstack_full_argument_spec(
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')


    try:
        cloud = shade.openstack_cloud(**module.params)
        stacks = cloud.list_stacks()
        module.exit_json(changed=False, ansible_facts={
            'openstack_stacks': stacks})

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
