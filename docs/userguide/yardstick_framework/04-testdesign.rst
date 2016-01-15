===========
Test design
===========

This chapter describes in general how to add new test cases to Yardstick.

The relevant use cases will probably be either to reuse an existing test case
in a new test suite combination, or to make minor modifications to existing
YAML files, or to create new YAML files, or to create completely new test
cases and also new test types.


General guidelines
==================

- Reuse what already exists as much as possible.

- Adhere to the patterns of the existing design, such as using scenarios,
  runners and so on.

- Make sure any new code has enough test coverage. If the coverage is not good
  enough the build system will complain.

- There should be no dependencies between different test scenarios. Scenarios
  should be possible to combine without dependencies between them.

- Any modifications made to the system under test by a test scenario should
  be reset after the test is completed or aborted.

- Additions and changes should be documented in a suitable fashion.
  Remember not only pure coders/designers could be interested in getting a
  deeper understanding of Yardstick.


Test case design
================

This chapter describes how to add a new test case type. For more limited
changes the scope of the test design would be reduced.

Scenario configuration
----------------------

A new test scenario type should be defined in a separate YAML file. Typically
such includes Yardstick VM deployment configurations, VM affinity rules, which
images to run where, VM image login credentials, test duration, optional test
passing boundaries (SLA) and network configuration. Depending on the nature of
a new test type also other or new parameters may be valid to add.

There exists several predefined runner types to choose between when designing
a new test case:

**Arithmetic:**
Every test run arithmetically steps the specified input value(s) to the
test scenario, adding a value to the previous input value. It is also possible
to combine several named input values for the same test case in different
combinations.

**Duration:**
The test run is run a specific time before completed.

**Sequence:**
Every test run a specified input value to the scenario is changed. Each input
value in the sequence is specified in a list.

**Iteration:**
Tests are run a specified number of times before completed.


Test case coding
----------------

The actual test case is typically realized by a scenario Python file, or
files. The test class name should be the same as the test type name.
Typical class definitions are the init and run methods. Additional test
support methods can also be added to the class.
Also test methods should be added to the respective file for code coverage
purposes. These are used for internal Yardstick verification, and also run
when Yardstick is deployed onto an environment/POD.
A comment field describing the different valid input parameters in the
above YAML file, possible dependencies and parameter boundaries should also
be shortly described.

Test image
----------

The Yardstick test VM image where tests, deployed onto the system under test,
are run from must contain all the necessary tools for all supported test cases.
Hence, any missing packages in this dedicated Yardstick Ubuntu image should
be added to the script that builds it.

Test case output
----------------

Yardstick test output is by default sent to a file, /tmp/yardstick.out. This
file is overwritten by each new test run. This is practical when doing
test design and local test verification, but not when releasing test scenarios
for public use and evaluation. For this purpose test output can be routed to
either a Yardstick internal InfluxDB database, and visualized by Grafana, or
to the official OPNFV MongoDB database using Bitergia as visualization tool.

Daily and weekly builds
-----------------------

Test run time boundaries should be kept in mind when doing new test design,
or when doing modifications to existing configurations. The daily and weekly
test suites have timing constraints to align to. For further details on these
constraints please consult the project.

Test case documentation
-----------------------

Each test case should be described in a separate file in reStructuredText
format. There is a template for this in the *docs* directory to guide you.
These documents must also be added to the build scripts to hint to the build
system to generate appropriate html and pdf files out of them.
