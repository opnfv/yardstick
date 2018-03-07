.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

Yardstick Restful API
======================


Abstract
--------

Yardstick support restful API since Danube.


Available API
-------------

/yardstick/env/action
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description: This API is used to prepare Yardstick test environment. For Euphrates, it supports:

1. Prepare yardstick test environment, including set external network environment variable, load Yardstick VM images and create flavors;
2. Start an InfluxDB Docker container and config Yardstick output to InfluxDB;
3. Start a Grafana Docker container and config it with the InfluxDB.

Which API to call will depend on the parameters.


Method: POST


Prepare Yardstick test environment
Example::

    {
        'action': 'prepareYardstickEnv'
    }

This is an asynchronous API. You need to call /yardstick/asynctask API to get the task result.


Start and config an InfluxDB docker container
Example::

    {
        'action': 'createInfluxDBContainer'
    }

This is an asynchronous API. You need to call /yardstick/asynctask API to get the task result.


Start and config a Grafana docker container
Example::

    {
        'action': 'createGrafanaContainer'
    }

This is an asynchronous API. You need to call /yardstick/asynctask API to get the task result.


/yardstick/asynctask
^^^^^^^^^^^^^^^^^^^^

Description: This API is used to get the status of asynchronous tasks


Method: GET


Get the status of asynchronous tasks
Example::

    http://localhost:8888/yardstick/asynctask?task_id=3f3f5e03-972a-4847-a5f8-154f1b31db8c

The returned status will be 0(running), 1(finished) and 2(failed).


/yardstick/testcases
^^^^^^^^^^^^^^^^^^^^

Description: This API is used to list all released Yardstick test cases.


Method: GET


Get a list of released test cases
Example::

    http://localhost:8888/yardstick/testcases


/yardstick/testcases/release/action
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description: This API is used to run a Yardstick released test case.


Method: POST


Run a released test case
Example::

    {
        'action': 'runTestCase',
        'args': {
            'opts': {},
            'testcase': 'tc002'
        }
    }

This is an asynchronous API. You need to call /yardstick/results to get the result.


/yardstick/testcases/samples/action
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description: This API is used to run a Yardstick sample test case.


Method: POST


Run a sample test case
Example::

    {
        'action': 'runTestCase',
        'args': {
            'opts': {},
            'testcase': 'ping'
        }
    }

This is an asynchronous API. You need to call /yardstick/results to get the result.


/yardstick/testcases/<testcase_name>/docs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description: This API is used to the documentation of a certain released test case.


Method: GET


Get the documentation of a certain test case
Example::

    http://localhost:8888/yardstick/taskcases/opnfv_yardstick_tc002/docs


/yardstick/testsuites/action
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description: This API is used to run a Yardstick test suite.


Method: POST


Run a test suite
Example::

    {
        'action': 'runTestSuite',
        'args': {
            'opts': {},
            'testcase': 'smoke'
        }
    }

This is an asynchronous API. You need to call /yardstick/results to get the result.


/yardstick/tasks/<task_id>/log

Description: This API is used to get the real time log of test case execution.


Method: GET


Get real time of test case execution
Example::

    http://localhost:8888/yardstick/tasks/14795be8-f144-4f54-81ce-43f4e3eab33f/log?index=0


/yardstick/results
^^^^^^^^^^^^^^^^^^

Description: This API is used to get the test results of tasks. If you call /yardstick/testcases/samples/action API, it will return a task id. You can use the returned task id to get the results by using this API.


Method: GET


Get test results of one task
Example::

    http://localhost:8888/yardstick/results?task_id=3f3f5e03-972a-4847-a5f8-154f1b31db8c

This API will return a list of test case result


/api/v2/yardstick/openrcs/action

Description: This API provides functionality of handling OpenStack credential file (openrc). For Euphrates, it supports:

1. Upload an openrc file for an OpenStack environment;
2. Update an openrc file;
3. Get openrc file information;
4. Delete an openrc file.

Which API to call will depend on the parameters.


METHOD: POST


Upload an openrc file for an OpenStack environment
Example::

    {
        'action': 'upload_openrc',
        'args': {
            'file': file,
            'environment_id': environment_id
        }
    }


METHOD: POST


Update an openrc file
Example::

    {
        'action': 'update_openrc',
        'args': {
            'openrc': {
                "EXTERNAL_NETWORK": "ext-net",
                "OS_AUTH_URL": "http://192.168.23.51:5000/v3",
                "OS_IDENTITY_API_VERSION": "3",
                "OS_IMAGE_API_VERSION": "2",
                "OS_PASSWORD": "console",
                "OS_PROJECT_DOMAIN_NAME": "default",
                "OS_PROJECT_NAME": "admin",
                "OS_USERNAME": "admin",
                "OS_USER_DOMAIN_NAME": "default"
            },
            'environment_id': environment_id
        }
    }


METHOD: GET

Get openrc file information
Example::

    http://localhost:8888/api/v2/yardstick/openrcs/5g6g3e02-155a-4847-a5f8-154f1b31db8c


METHOD: DELETE


Delete openrc file
Example::

    http://localhost:8888/api/v2/yardstick/openrcs/5g6g3e02-155a-4847-a5f8-154f1b31db8c


/api/v2/yardstick/pods/action

Description: This API provides functionality of handling Yardstick pod file (pod.yaml). For Euphrates, it supports:

1. Upload a pod file;
2. Get pod file information;
3. Delete an openrc file.

Which API to call will depend on the parameters.


METHOD: POST


Upload a pod.yaml file
Example::

    {
        'action': 'upload_pod_file',
        'args': {
            'file': file,
            'environment_id': environment_id
        }
    }


METHOD: GET

