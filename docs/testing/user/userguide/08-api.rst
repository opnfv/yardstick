.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

Yardstick Restful API
======================


Abstract
--------

Yardstick support restful API in danube.


Available API
-------------

/yardstick/env/action
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description: This API is used to do some work related to environment. For now, we support:

1. Prepare yardstick environment (including get external network and load images and flavors)
2. Start an InfluxDB Docker container and config yardstick output to InfluxDB.
3. Start a Grafana Docker container and config with the InfluxDB.

Which API to call will depend on the Parameters.


Method: POST


Prepare Yardstick Environment
Example::

    {
        'action': 'prepareYardstickEnv'
    }

This is an asynchronous API. You need to call /yardstick/asynctask API to get the task result.


Start and Config InfluxDB docker container
Example::

    {
        'action': 'createInfluxDBContainer'
    }

This is an asynchronous API. You need to call /yardstick/asynctask API to get the task result.


Start and Config Grafana docker container
Example::

    {
        'action': 'createGrafanaContainer'
    }

This is an asynchronous API. You need to call /yardstick/asynctask API to get the task result.


/yardstick/asynctask
^^^^^^^^^^^^^^^^^^^^

Description: This API is used to get the status of asynchronous task


Method: GET


Get the status of asynchronous task
Example::

    http://localhost:8888/yardstick/asynctask?task_id=3f3f5e03-972a-4847-a5f8-154f1b31db8c

The returned status will be 0(running), 1(finished) and 2(failed).


/yardstick/testcases
^^^^^^^^^^^^^^^^^^^^

Description: This API is used to list all release test cases now in yardstick.


Method: GET


Get a list of release test cases
Example::

    http://localhost:8888/yardstick/testcases


/yardstick/testcases/release/action
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description: This API is used to run a yardstick release test case.


Method: POST


Run a release test case
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

Description: This API is used to run a yardstick sample test case.


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


/yardstick/testsuites/action
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description: This API is used to run a yardstick test suite.


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


/yardstick/tasks/

Description: This API is used to get the real time log if we use API(v1) run test cases.

Method: GET

Get real time of test cases
Example:

    http://localhost:8888/yardstick/tasks/14795be8-f144-4f54-81ce-43f4e3eab33f/log?index=0


/yardstick/results
^^^^^^^^^^^^^^^^^^

Description: This API is used to get the test results of certain task. If you call /yardstick/testcases/samples/action API, it will return a task id. You can use the returned task id to get the results by using this API.

Method: GET

Get test results of one task
Example::

    http://localhost:8888/yardstick/results?task_id=3f3f5e03-972a-4847-a5f8-154f1b31db8c

This API will return a list of test case result


/api/v2/yardstick/environments/openrcs/action

Description: This API is used to do some work related to OpenStack credential file (openrc). For now, we support:

1. Upload an openrc file for an OpenStack environment.
2. Update an openrc file.
3. Get openrc file information.
4. Delete an openrc file.

Which API to call will depend on the Parameters.


METHOD: POST


Upload an openrc file for an OpenStack environment
Example:

    { 'action': 'upload_openrc',
      'args': { 
            'file': file,
            'environment_id': environment_id
        }
    }


METHOD: POST


Update an openrc file
Example:

    { 'action': 'update_openrc',
        'args': {
            'openrc': {
                "EXTERNAL_NETWORK": "ext-net",
                "OS_AUTH_URL": "http://192.168.23.51:5000/v3",
                "OS_IDENTITY_API_VERSION": "3",
                "OS_IMAGE_API_VERSION": "2",
                "OS_PASSWORD": "console",
                "OS_PROJECT_DOMAIN_NAME": "default",
                "OS_PROJECT_NAME": "admin",
                "OS_TENANT_NAME": "admin",
                "OS_USERNAME": "admin",
                "OS_USER_DOMAIN_NAME": "default"
            },
            'environment_id': environment_id
        }
    }


METHOD: GET

Get openrc file information
Example:
    http://localhost:8888/api/v2/yardstick/environments/openrcs/5g6g3e02-155a-4847-a5f8-154f1b31db8c


METHOD: DELETE


Delete openrc file
Example:
    http://localhost:8888/api/v2/yardstick/environments/openrcs/5g6g3e02-155a-4847-a5f8-154f1b31db8c


/api/v2/yardstick/environments/pods/action

Description: This API is used to do some work related to Yardstick pod file (pod.yaml). For now, we support:

1. Upload a pod file.
2. Get pod file information.
3. Delete an openrc file.

Which API to call will depend on the Parameters.


METHOD: POST


Upload a pod.yaml file
Example:

    { 'action': 'upload_pod_file',
        'args': {
            'file': file,
            'environment_id': environment_id
        }
    }


METHOD: GET

Get pod file information
Example:
    http://localhost:8888/api/v2/yardstick/pods/5g6g3e02-155a-4847-a5f8-154f1b31db8c


METHOD: DELETE

Delete openrc file
Example:
    http://localhost:8888/api/v2/yardstick/pods/5g6g3e02-155a-4847-a5f8-154f1b31db8c
