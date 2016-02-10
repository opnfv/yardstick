.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Intel Corporation and others.


=================================
Apexlake API Interface Definition
=================================

Abstract
--------

The API interface provided by the framework to enable the execution of test
cases is defined as follows.


init
----

**static init()**

    Initializes the Framework

    **Returns** None


execute_framework
-----------------

**static execute_framework** (test_cases,

                                iterations,

                                heat_template,

                                heat_template_parameters,

                                deployment_configuration,

                                openstack_credentials)

    Executes the framework according the specified inputs

    **Parameters**

        - **test_cases**

            Test cases to be run with the workload (dict() of dict())

            Example:
                test_case = dict()

                test_case[’name’] = ‘module.Class’

                test_case[’params’] = dict()

                test_case[’params’][’throughput’] = ‘1’

                test_case[’params’][’vlan_sender’] = ‘1000’

                test_case[’params’][’vlan_receiver’] = ‘1001’

                test_cases = [test_case]

        - **iterations**
            Number of test cycles to be executed (int)

        - **heat_template**
            (string) File name of the heat template corresponding to the workload to be deployed.
            It contains the parameters to be evaluated in the form of #parameter_name.
            (See heat_templates/vTC.yaml as example).

        - **heat_template_parameters**
            (dict) Parameters to be provided as input to the
            heat template. See http://docs.openstack.org/developer/heat/ template_guide/hot_guide.html
            section “Template input parameters” for further info.

        - **deployment_configuration**
            ( dict[string] = list(strings) ) ) Dictionary of parameters
            representing the deployment configuration of the workload.

            The key is a string corresponding to the name of the parameter,
            the value is a list of strings representing the value to be
            assumed by a specific param. The parameters are user defined:
            they have to correspond to the place holders (#parameter_name)
            specified in the heat template.

        **Returns** dict() containing results
