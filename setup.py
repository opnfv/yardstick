import ez_setup
from setuptools import setup, find_packages

ez_setup.use_setuptools()

setup(
    name="yardstick",
    version="0.1dev",
    packages=find_packages(),
    scripts=['bin/yardstick'],
    include_package_data=True,
    url="https://www.opnfv.org",
    install_requires=["flake8",
                      "PyYAML>=3.10",
                      "python-glanceclient>=0.12.0",
                      "python-heatclient>=0.2.12",
                      "python-keystoneclient>=0.11.1",
                      "python-neutronclient>=2.3.9",
                      "python-novaclient>=2.24.1",
                      "mock>=1.0.1",
                      "paramiko",
                      "six"
                      ],
)
