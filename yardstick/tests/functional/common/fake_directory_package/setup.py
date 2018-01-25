# Copyright (c) 2018 Intel Corporation
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

from setuptools import setup, find_packages

setup(
    name='yardstick_new_plugin_2',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    url='https://www.opnfv.org',
    entry_points={
        'yardstick.scenarios': [
            'Dummy2 = yardstick_new_plugin.benchmark.scenarios.dummy2.dummy2:'
            'Dummy2',
        ]
    },
)
