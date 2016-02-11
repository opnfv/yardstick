.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) 2015 Ericsson AB and others

============
Architecture
============

Overview
========

Apart from a testing framework Yardstick also comes with default
configured test cases, test suites and test sample cases. These can be
picked and chosen from, and also modified to fit specific use cases.

Included is documentation describing how to install Yardstick on to
different deployment configurations, see :doc:`03-installation`, how to
run individual test cases and test suites and how to design new test cases,
see :doc:`testdesign`.

Yardstick is mainly written in Python, and test configurations are made
in YAML. Documentation is written in reStructuredText format, i.e. .rst
files.

The Yardstick environment is mainly intended to be installed via
a container framework, but it is also possible to install Yardstick
directly as well, see :doc:`03-installation`.

The Yardstick framework can be installed either on bare metal or on
virtualized deployments see `Virtual and bare metal deployments`_.
Yardstick supports bare metal environments to be able to test things that
are not possible to test on virtualized environments.

Typical test execution is done by deploying one or several :term:`VM`:s on to
the :term:`NFVI` invoking the tests from there, see `Test execution flow`_.

Yardstick can be run on its own on top of a deployed :term:`NFVI`,
which is mainly how it is run inside the OPNFV community labs in regular
daily and weekly OPNFV builds. It can also run in parallel to a deployed
:term:`VNF`.

All of the tools used by and included in Yardstick are open source, also the
tools developed by the Yardstick project.


Virtual and bare metal deployments
==================================

Yardstick tests can be deployed either on virtualized or on bare metal
(:term:`BM`) environments. For some type of tests a virtualized system under
test (:term:`SUT`) may not be suitable.

A :term:`BM` deployment means that the OpenStack controllers and computes run
on :term:`BM`, directly on top of dedicated HW, i.e. non-virtualized. Hence, a
virtualized deployment means that the OpenStack controllers and computes run
virtualized, as :term:`VM`:s.

The Cloud system installer is a separate function, but that too can run
either virtualized or :term:`BM`.

The most common practice on the different Yardstick PODs is to have :term:`BM`
Cloud deployments, with the installer running virtualized on the POD's jump
server. The virtualized deployment practice is more common in smaller test
design environments.

The Yardstick logic normally runs outside the :term:`SUT`, on a separate
server, either as :term:`BM` or deployed within a separate Yardstick container.

Yardstick must have access privileges to the OpenStack :term:`SUT` to be able
to set up the :term:`SUT` environment and to (optionally) deploy any images
into the :term:`SUT` to execute the tests scenarios from.

Yardstick tests are run as if run as a :term:`VNF`, as one or several compute
:term:`VM`:s. Hence, the software maintained by and deployed by Yardstick on the
:term:`SUT` to execute the tests from is always run virtualized.


Concepts
========

Below is a list of common Yardstick concepts and a short description of each.

**Benchmark configuration file** - Describes a single test case in YAML format.

**Context** - The set of Cloud resources used by a scenario, such as user
names, image names, affinity rules and network configurations. A context is
converted into a simplified Heat template, which is used to deploy onto the
Openstack environment.

**Runner** - Logic that determines how a test scenario is run and reported, for
example the number of test iterations, input value stepping and test duration.
Predefined runner types exist for re-usage, see `Runner types`_.

**Scenario** - The overall test management of the runners.

**SLA** - Relates to what result boundary a test case must meet to pass. For
example a latency limit, amount or ratio of lost packets and so on. Action
based on :term:`SLA` can be configured, either just to log (monitor) or to stop
further testing (assert). The :term:`SLA` criteria is set in the benchmark
configuration file and evaluated by the runner.

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



Test execution flow
===================

As described earlier the Yardstick engine and central logic should be run
on a computer from outside the :term:`SUT`, on where the actual testing is
executed. This is where the benchmark configuration YAML-file is parsed when
invoking the Yardstick task shell command.
For instance in the continuous integration activities of a POD Yardstick
typically runs on the combined jump and Jenkins server of the respective POD.

The benchmark configuration YAML-file (the test case) is parsed by the
Yardstick task shell command. Its context part is then converted into a Heat
template and deployed into the stack (in OpenStack) of the :term:`SUT`. This
includes for instance :term:`VM` deployment, network, and authentication
configuration. Once the context is up an running on Openstack it is
orchestrated by a Yardstick runner to run the tests of the :term:`SUT`.

The Yardstick runner(s) is also created when the Yardstick task command is
parsed. A runner runs in its own Yardstick subprocess executing commands
remotely into a (context) :term:`VM` using SSH, for example invoking ping from
inside the deployed :term:`VM` acting as the :term:`VNF` application.
While the test runs the output of the SSH commands is collected by the runner
and written as JSON records to a file that is output into either a file
(/tmp/yardstick.out by default), or in the case of running in a POD into a
database instead.

When a test case is finished everything is cleaned out on the :term:`SUT` to
prepare for the next test case. A manually aborted test case is also cleaned
out.


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
