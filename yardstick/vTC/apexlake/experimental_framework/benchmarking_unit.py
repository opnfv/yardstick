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

'''
The Benchmarking Unit manages the Benchmarking of VNFs orchestrating the
initialization, execution and finalization
'''


import json
import time
import inspect

from experimental_framework.benchmarks import benchmark_base_class as base
from experimental_framework import common
# from experimental_framework import data_manager as data
from experimental_framework import heat_template_generation as heat
from experimental_framework import deployment_unit as deploy


class BenchmarkingUnit:
    """
    Management of the overall Benchmarking process
    """

    def __init__(self, heat_template_name, openstack_credentials,
                 heat_template_parameters, iterations, benchmarks):
        """
        :param heat_template_name: (str) Name of the heat template.

        :param openstack_credentials: (dict) Credentials for openstack.
                        Required fields are: 'ip_controller', 'heat_url',
                        'user', 'password', 'auth_uri', 'project'.

        :param heat_template_parameters: (dict) parameters to be given as
                        input to the heat template. Required keys depend on
                        the specific heat template.

        :param iterations: (int) number of cycles to be executed.

        :param benchmarks: (list[str]) List of the names of the
                        benchmarks/test_cases to be executed in the cycle.

        :return: None
        """
        # Loads vars from configuration file
        self.template_file_extension = common.TEMPLATE_FILE_EXTENSION
        self.template_dir = common.get_template_dir()
        self.results_directory = str(common.RESULT_DIR) + str(time.time())

        # Initializes other internal variable from parameters
        self.template_name = heat_template_name
        self.iterations = iterations
        self.required_benchmarks = benchmarks
        self.template_files = []
        self.benchmarks = list()
        self.benchmark_names = list()
        # self.data_manager = data.DataManager(self.results_directory)
        self.heat_template_parameters = heat_template_parameters
        self.template_files = \
            heat.get_all_heat_templates(self.template_dir,
                                        self.template_file_extension)
        common.DEPLOYMENT_UNIT = deploy.DeploymentUnit(openstack_credentials)

    def initialize(self):
        """
        Initialize the environment in order to run the benchmarking

        :return: None
        """
        for benchmark in self.required_benchmarks:
            benchmark_class = BenchmarkingUnit.get_benchmark_class(
                benchmark['name'])
            # Need to generate a unique name for the benchmark
            # (since there is the possibility to have different
            # instances of the same benchmark)
            self.benchmarks.append(benchmark_class(
                self.get_benchmark_name(benchmark['name']),
                benchmark['params']))

        for template_file_name in self.template_files:
            experiment_name = BenchmarkingUnit.extract_experiment_name(
                template_file_name)
            # self.data_manager.create_new_experiment(experiment_name)
            # for benchmark in self.benchmarks:
            #     self.data_manager.add_benchmark(experiment_name,
            #                                    benchmark.get_name())

    def finalize(self):
        """
        Finalizes the Benchmarking Unit
        Destroys all the stacks deployed by the framework and save results on
        csv file.

        :return: None
        """
        # self.data_manager.generate_result_csv_file()
        common.DEPLOYMENT_UNIT.destroy_all_deployed_stacks()

    def run_benchmarks(self):
        """
        Runs all the requested benchmarks and collect the results.

        :return: None
        """
        common.LOG.info('Run Benchmarking Unit')

        experiment = dict()
        result = dict()
        for iteration in range(0, self.iterations):
            common.LOG.info('Iteration ' + str(iteration))
            for template_file_name in self.template_files:
                experiment_name = BenchmarkingUnit.\
                    extract_experiment_name(template_file_name)
                experiment['experiment_name'] = experiment_name
                configuration = self.\
                    get_experiment_configuration(template_file_name)
                # self.data_manager.add_configuration(experiment_name,
                #                                     configuration)
                for key in configuration.keys():
                    experiment[key] = configuration[key]
                # metadata = dict()
                # metadata['experiment_name'] = experiment_name
                # self.data_manager.add_metadata(experiment_name, metadata)

                # For each benchmark in the cycle the workload is deployed
                for benchmark in self.benchmarks:
                    log_msg = 'Benchmark {} started on {}'.format(
                        benchmark.get_name(), template_file_name
                    )
                    common.LOG.info(log_msg)

                    # Initialization of Benchmark
                    benchmark.init()
                    log_msg = 'Template {} deployment START'.\
                        format(experiment_name)
                    common.LOG.info(log_msg)

                    # Deployment of the workload
                    deployment_success = \
                        common.DEPLOYMENT_UNIT.deploy_heat_template(
                            self.template_dir + template_file_name,
                            experiment_name,
                            self.heat_template_parameters)

                    if deployment_success:
                        log_msg = 'Template {} deployment COMPLETED'.format(
                            experiment_name)
                        common.LOG.info(log_msg)
                    else:
                        log_msg = 'Template {} deployment FAILED'.format(
                            experiment_name)
                        common.LOG.info(log_msg)
                        continue

                    # Running the Benchmark/test case
                    result = benchmark.run()
                    # self.data_manager.add_data_points(experiment_name,
                    #                                   benchmark.get_name(),
                    #                                   result)

                    # Terminate the workload
                    log_msg = 'Destroying deployment for experiment {}'.\
                        format(experiment_name)
                    common.LOG.info(log_msg)
                    common.DEPLOYMENT_UNIT.destroy_heat_template(
                        experiment_name)

                    # Finalize the benchmark
                    benchmark.finalize()
                    log_msg = 'Benchmark {} terminated'.format(
                        benchmark.__class__.__name__)
                    common.LOG.info(log_msg)
                    # self.data_manager.generate_result_csv_file()

                    experiment['benchmark'] = benchmark.get_name()
                    for key in benchmark.get_params():
                        experiment[key] = benchmark.get_params()[key]
                common.LOG.info('Benchmark Finished')
                self.data_manager.generate_result_csv_file()
        common.LOG.info('Benchmarking Unit: Experiments completed!')
        return result

    def get_experiment_configuration(self, template_file_name):
        """
        Reads and returns the configuration for the specific experiment
        (heat template)

        :param template_file_name: (str) Name of the file for the heat
                        template for which it is requested the configuration

        :return: dict() Configuration parameters and values
        """
        file_name = "{}{}.json".format(self.template_dir, template_file_name)
        with open(file_name) as json_file:
            configuration = json.load(json_file)
        return configuration

    def get_benchmark_name(self, name, instance=0):
        """
        Returns the name to be used for the benchmark/test case (TC).
        This is required since each benchmark/TC could be run more than once
        within the same cycle, with different initialization parameters.
        In order to distinguish between them, a unique name is generated.

        :param name: (str) original name of the benchmark/TC

        :param instance: (int) number of instance already in the queue for
                        this type of benchmark/TC.

        :return: (str) name to be assigned to the benchmark/TC
        """
        if name + "_" + str(instance) in self.benchmark_names:
            instance += 1
            return self.get_benchmark_name(name, instance)
        self.benchmark_names.append(name + "_" + str(instance))
        return name + "_" + str(instance)

    @staticmethod
    def extract_experiment_name(template_file_name):
        """
        Generates a unique experiment name for a given template.

        :param template_file_name: (str) File name of the template used
                        during the experiment string

        :return: (str) Experiment Name
        """
        strings = template_file_name.split('.')
        return ".".join(strings[:(len(strings)-1)])

    @staticmethod
    def get_benchmark_class(complete_module_name):
        """
        Returns the classes included in a given module.

        :param complete_module_name: (str) Complete name of the module as
                        returned by get_available_test_cases.

        :return: Class related to the benchmark/TC present in the requested
                        module.
        """
        strings = complete_module_name.split('.')
        class_name = 'experimental_framework.benchmarks.{}'.format(strings[0])
        pkg = __import__(class_name, globals(), locals(), [], -1)
        module = getattr(getattr(pkg, 'benchmarks'), strings[0])
        members = inspect.getmembers(module)
        for m in members:
            if inspect.isclass(m[1]):
                class_name = m[1]("", dict()).__class__.__name__
                if isinstance(m[1]("", dict()), base.BenchmarkBaseClass) and \
                        not class_name == 'BenchmarkBaseClass':
                    return m[1]

    @staticmethod
    def get_required_benchmarks(required_benchmarks):
        """
        Returns instances of required test cases.

        :param required_benchmarks: (list() of strings) Benchmarks to be
                        executed by the experimental framework.

        :return: list() of BenchmarkBaseClass
        """
        benchmarks = list()
        for b in required_benchmarks:
            class_ = BenchmarkingUnit.get_benchmark_class(b)
            instance = class_("", dict())
            benchmarks.append(instance)
        return benchmarks
