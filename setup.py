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
