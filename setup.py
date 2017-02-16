# Copyright (c) 2016-2017 Intel Corporation
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

from __future__ import absolute_import
from setuptools import setup, find_packages


setup(
    name="yardstick",
    version="0.1.dev0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'yardstick': [
            'benchmark/scenarios/availability/*.yaml',
            'benchmark/scenarios/availability/attacker/*.yaml',
            'benchmark/scenarios/availability/ha_tools/*.bash',
            'benchmark/scenarios/availability/ha_tools/*/*.bash',
            'benchmark/scenarios/availability/attacker/scripts/*.bash',
            'benchmark/scenarios/availability/monitor/*.yaml',
            'benchmark/scenarios/availability/monitor/script_tools/*.bash',
            'benchmark/scenarios/compute/*.bash',
            'benchmark/scenarios/networking/*.bash',
            'benchmark/scenarios/networking/*.txt',
            'benchmark/scenarios/parser/*.sh',
            'benchmark/scenarios/storage/*.bash',
            'resources/files/*',
            'resources/scripts/install/*.bash',
            'resources/scripts/remove/*.bash'
        ],
        'etc': [
            'yardstick/nodes/*/*.yaml',
            'yardstick/*.sample'
        ],
        'tests': [
            'opnfv/*/*.yaml',
            'ci/*.sh'
        ]
    },
    url="https://www.opnfv.org",
    extras_require={
        'plot': ["matplotlib>=1.4.2"]
    },
    entry_points={
        'console_scripts': [
            'yardstick=yardstick.main:main',
            'yardstick-plot=yardstick.plot.plotter:main [plot]'
        ],
    },
    scripts=[
        'tools/yardstick-img-modify',
        'tools/yardstick-img-lxd-modify',
        'tools/yardstick-img-dpdk-modify'
    ]
)
