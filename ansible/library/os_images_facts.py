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
module: os_images_facts
short_description: Retrieve facts about an image within OpenStack.
version_added: "2.0"
author: "Originally: Davide Agnello (@dagnello); modified"
description:
    - Retrieve facts about a image image from OpenStack.
notes:
    - Facts are placed in the C(openstack) variable.
requirements:
    - "python >= 2.6"
    - "shade"
options:
   image:
     description:
        - Name or ID of the image
     required: false
   filters:
     description:
        - A dictionary of meta data to use for further filtering.  Elements of
          this dictionary may be additional dictionaries.
     required: false
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather facts about a previously created image named image1
- os_images_facts:
    auth:
      auth_url: https://your_api_url.com:9000/v2.0
      username: user
      password: password
      project_name: someproject
    image: image1
- debug: var=openstack
'''

RETURN = '''
openstack_image:
    description: has all the openstack facts about the image
    returned: always, but can be null
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: string
        name:
            description: Name given to the image.
            returned: success
            type: string
        status:
            description: Image status.
            returned: success
            type: string
        created_at:
            description: Image created at timestamp.
            returned: success
            type: string
        deleted:
            description: Image deleted flag.
            returned: success
            type: boolean
        container_format:
            description: Container format of the image.
            returned: success
            type: string
        min_ram:
            description: Min amount of RAM required for this image.
            returned: success
            type: int
        disk_format:
            description: Disk format of the image.
            returned: success
            type: string
        updated_at:
            description: Image updated at timestamp.
            returned: success
            type: string
        properties:
            description: Additional properties associated with the image.
            returned: success
            type: dict
        min_disk:
            description: Min amount of disk space required for this image.
            returned: success
            type: int
        protected:
            description: Image protected flag.
            returned: success
            type: boolean
        checksum:
            description: Checksum for the image.
            returned: success
            type: string
        owner:
            description: Owner for the image.
            returned: success
            type: string
        is_public:
            description: Is public flag of the image.
            returned: success
            type: boolean
        deleted_at:
            description: Image deleted at timestamp.
            returned: success
            type: string
        size:
            description: Size of the image.
            returned: success
            type: int
'''


def main():

    argument_spec = openstack_full_argument_spec(
        image={'required': False, 'default': None},
        filters={'required': False, 'default': None},
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    image = module.params.pop('image')
    filters = module.params.pop('filters')

    try:
        cloud = shade.openstack_cloud(**module.params)
        images = cloud.search_images(image, filters)
        module.exit_json(changed=False, ansible_facts={
            'openstack_images': images})

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
