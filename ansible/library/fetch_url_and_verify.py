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
module: fetch_url_and_verify
short_description: Fetch image and verify against a SHA256SUM URL
description:
    - Download a URL and check it against a remote SHA256SUMS file
options:
  url: Image URL
  image_dest: Image filename
  sha256_url: SHA256SUMS URL
  dest: python file mode (w, wb, a, ab)
  retries: fetch retries
'''


def main():
    module = AnsibleModule(
        argument_spec={
            'url': {'required': True, 'type': 'str'},
            'sha256url': {'required': True, 'type': 'str'},
            'dest': {'required': True, 'type': 'path'},
            'retries': {'required': False, 'type': 'int', 'default': 3},
        }
    )
    params = module.params
    url = params['url']
    dest = params['dest']
    sha256url = params['sha256url']
    retries = params['retries']

    image_dir, image_filename = os.path.split(dest)
    rc, stdout, stderr = module.run_command(['curl', '-sS', sha256url])
    if rc == 0 and stdout:
        sha256line = next(
            (l for l in stdout.splitlines() if image_filename in l), "")
    if not sha256line:
        module.fail_json(
            msg="Unable to find SHA256SUMS line for file {}".format(
                image_filename))
    rc = \
    module.run_command(['sha256sum', '-c'], data=sha256line, cwd=image_dir)[0]
    if rc == 0:
        sha256sum = sha256line.split()[0]
        module.exit_json(changed=False, dest=dest, url=url,
                         sha256sum=sha256sum)

    for retry in range(retries):
        curl_rc, stdout, stderr = module.run_command(
            ['curl', '-sS', '-o', dest, url], cwd=image_dir)
        if curl_rc == 0:
            sha256_rc, stdout, stderr = module.run_command(['sha256sum', '-c'],
                                                           data=sha256line,
                                                           cwd=image_dir)
            if sha256_rc == 0:
                module.exit_json(changed=True)

    module.fail_json(msg="Unable to download {}".format(url), stdout=stdout,
                     stderr=stderr)


# <<INCLUDE_ANSIBLE_MODULE_COMMON>>
from ansible.module_utils.basic import *  # noqa

if __name__ == '__main__':
    main()
