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

1. Prepare yardstick environment(Including fetch openrc file, get external network and load images)
2. Start a InfluxDB docker container and config yardstick output to InfluxDB.
3. Start a Grafana docker container and config with the InfluxDB.

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


/yardstick/results
^^^^^^^^^^^^^^^^^^


Description: This API is used to get the test results of certain task. If you call /yardstick/testcases/samples/action API, it will return a task id. You can use the returned task id to get the results by using this API.


Get test results of one task
Example::

    http://localhost:8888/yardstick/results?task_id=3f3f5e03-972a-4847-a5f8-154f1b31db8c

This API will return a list of test case result
