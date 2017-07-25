# Copyright 2015-2017 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
vSwitch Characterization Report Generation.

Generate reports in format defined by X.
"""

import os
import logging
import jinja2

from core.results.results_constants import ResultsConstants
from conf import settings as S
from tools import systeminfo

_TEMPLATE_FILES = ['report.jinja', 'report_rst.jinja']
_ROOT_DIR = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))


def _get_env(result, versions):
    """
    Get system configuration.

    :returns: Return a dictionary of the test environment.
              The following is an example return value:
               {'kernel': '3.10.0-229.4.2.el7.x86_64',
                'os': 'OS Version',
                'cpu': ' CPU 2.30GHz',
                'platform': '[2 sockets]',
                'nic': 'NIC'}

    """
    def _get_version(name, versions):
        """Returns version of tool with given `name` if version was not read
        during runtime (not inside given `versions` list), then it will be
        obtained by call of systeminfo.get_version()
        """
        for version in versions:
            if version.get()['name'] == name:
                return version

        return systeminfo.get_version(name)

    env = {
        'os': systeminfo.get_os(),
        'kernel': systeminfo.get_kernel(),
        'nics': systeminfo.get_nic(),
        'cpu': systeminfo.get_cpu(),
        'cpu_cores': systeminfo.get_cpu_cores(),
        'memory' : systeminfo.get_memory(),
        'platform': systeminfo.get_platform(),
        'vsperf': systeminfo.get_version('vswitchperf'),
        'traffic_gen': systeminfo.get_version(S.getValue('TRAFFICGEN')),
        'vswitch': _get_version(S.getValue('VSWITCH'), versions),
    }

    if str(S.getValue('VSWITCH')).lower().count('dpdk'):
        env.update({'dpdk': _get_version('dpdk', versions)})

    if result[ResultsConstants.DEPLOYMENT].count('v'):
        env.update({'vnf': systeminfo.get_version(S.getValue('VNF')),
                    'guest_image': S.getValue('GUEST_IMAGE'),
                    'loopback_app': list(map(systeminfo.get_loopback_version,
                                             S.getValue('GUEST_LOOPBACK'))),
                   })

    return env


def generate(testcase):
    """Generate actual report.

    Generate a Markdown and RST formatted files using results of tests and some
    parsed system info.

    :param input_file: Path to CSV results file
    :param tc_results: A list of dictionaries with detailed test results.
        Each dictionary represents test results for one of specified packet
        sizes.
    :param tc_stats: System statistics collected during testcase execution.
        These statistics are overall statistics for all specified packet
        sizes.
    :param traffic: Dictionary with traffic definition used by TC to control
        traffic generator.
    :test_type: Specifies type of the testcase. Supported values are
        'performance' and 'integration'.

    :returns: Path to generated report
    """
    output_files = [('.'.join([os.path.splitext(testcase.get_output_file())[0], 'md'])),
                    ('.'.join([os.path.splitext(testcase.get_output_file())[0], 'rst']))]
    template_loader = jinja2.FileSystemLoader(searchpath=_ROOT_DIR)
    template_env = jinja2.Environment(loader=template_loader)

    tests = []
    try:
        # there might be multiple test results, but they are produced
        # by the same test, only traffic details (e.g. packet size)
        # differs
        # in case that multiple TC conf values will be needed, then
        # testcase refactoring should be made to store updated cfg
        # options into testcase._cfg dictionary
        test_config = {'Description' : testcase.get_desc(),
                       'bidir' : testcase.get_traffic()['bidir']}

        for result in testcase.get_tc_results():
            # pass test results, env details and configuration to template
            tests.append({
                'ID': result[ResultsConstants.ID].upper(),
                'id': result[ResultsConstants.ID],
                'deployment': result[ResultsConstants.DEPLOYMENT],
                'conf': test_config,
                'result': result,
                'env': _get_env(result, testcase.get_versions()),
                'stats': testcase.get_collector().get_results(),
            })

            # remove id and deployment from results before rendering
            # but after _get_env() is called; tests dict has its shallow copy
            del result[ResultsConstants.ID]
            del result[ResultsConstants.DEPLOYMENT]

        template_vars = {
            'tests': tests,
        }
        i = 0
        # pylint: disable=no-member
        for output_file in output_files:
            template = template_env.get_template(_TEMPLATE_FILES[i])
            output_text = template.render(template_vars)
            with open(output_file, 'w') as file_:
                file_.write(output_text)
                logging.info('Test report written to "%s"', output_file)
            i += 1

    except KeyError:
        logging.info("Report: Ignoring file (Wrongly defined columns): %s",
                     testcase.get_output_file())
        raise
    return output_files
