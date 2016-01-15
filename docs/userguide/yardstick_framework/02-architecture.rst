.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) 2015 Ericsson AB and others

============
Architecture
============

Concepts
========

Below is a list of common Yardstick concepts and a short description of each.

**Benchmark configuration file** - Describes a single test case in YAML format.

**Context** - The set of Cloud resources used by a scenario, such as user names,
image names, affinity rules and network configurations. A context is converted
into a simplified Heat template, which is used to deploy the Openstack
environment.

**Runner** - Logic that determines how a test scenario is run, for example the
number of test iterations, input value stepping and test duration. Predefined
runner types exist for re-usage, see `Runner types`_.

**Scenario** - Type of measurement (the tool), such as Ping, Pktgen, Iperf,
LmBench and Fio. Runners are part of a scenario, as well as specific test
options settings and SLA configuration.

**SLA** - Relates to what result boundary a test case must meet to pass. For
example a latency limit, amount or ratio of lost packets and so on. Action
based on SLA can be configured, either just to log (monitor) or to stop further
testing (assert)

::


  +--------------------------------+  ^
  | Benchmark                      |  |
  |                                |  |
  | +----------+ 1   1 +---------+ |  |
  | | Scenario | ----- | Context | |  | **Benchmark**
  | +----------+       +---------+ |  | **configuration**
  |   |1                           |  | **file content**
  |   |                            |  | **and relationships**
  |   |n                           |  |
  | +--------+                     |  |
  | | Runner |+                    |  |
  | +--------+|+                   |  |
  |  +--------+|                   |  |
  |   +--------+                   |  |
  +--------------------------------+  v


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


Virtual and bare metal deployments
==================================

Yardstick tests can be deployed either on virtualized or on bare metal (BM)
environments. For some type of tests a virtualized system under test (SUT)
may not be suitable.

A BM deployment means that the OpenStack controllers and computes run on BM,
directly on top of dedicated HW, i.e. non-virtualized. Hence, a virtualized
deployment means that the OpenStack controllers and computes run virtualized,
as VMs.

The Cloud system installer is a separate function, but that too can run
either virtualized or BM.

The most common practice on the different Yardstick PODs is to have BM
Cloud deployments, with the installer running virtualized on the POD's jump
server. The virtualized deployment practice is more common in smaller test
design environments.

The Yardstick logic normally runs outside the SUT, on a separate server,
either as BM or deployed within a separate Yardstick container.

Yardstick must have access privileges to the OpenStack SUT to be able to set
up the SUT environment and to (optionally) deploy any images into the SUT
to execute the tests scenarios from.

Yardstick tests are run as if run as a VNF, as one or several compute VMs.
Hence, the software maintained by and deployed by Yardstick on the SUT to
execute the tests from is always run virtualized.


Test execution flow
===================

As described earlier the Yardstick engine and central logic should be run
on a computer from outside the SUT, where the actual testing is executed.
For instance in the continuous integration activities of a POD Yardstick
typically runs on the combined jump and Jenkins server of the respective POD.

Each benchmark configuration YAML-file (the test case) is parsed and converted
into a Yardstick-internal model. When the test case is invoked (i.e. when a
task is started) then first the context part of the model is converted
into a Heat template and deployed into the stack (in OpenStack) of the SUT.
This includes for instance VM deployment, network configuration and user
authentication. Once the context is up an running the scenario is orchestrated
from a Yardstick runner, either serially or in parallel, or a combination of
both.

Each runner runs in its own subprocess executing commands in a VM using SSH,
for example invoking ping from inside the VM acting as the VNF application.
The output of each command is written as JSON records to a file that is output
into either a file (/tmp/yardstick.out by default), or in the case of running
in a POD into a database instead.

When a test case is finished everything is cleaned out on the SUT to prepare
for the next test case. A manually aborted test case is also cleaned out.


Directory structure
===================

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
