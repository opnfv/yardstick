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

import argparse
import collections
import os
from packaging import version as pkg_version
import sys

from openstack_requirements import requirement


PROJECT_REQUIREMENTS_FILES = ['requirements.txt']
QUALIFIER_CHARS = ['<', '>', '!', '=']


def _grab_args():
    """Grab and return arguments"""
    parser = argparse.ArgumentParser(
        description='Check if project requirements have changed')

    parser.add_argument('env_dir', help='tox environment directory')
    return parser.parse_args()


def _extract_reqs(file_name, blacklist=None):
    blacklist = blacklist or {}
    content = open(file_name, 'rt').read()
    reqs = collections.defaultdict(tuple)
    parsed = requirement.parse(content)
    for name, entries in ((name, entries) for (name, entries) in parsed.items()
                          if (name and name not in blacklist)):
        list_reqs = [r for (r, line) in entries]
        # Strip the comments out before checking if there are duplicates
        list_reqs_stripped = [r._replace(comment='') for r in list_reqs]
        if len(list_reqs_stripped) != len(set(list_reqs_stripped)):
            print('Requirements file %s has duplicate entries for package '
                  '"%s: %r' % (file_name, name, list_reqs))
        reqs[name] = list_reqs
    return reqs


def _extract_qualifier_version(specifier):
    index = 1
    # Find qualifier (one or two chars).
    if specifier[0] in QUALIFIER_CHARS and specifier[1] in QUALIFIER_CHARS:
        index = 2
    qualifier = specifier[:index]
    version = pkg_version.Version(specifier[index:])
    return qualifier, version


def main():
    args = _grab_args()

    # Build a list of requirements from the global list in the
    # openstack/requirements project so we can match them to the changes
    env_dir = args.env_dir
    req_dir = env_dir + '/src/os-requirements/'
    global_reqs = _extract_reqs(req_dir + '/global-requirements.txt')
    blacklist = _extract_reqs(req_dir + '/blacklist.txt')

    # Build a list of project requirements.
    failed = False
    local_dir = os.getcwd()
    for file_name in PROJECT_REQUIREMENTS_FILES:
        print('Validating requirements file "%s"' % file_name)
        proj_reqs = _extract_reqs(local_dir + '/' + file_name,
                                  blacklist=blacklist)

        for name, req in proj_reqs.items():
            global_req = global_reqs.get(name)
            if not global_req:
                continue
            global_req = global_req[0]
            req = req[0]
            if not global_req.specifiers:
                continue

            specifiers = global_req.specifiers.split(',')
            for spec in specifiers:
                _, req_version = _extract_qualifier_version(req.specifiers)
                g_qualifier, g_version = _extract_qualifier_version(spec)
                if g_qualifier == '!=' and g_version == req_version:
                    print('Package "%s" version %s is not compatible' %
                          (name, req_version))
                    failed = True
                if g_qualifier == '>=' and g_version > req_version:
                    print('Package "%s" version %s outdated, minimum version '
                          '%s' % (name, req_version, g_version))
                    failed = True

    if failed:
        print('Incompatible requirement found!')
        sys.exit(1)
    print('Updated requirements match openstack/requirements')


if __name__ == '__main__':
    main()
