=================================
Apexlake API interface definition
=================================

The API interface provided by the framework in order to execute the test cases is defined in the following.


init
----

**static init()**

    Initializes the Framework

    **Returns** None


get_available_test_cases
------------------------

**static get_available_test_cases()**

    Returns a list of available test cases. This list include eventual modules developed by the user, if any.
    Each test case is returned as a string that represents the full name of the test case and that
    can be used to get more information calling get_test_case_features(test_case_name)

    **Returns** list of strings


get_test_case_features
----------------------

**static get_test_case_features(test_case)**

    Returns a list of features (description, requested parameters, allowed values, etc.)
    for a specified test case.

    **Parameters**

        - **test_case**

            Name of the test case (string). The string represents the test
            case and can be obtained calling “get_available_test_cases()” method.

    **Returns**
        dict() containing the features of the test case


execute_framework
-----------------

**static execute_framework** (test_cases,

                                iterations,

                                heat_template,

                                heat_template_parameters,

                                deployment_configuration,

                                openstack_credentials)

    Executes the framework according the inputs

    **Parameters**

        - **test_cases**

            Test cases to be ran on the workload (dict() of dict())

            Example:
                test_case = dict()

                test_case[’name’] = ‘module.Class’

                test_case[’params’] = dict()

                test_case[’params’][’throughput’] = ‘1’

                test_case[’params’][’vlan_sender’] = ‘1000’

                test_case[’params’][’vlan_receiver’] = ‘1001’

                test_cases = [test_case]

        - **iterations**
            Number of cycles to be executed (int)

        - **heat_template**
            (string) File name of the heat template of the workload to be deployed.
            It contains the parameters to be evaluated in the form of #parameter_name.
            (See heat_templates/vTC.yaml as example).

        - **heat_template_parameters**
            (dict) Parameters to be provided as input to the
            heat template. See http://docs.openstack.org/developer/heat/ template_guide/hot_guide.html
            section “Template input parameters” for further info.

        - **deployment_configuration**
            ( dict[string] = list(strings) ) ) Dictionary of parameters
            representing the deployment configuration of the workload

            The key is a string corresponding to the name of the parameter,
            the value is a list of strings representing the value to be
            assumed by a specific param. The parameters are user defined:
            they have to correspond to the place holders (#parameter_name)
            specified in the heat template.

        **Returns** dict() containing results
