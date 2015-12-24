"""
Experimental Framework
"""

from distutils.core import setup


# TODO: Add instruction to compile the test_sniff

setup(name='apexlake',
      version='1.0',
      description='Framework to automatically run experiments/benchmarks '
                  'with VMs within OpenStack environments',
      author='Intel Research and Development Ireland Ltd',
      author_email='vincenzo.m.riccobene@intel.com',
      license='Apache 2.0',
      url='www.intel.com',
      packages=['experimental_framework',
                'experimental_framework.benchmarks',
                'experimental_framework.packet_generators',
                'experimental_framework.libraries',
                'experimental_framework.constants'],
      include_package_data=True,
      package_data={
          'experimental_framework': [
              'packet_generators/dpdk_pktgen/*.lua',
              'packet_generators/pcap_files/*.pcap',
              'packet_generators/pcap_files/*.sh',
              'libraries/packet_checker/*'
          ]
      },
      data_files=[
          ('/etc/apexlake/', ['apexlake.conf']),
          ('/etc/apexlake/heat_templates/',
           ['heat_templates/vTC.yaml']),
          ('/etc/apexlake/heat_templates/',
           ['heat_templates/stress_workload.yaml'])
      ])
