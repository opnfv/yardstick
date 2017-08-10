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

import pkg_resources
import pip.req
import sys


def get_pkg_license(pkg):
    """
    Given a package reference (as from requirements.txt),
    return license listed in package metadata.
    NOTE: This function does no error checking and is for
    demonstration purposes only.

    can-pip-or-setuptools-distribute-etc-list-the-license-used-by-each-install
    https://stackoverflow.com/a/19086260
    https://stackoverflow.com/users/308066/dkamins
    """
    try:
        pkgs = pkg_resources.working_set.resolve(pkg, replace_conflicting=True)
        # pkgs = pkg_resources.require(pkg)
    except pkg_resources.DistributionNotFound as e:
        sys.stderr.write("%s\n" % e)
        return None
    pkg = pkgs[0]
    try:
        info = pkg.get_metadata_lines('METADATA')
    except IOError:
        try:
            info = pkg.get_metadata_lines('PKG-INFO')
        except IOError:
            info = []
    licenses = []
    for line in info:
        if "License:" in line:
            lic = line.split(': ', 1)[1]
            if "UNKNOWN" not in lic:
                # try this type first
                licenses.append(lic)
                # break
        elif "License ::" in line:
            licenses.append(" ".join(line.split(':: ')[1:3]))
    return "; ".join(licenses)

# quick and dirty hack


def main():

    reqs = list(pip.req.parse_requirements("../../requirements.txt", session='hack'))
    lines = []
    for req in reqs:
        pkg = pkg_resources.parse_requirements([req.name])
        lic = get_pkg_license(pkg)
        markers = req.markers
        if markers:
            mark = "; " + str(req.markers)
        else:
            mark = ""
        line = "{0}{1}\t\t# {2}\n".format(req.req, mark, lic)
        sys.stdout.write(line)
        lines.append(line)
    with open("requirements.txt", "w") as rrr:
        rrr.writelines(lines)


if __name__ == '__main__':
    main()
