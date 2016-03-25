.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) 2016 Huawei Technologies Co.,Ltd and others

============
Architecture
============

Abstract
========
This chapter describes the yardstick framework software architecture. we will introduce it from Use-Case View,
Logical View, Process View and Deployment View. More technical details will be introduced in this chapter.

Overview
========

Architecture overview
---------------------
Yardstick is mainly written in Python, and test configurations are made
in YAML. Documentation is written in reStructuredText format, i.e. .rst
files. Yardstick is inspired by Rally. Yardstick is intended to run on a
computer with access and credentials to a cloud. The test case is described
in a configuration file given as an argument.

How it works: the benchmark task configuration file is parsed and converted into
an internal model. The context part of the model is converted into a Heat
template and deployed into a stack. Each scenario is run using a runner, either
serially or in parallel. Each runner runs in its own subprocess executing
commands in a VM using SSH. The output of each scenario is written as json
records to a file or influxdb or http server, we use influxdb as the backend,
the test result will be shown with grafana.


Concept
-------
**Benchmark** - assess the relative performance of something

**Benchmark** configuration file - describes a single test case in yaml format

**Context** - The set of Cloud resources used by a scenario, such as user
names, image names, affinity rules and network configurations. A context is
converted into a simplified Heat template, which is used to deploy onto the
Openstack environment.

**Data** - Output produced by running a benchmark, written to a file in json format

**Runner** - Logic that determines how a test scenario is run and reported, for
example the number of test iterations, input value stepping and test duration.
Predefined runner types exist for re-usage, see `Runner types`_.

**Scenario** - Type/class of measurement for example Ping, Pktgen, (Iperf, LmBench, ...)

**SLA** - Relates to what result boundary a test case must meet to pass. For
example a latency limit, amount or ratio of lost packets and so on. Action
based on :term:`SLA` can be configured, either just to log (monitor) or to stop
further testing (assert). The :term:`SLA` criteria is set in the benchmark
configuration file and evaluated by the runner.


Runner types
------------

There exists several predefined runner types to choose between when designing
a test scenario:

**Arithmetic:**
Every test run arithmetically steps the specified input value(s) in the
test scenario, adding a value to the previous input value. It is also possible
to combine several input values for the same test case in different
combinations.

Snippet of an Arithmetic runner configuration:
::


  runner:
      type: Arithmetic
      iterators:
      -
        name: stride
        start: 64
        stop: 128
        step: 64

**Duration:**
The test runs for a specific period of time before completed.

Snippet of a Duration runner configuration:
::


  runner:
    type: Duration
    duration: 30

**Sequence:**
The test changes a specified input value to the scenario. The input values
to the sequence are specified in a list in the benchmark configuration file.

Snippet of a Sequence runner configuration:
::


  runner:
    type: Sequence
    scenario_option_name: packetsize
    sequence:
    - 100
    - 200
    - 250


**Iteration:**
Tests are run a specified number of times before completed.

Snippet of an Iteration runner configuration:
::


  runner:
    type: Iteration
    iterations: 2




Use-Case View
=============
Yardstick Use-Case View shows two kinds of users. One is the Tester who will
do testing in cloud, another is the User who is more concerned with test result
and result analyses.

For testers, they will run a single test case or test case suite to verify
infrastructure compliance or bencnmark their own infrastructure performance.
Test result will be stored by dispatcher module, three kinds of store method
(file, influxdb and http) can be configured. The detail information of
scenarios and runners can be queried with CLI by testers.

For users, they would check test result with four ways.

if dispatcher module is configured as file(default), there are two ways to
check test result. One is to get result from yardstick.out ( default path:
/tmp/yardstick.out), another is to get plot of test result, it will be shown
if users execute command "yardstick plot".

if dispatcher module is configured as influxdb, users could check test
result on Grafana which is most commonly used for visualizing time series data.

if dispatcher module is configured as http, users cloud check test result
on OPNFV testing dashboard which use MongoDB as backend.

.. image:: images/Use_case.png
   :width: 800px
   :alt: Yardstick Use-Case View

Logical View
============
Yardstick Logical View describes the most important classes, their
organization, and the most important use-case realizations.

Main classes:

**TaskCommands** - "yardstick task" subcommand handler.
**HeatContext** - Do test yaml file context section model convert to HOT,
deploy and undeploy Openstack heat stack.
**Runner** - Logic that determines how a test scenario is run and reported.
**TestScenario** - Type/class of measurement for example Ping, Pktgen, (Iperf,
LmBench, ...)
**Dispatcher** - Choose user defined way to store test results.

TaskCommands is the "yardstick task" subcommand's main enter, it takes
test.yaml as input, use HeatContext to convert the yaml file's context section
to HOT, to deploy Openstack heat stack with the converted HOT. After heat
stack is deployed, TaskCommands use Runner to run specified TestScenario.
During first runner initialization, it will create output process. The output
process use Dispatcher to push test results to the user defined place. The
Runner itself will also create a process to execute TestScenario. And there is
a multiprocessing queue between each runner and output process, so the runner
process can push the real-time test results to the storage media. TestScenario
commonly connect Openstack created VMs by using ssh, setup VMs and run test
measurement scripts through the created ssh tunnel. After all TestScenaio
is finished, TaskCommands will undeploy the heat stack.

.. image:: images/Logical_view.png
   :width: 800px
   :alt: Yardstick Logical View

Process View (Test execution flow)
==================================
TBD(Limingjiang)

Deployment View
===============
TBD(Patrick)












Yardstick Directory structure
=============================

**yardstick/** - Yardstick main directory.

*ci/* - Used for continuous integration of Yardstick at different PODs and
        with support for different installers.

*docs/* - All documentation is stored here, such as configuration guides,
          user guides and Yardstick descriptions.

*etc/* - Used for test cases requiring specific POD configurations.

*samples/* - VNF test case samples are stored here. These are only samples,
             and not run during VNF verification.

*tests/* - Here both Yardstick internal tests (*functional/* and *unit/*) as
           well as the test cases run to verify the VNFs (*opnfv/*) are stored.
           Also configurations of what to run daily and weekly at the different
           PODs is located here.

*tools/* - Various tools to run Yardstick. Currently contains how to
           create the yardstick-trusty-server image with the different tools
           that are needed from within the image.

*vTC/* - Contains the files for running the virtual Traffic Classifier tests.

*yardstick/* - Contains the internals of Yardstick: Runners, CLI parsing,
               authentication keys, plotting tools, database and so on.

