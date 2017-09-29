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
module: shade_api
short_description: directly access shade
description:
    - directly access shade API
options:
  method: shade method
  args: list of ags
  kwargs: dict of kwargs
  fact_name: name of ansible fact to store result
'''

try:
    import shade
except ImportError:
    SHADE_PRESENT = False
else:
    SHADE_PRESENT = True


def main():
    module = AnsibleModule(
        argument_spec={
            'method': {'required': True, 'type': 'str'},
            'args': {'required': False, 'type': 'list', 'default': []},
            'kwargs': {'required': False, 'type': 'dict', 'default': {}},
            'os_auth': {'required': False, 'type': 'dict', 'default': {}},
            'fact_name': {'required': True, 'type': 'str'},
        }
    )

    if not SHADE_PRESENT:
        module.fail_json(msg="shade not found")
    shade.simple_logging(debug=True)
    params = module.params
    method = params['method']
    args = params['args']
    kwargs = params['kwargs']
    os_auth = params['os_auth']
    fact_name = params['fact_name']
    if os_auth:
        os.environ.update(os_auth)

    c = shade.openstack_cloud()
    module.debug(args)
    module.debug(kwargs)
    ret = getattr(c, method)(*args, **kwargs)
    if ret:
        try:
            # convert to regular dict, might not be necessary
            ret = ret.toDict()
        except AttributeError:
            pass
    else:
        ret = {}
    ansible_facts = {
        fact_name: ret
    }
    module.exit_json(ansible_facts=ansible_facts)


# <<INCLUDE_ANSIBLE_MODULE_COMMON>>
from ansible.module_utils.basic import *  # noqa

if __name__ == '__main__':
    main()
