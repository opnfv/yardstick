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
---
module: my_os_network_facts
short_description: Retrieve facts about one or more OpenStack networks.
version_added: "2.0"
author: "Davide Agnello (@dagnello)"
description:
    - Retrieve facts about one or more networks from OpenStack.
requirements:
    - "python >= 2.6"
    - "shade"
options:
   network:
     description:
        - Name or ID of the Network
     required: false
   filters:
     description:
        - A dictionary of meta data to use for further filtering.  Elements of
          this dictionary may be additional dictionaries.
     required: false
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather facts about previously created networks
- my_os_network_facts:
    auth:
      auth_url: https://your_api_url.com:9000/v2.0
      username: user
      password: password
      project_name: someproject
- debug: var=openstack_networks

# Gather facts about a previously created network by name
- my_os_network_facts:
    auth:
      auth_url: https://your_api_url.com:9000/v2.0
      username: user
      password: password
      project_name: someproject
    name:  network1
- debug: var=openstack_networks

# Gather facts about a previously created network with filter (note: name and
  filters parameters are Not mutually exclusive)
- my_os_network_facts:
    auth:
      auth_url: https://your_api_url.com:9000/v2.0
      username: user
      password: password
      project_name: someproject
    filters:
      tenant_id: 55e2ce24b2a245b09f181bf025724cbe
      subnets:
        - 057d4bdf-6d4d-4728-bb0f-5ac45a6f7400
        - 443d4dc0-91d4-4998-b21c-357d10433483
- debug: var=openstack_networks
'''

RETURN = '''
openstack_networks:
    description: has all the openstack facts about the networks
    returned: always, but can be null
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: string
        name:
            description: Name given to the network.
            returned: success
            type: string
        status:
            description: Network status.
            returned: success
            type: string
        subnets:
            description: Subnet(s) included in this network.
            returned: success
            type: list of strings
        tenant_id:
            description: Tenant id associated with this network.
            returned: success
            type: string
        shared:
            description: Network shared flag.
            returned: success
            type: boolean
'''

def main():

    argument_spec = openstack_full_argument_spec(
        network={'required': False, 'default': None},
        filters={'required': False, 'default': None}
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    network = module.params.pop('network')
    filters = module.params.pop('filters')

    try:
        cloud = shade.openstack_cloud(**module.params)
        networks = cloud.search_networks(network, filters)
        module.exit_json(changed=False, ansible_facts={
            'openstack_networks': networks})

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
