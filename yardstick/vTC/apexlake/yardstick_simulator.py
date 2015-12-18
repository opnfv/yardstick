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


from experimental_framework import common, api


# Initializes the framework
api.FrameworkApi.init()

##########################################################################
# Use Case 1 - Get the list of the available TestCases
available_test_cases = api.FrameworkApi.get_available_test_cases()


##########################################################################
# Use Case 2 - Get the Description of each test case
# (text description and required parameters)
# and the features (required params and allowed values)
tc_features = dict()
common.LOG.info('Available test cases')
for tc in available_test_cases:
    common.LOG.info(tc)
    tc_features[tc] = api.FrameworkApi.get_test_case_features(tc)
    common.LOG.info(tc_features[tc])


##########################################################################
# Use Case 3 - Execute some test cases from the Framework:

# Set the OpenStack credentials
openstack_credentials = dict()
openstack_credentials['ip_controller'] = 'IP_CONTROLLER'
openstack_credentials['heat_url'] = 'http://IP_CONTROLLER:8004/v1/' \
                                    'tenant_id'
openstack_credentials['user'] = 'admin'
openstack_credentials['password'] = 'password'
openstack_credentials['auth_uri'] = 'http://IP_CONTROLLER:5000/v2.0'
openstack_credentials['project'] = 'project_name'

# Set the number of cycles to be run
iterations = 2

# Select which heat template to use
heat_template = 'vTC.yaml'

# Set deployment configuration of the vTC
# # SHORT RUN CONFIGURATION (Only 2 Deployment Configurations)
# deployment_configuration = dict()
# deployment_configuration['vnic_type'] = ['normal', 'direct']
# deployment_configuration['vtc_flavor'] = ['m1.large']

# LONG RUN CONFIGURATION (6 Deployment configurations)
deployment_configuration = dict()
deployment_configuration['vnic_type'] = ['normal', 'direct']
deployment_configuration['vtc_flavor'] = [
    'm1.small',
    'm1.medium',
    'm1.large']
# It is possible to add more configurations

# heat template parameters (Required to initialize the vTC
heat_template_parameters = dict()
heat_template_parameters['key_name'] = "apexlake_key"
heat_template_parameters['ip_family'] = "192.168.204"
heat_template_parameters['name'] = "vtc_compB"
heat_template_parameters['default_net'] = "net04"
heat_template_parameters['default_subnet'] = "net04__subnet "
heat_template_parameters['source_net'] = "apexlake_inbound_net"
heat_template_parameters['source_subnet'] = "inbound_sub"
heat_template_parameters['destination_net'] = "apexlake_outbound_net"
heat_template_parameters['destination_subnet'] = "outbound_sub"

# Configure the test cases to be executed
packet_sizes = ['64', '128', '256', '512', '1024', '1280', '1518']
avail_test_cases = [
    'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark',
    'multi_tenancy_throughput_benchmark.MultiTenancyThroughputBenchmark'
    'instantiation_validation_benchmark.InstantiationValidationBenchmark',
    'instantiation_validation_noisy_neighbors_benchmark.'
    'InstantiationValidationNoisyNeighborsBenchmark'
]

# # Short Run
# test_cases = list()
# test_case1 = dict()
# test_case1['name'] = \
#     'instantiation_validation_benchmark.InstantiationValidationBenchmark'
# test_case1['params'] = dict()
# test_case1['params']['packet_size'] = '1280'
# test_cases.append(test_case1)
#
# test_case2 = dict()
# test_case2['name'] = 'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark'
# test_case2['params'] = dict()
# test_case2['params']['packet_size'] = '1280'
# test_cases.append(test_case2)
#
# test_case3 = dict()
# test_case3['name'] = 'multi_tenancy_cpu_throughput_benchmark.' \
#                      'MultiTenancyCpuThroughputBenchmark'
# test_case3['params'] = dict()
# test_case3['params']['packet_size'] = '1280'
# test_cases.append(test_case3)

# Long Run
test_cases = list()

for pkt_sz in packet_sizes:
    test_case = dict()
    test_case['name'] = available_test_cases[0]
    test_case['params'] = dict()
    test_case['params']['packet_size'] = pkt_sz
    test_case['params']['vlan_sender'] = 2025
    test_case['params']['vlan_receiver'] = 2021
    test_cases.append(test_case)

    test_case = dict()
    test_case['name'] = available_test_cases[1]
    test_case['params'] = dict()
    test_case['params']['packet_size'] = pkt_sz
    test_case['params']['vlan_sender'] = 2025
    test_case['params']['vlan_receiver'] = 2021
    test_case['params']['num_of_neighbours'] = 1
    test_case['params']['amount_of_ram'] = 4096
    test_case['params']['number_of_cores'] = 2
    test_cases.append(test_case)

test_case = dict()
test_case['name'] = available_test_cases[2]
test_case['params'] = dict()
test_case['params']['throughput'] = 5
test_case['params']['vlan_sender'] = 2025
test_case['params']['vlan_receiver'] = 2021
test_cases.append(test_case)

test_case = dict()
test_case['name'] = available_test_cases[3]
test_case['params'] = dict()
test_case['params']['throughput'] = 5
test_case['params']['vlan_sender'] = 2025
test_case['params']['vlan_receiver'] = 2021
test_case['params']['num_of_neighbours'] = 1
test_case['params']['amount_of_ram'] = 4096
test_case['params']['number_of_cores'] = 2
test_cases.append(test_case)

# Invokes the framework
api.FrameworkApi.execute_framework(test_cases, iterations, heat_template,
                                   heat_template_parameters,
                                   deployment_configuration,
                                   openstack_credentials)