Get pod file information
Example::

    http://localhost:8888/api/v2/yardstick/pods/5g6g3e02-155a-4847-a5f8-154f1b31db8c


METHOD: DELETE

Delete openrc file
Example::

    http://localhost:8888/api/v2/yardstick/pods/5g6g3e02-155a-4847-a5f8-154f1b31db8c


/api/v2/yardstick/images/action

Description: This API is used to do some work related to Yardstick VM images. For Euphrates, it supports:

1. Load Yardstick VM images;
2. Get image's information;
3. Delete images.

Which API to call will depend on the parameters.


METHOD: POST


Load VM images
Example::

    {
        'action': 'load_images'
    }


METHOD: GET

Get image information
Example::

    http://localhost:8888/api/v2/yardstick/images/5g6g3e02-155a-4847-a5f8-154f1b31db8c


METHOD: DELETE

Delete images
Example::

    http://localhost:8888/api/v2/yardstick/images/5g6g3e02-155a-4847-a5f8-154f1b31db8c


/api/v2/yardstick/tasks/action

Description: This API is used to do some work related to yardstick tasks. For Euphrates, it supports:

1. Create a Yardstick task;
2. run a Yardstick task;
3. Add a test case to a task;
4. Add a test suite to a task;
5. Get a tasks' information;
6. Delete a task.

Which API to call will depend on the parameters.


METHOD: POST


Create a Yardstick task
Example::

    {
        'action': 'create_task',
            'args': {
                'name': 'task1',
                'project_id': project_id
            }
    }


METHOD: PUT


Run a task
Example::

    {
        'action': 'run'
    }


METHOD: PUT


Add a test case to a task
Example::

    {
        'action': 'add_case',
        'args': {
            'case_name': 'opnfv_yardstick_tc002',
            'case_content': case_content
        }
    }


METHOD: PUT


Add a test suite to a task
Example::

    {
        'action': 'add_suite',
        'args': {
            'suite_name': 'opnfv_smoke',
            'suite_content': suite_content
        }
    }


METHOD: GET

Get a task's information
Example::

    http://localhost:8888/api/v2/yardstick/tasks/5g6g3e02-155a-4847-a5f8-154f1b31db8c


METHOD: DELETE

Delete a task
Example::
    http://localhost:8888/api/v2/yardstick/tasks/5g6g3e02-155a-4847-a5f8-154f1b31db8c


/api/v2/yardstick/testcases/action

Description: This API is used to do some work related to yardstick testcases. For Euphrates, it supports:

1. Upload a test case;
2. Get all released test cases' information;
3. Get a certain released test case's information;
4. Delete a test case.

Which API to call will depend on the parameters.


METHOD: POST


Upload a test case
Example::

    {
        'action': 'upload_case',
        'args': {
            'file': file
        }
    }


METHOD: GET


Get all released test cases' information
Example::

    http://localhost:8888/api/v2/yardstick/testcases


METHOD: GET


Get a certain released test case's information
Example::

    http://localhost:8888/api/v2/yardstick/testcases/opnfv_yardstick_tc002


METHOD: DELETE


Delete a certain test case
Example::
    http://localhost:8888/api/v2/yardstick/testcases/opnfv_yardstick_tc002


/api/v2/yardstick/testsuites/action

Description: This API is used to do some work related to yardstick test suites. For Euphrates, it supports:

1. Create a test suite;
2. Get a certain test suite's information;
3. Get all test suites;
4. Delete a test case.

Which API to call will depend on the parameters.


METHOD: POST


Create a test suite
Example::

    {
        'action': 'create_sutie',
        'args': {
            'name': <suite_name>,
            'testcases': [
                'opnfv_yardstick_tc002'
            ]
        }
    }


METHOD: GET


Get a certain test suite's information
Example::

    http://localhost:8888/api/v2/yardstick/testsuites/<suite_name>


METHOD: GET


Get all test suite
Example::

    http://localhost:8888/api/v2/yardstick/testsuites


METHOD: DELETE


Delete a certain test suite
Example::

    http://localhost:8888/api/v2/yardstick/testsuites/<suite_name>


/api/v2/yardstick/projects/action

Description: This API is used to do some work related to yardstick test projects. For Euphrates, it supports:

1. Create a Yardstick project;
2. Get a certain project's information;
3. Get all projects;
4. Delete a project.

Which API to call will depend on the parameters.


METHOD: POST


Create a Yardstick project
Example::

    {
        'action': 'create_project',
        'args': {
            'name': 'project1'
        }
    }


METHOD: GET


Get a certain project's information
Example::

    http://localhost:8888/api/v2/yardstick/projects/<project_id>


METHOD: GET


Get all projects' information
Example::

    http://localhost:8888/api/v2/yardstick/projects


METHOD: DELETE


Delete a certain project
Example::

    http://localhost:8888/api/v2/yardstick/projects/<project_id>


/api/v2/yardstick/containers/action

Description: This API is used to do some work related to Docker containers. For Euphrates, it supports:

1. Create a Grafana Docker container;
2. Create an InfluxDB Docker container;
3. Get a certain container's information;
4. Delete a container.

Which API to call will depend on the parameters.


METHOD: POST


Create a Grafana Docker container
Example::

    {
        'action': 'create_grafana',
        'args': {
            'environment_id': <environment_id>
        }
    }


METHOD: POST


Create an InfluxDB Docker container
Example::

    {
        'action': 'create_influxdb',
        'args': {
            'environment_id': <environment_id>
        }
    }


METHOD: GET


Get a certain container's information
Example::

    http://localhost:8888/api/v2/yardstick/containers/<container_id>


METHOD: DELETE


Delete a certain container
Example::

    http://localhost:8888/api/v2/yardstick/containers/<container_id>
