#!/usr/bin/python

# Copyright (c) 2016 IBM
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
module: os_router_facts
short_description: Retrieve facts about routers within OpenStack.
version_added: "2.1"
author: "Originally: David Shrewsbury (@Shrews); modified"
description:
    - Retrieve facts about routers from OpenStack.
notes:
    - Facts are placed in the C(openstack_routers) variable.
requirements:
    - "python >= 2.6"
    - "shade"
options:
    port:
        description:
            - Unique name or ID of a port.
        required: false
        default: null
    filters:
        description:
            - A dictionary of meta data to use for further filtering. Elements
              of this dictionary will be matched against the returned port
              dictionaries. Matching is currently limited to strings within
              the port dictionary, or strings within nested dictionaries.
        required: false
        default: null
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather facts about all routers
- os_router_facts:
    cloud: mycloud

# Gather facts about a single port
- os_router_facts:
    cloud: mycloud
    port: 6140317d-e676-31e1-8a4a-b1913814a471

# Gather facts about all routers that have device_id set to a specific value
# and with a status of ACTIVE.
- os_router_facts:
    cloud: mycloud
   router:
     description:
        - Name or ID of the router
     required: false
    filters:
      device_id: 1038a010-3a37-4a9d-82ea-652f1da36597
      status: ACTIVE
'''

RETURN = '''
openstack_routers:
    description: List of port dictionaries. A subset of the dictionary keys
                 listed below may be returned, depending on your cloud provider.
    returned: always, but can be null
    type: complex
    contains:
'''


def main():
    argument_spec = openstack_full_argument_spec(
        router={'required': False, 'default': None},
        filters={'required': False, 'type': 'dict', 'default': None},
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    router = module.params.pop('router')
    filters = module.params.pop('filters')

    try:
        cloud = shade.openstack_cloud(**module.params)
        routers = cloud.search_routers(router, filters)
        module.exit_json(changed=False, ansible_facts=dict(
            openstack_routers=routers))

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
