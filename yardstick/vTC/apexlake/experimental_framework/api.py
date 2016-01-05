# Copyright (c) 2015 Intel Research and Development Ireland Ltd.
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

import experimental_framework.benchmarking_unit as b_unit
from experimental_framework import heat_template_generation, common


class FrameworkApi(object):

    @staticmethod
    def init():
        """
        Initializes the Framework

        :return: None
        """
        common.init(api=True)

    # @staticmethod
    # def get_available_test_cases():
    #     """
    #     Returns a list of available test cases.
    #     This list include eventual modules developed by the user, if any.
    #     Each test case is returned as a string that represents the full name
    #     of the test case and that can be used to get more information
    #     calling get_test_case_features(test_case_name)
    #
    #     :return: list of strings
    #     """
    #     return b_unit.BenchmarkingUnit.get_available_test_cases()

    @staticmethod
    def get_test_case_features(test_case):
        """
        Returns a list of features (description, requested parameters,
        allowed values, etc.) for a specified test case.

        :param test_case: name of the test case (string)
                          The string represents the test case and can be
                          obtained  calling  "get_available_test_cases()"
                          method.

        :return: dict() containing the features of the test case
        """
        if not isinstance(test_case, str):
            raise ValueError('The provided test_case parameter has to be '
                             'a string')
        benchmark = b_unit.BenchmarkingUnit.get_required_benchmarks(
            [test_case])[0]
        return benchmark.get_features()

    @staticmethod
    def execute_framework(
            test_cases,
            iterations,
            heat_template,
            heat_template_parameters,
            deployment_configuration,
            openstack_credentials
    ):
        """
        Executes the framework according the inputs

        :param test_cases: Test cases to be ran on the workload
                            (dict() of dict())

                            Example:
                            test_case = dict()
                            test_case['name'] = 'module.Class'
                            test_case['params'] = dict()
                            test_case['params']['throughput'] = '1'
                            test_case['params']['vlan_sender'] = '1007'
                            test_case['params']['vlan_receiver'] = '1006'
                            test_cases = [test_case]

        :param iterations: Number of cycles to be executed (int)

        :param heat_template: (string) File name of the heat template of the
                            workload to be deployed. It contains the
                            parameters to be evaluated in the form of
                            #parameter_name. (See heat_templates/vTC.yaml as
                            example).

        :param heat_template_parameters: (dict) Parameters to be provided
                            as input to the heat template.
                            See http://docs.openstack.org/developer/heat/
                            template_guide/hot_guide.html - section
                            "Template input parameters" for further info.

        :param deployment_configuration: ( dict[string] = list(strings) ) )
                            Dictionary of parameters representing the
                            deployment configuration of the workload
                            The key is a string corresponding to the name of
                            the parameter, the value is a list of strings
                            representing the value to be assumed by a specific
                            param.
                            The parameters are user defined: they have to
                            correspond to the place holders (#parameter_name)
                            specified in the heat template.

        :return: dict() Containing results
        """
        common.init(api=True)

        # Input Validation
        common.InputValidation.validate_os_credentials(openstack_credentials)
        credentials = openstack_credentials

        msg = 'The provided heat_template does not exist'
        template = "{}{}".format(common.get_template_dir(), heat_template)
        common.InputValidation.validate_file_exist(template, msg)

        msg = 'The provided iterations variable must be an integer value'
        common.InputValidation.validate_integer(iterations, msg)

        msg = 'The provided heat_template_parameters variable must be a ' \
              'dictionary'
        common.InputValidation.validate_dictionary(heat_template_parameters,
                                                   msg)
        log_msg = "Generation of all the heat templates " \
                  "required by the experiment"
        common.LOG.info(log_msg)
        heat_template_generation.generates_templates(heat_template,
                                                     deployment_configuration)
        benchmarking_unit = \
            b_unit.BenchmarkingUnit(
                heat_template, credentials, heat_template_parameters,
                iterations, test_cases)
        try:
            common.LOG.info("Benchmarking Unit initialization")
            benchmarking_unit.initialize()
            common.LOG.info("Benchmarking Unit Running")
            results = benchmarking_unit.run_benchmarks()
        finally:
            common.LOG.info("Benchmarking Unit Finalization")
            benchmarking_unit.finalize()
        return results
