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
            'yardstick/nodes/*/*.yaml'
        ],
        'tests': [
            'opnfv/*/*.yaml'
        ]
    },
    url="https://www.opnfv.org",
    install_requires=["backport_ipaddress",  # remove with python3
                      "coverage>=3.6",
                      "flake8",
                      "Jinja2>=2.6",
                      "lxml",
                      "PyYAML>=3.10",
                      "pbr<2.0,>=1.3",
                      "python-openstackclient>=2.1.0",
                      "python-glanceclient>=0.12.0",
                      "python-heatclient>=0.2.12",
                      "python-keystoneclient>=0.11.1",
                      "python-neutronclient>=2.3.9",
                      "python-novaclient>=2.24.1",
                      "mock>=1.0.1",  # remove with python3
                      "paramiko",
                      "netifaces",
                      "scp",
                      "six",
                      "testrepository>=0.0.18",
                      "testtools>=1.4.0",
                      "nose"
                      ],
    extras_require={
        'plot': ["matplotlib>=1.4.2"]
    },
    entry_points={
        'console_scripts': [
            'yardstick=yardstick.main:main',
            'yardstick-plot=yardstick.plot.plotter:main [plot]'
        ],
    },
    scripts=['tools/yardstick-img-modify']
)
