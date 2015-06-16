import ez_setup
from setuptools import setup, find_packages

ez_setup.use_setuptools()

setup(
    name="yardstick",
    version="0.1.dev0",
    packages=find_packages(),
    include_package_data=True,
    package_data={'yardstick': ['benchmark/scenarios/networking/*.bash']},
    url="https://www.opnfv.org",
    install_requires=["backport_ipaddress",  # remove with python3
                      "flake8",
                      "PyYAML>=3.10",
                      "pbr!=0.7,<1.0,>=0.6",
                      "python-glanceclient>=0.12.0",
                      "python-heatclient>=0.2.12",
                      "python-keystoneclient>=0.11.1",
                      "python-neutronclient>=2.3.9",
                      "python-novaclient>=2.24.1",
                      "mock>=1.0.1",  # remove with python3
                      "paramiko",
                      "six"
                      ],
    entry_points={
        'console_scripts': [
            'yardstick=yardstick.main:main',
        ],
    },
    scripts=['tools/yardstick-img-modify']
)
