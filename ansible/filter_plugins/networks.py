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


from urlparse import urlsplit


def do_prefix_to_netmask(arg):
    return '.'.join(str((0xffffffff << (32 - int(arg)) >> i) & 0xff) for i in
                    range(24, -8, -8))


def do_netmask_to_prefix(arg):
    return sum([bin(int(x)).count('1') for x in arg.split('.')])


def do_urlsplit(arg):
    return urlsplit(arg)


class FilterModule(object):
    def filters(self):
        return {
            'prefix_to_netmask': do_prefix_to_netmask,
            'netmask_to_prefix': do_netmask_to_prefix,
            'urlsplit': do_urlsplit,
        }
