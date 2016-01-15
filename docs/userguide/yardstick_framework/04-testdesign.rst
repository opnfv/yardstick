.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) 2015 Ericsson AB and others

.. _InfluxDB: https://docs.influxdata.com/influxdb/v0.9/write_protocols/line.html

===============
NFV test design
===============

This chapter mainly describes how to add new NFV test cases to Yardstick.

The relevant use cases will probably be either to reuse an existing test case
in a new test suite combination, or to make minor modifications to existing
YAML files, or to create new YAML files, or to create completely new test
cases and also new test types.


General
=======

- Reuse what already exists as much as possible.

- Adhere to the architecture of the existing design, such as using scenarios,
  runners and so on.

- Make sure any new code has enough test coverage. If the coverage is not good
  enough the build system will complain, see `NFV test case design`_ for more
  details.

- There should be no dependencies between different test scenarios. Scenarios
  should be possible to combine and run without dependencies between them,
  otherwise it will not be possible to keep the testing modular, neither be
  possible to run them each as single scenarios. It will in practice be harder
  to include and exclude test cases in any desirable order in all different
  test suites. Any exception should be documented in a test scenario that
  depends on another scenario.

- Any modifications made to the system under test by a test scenario should
  be cleaned up after the test is completed or aborted.

- Additions and changes should be documented.
  Remember not only pure coders/designers could be interested in getting a
  deeper understanding of Yardstick.


NFV test case design
====================

This chapter describes how to add a new test case type. For more limited
changes the scope of the test design would be reduced.

Scenario configuration
----------------------

A new test scenario type should be defined in a separate benchmark configuration
YAML file. Typically such includes Yardstick VM deployment configurations,
VM affinity rules, which images to run where, VM image login credentials,
test duration, optional test passing boundaries (SLA) and network configuration.
Depending on the nature of a new test type also other or new parameters may be
valid to add.

NFV scenario example from *ping.yaml*:
::

  ---
  # Sample benchmark task config file
  # measure network latency using ping

  schema: "yardstick:task:0.1"

  scenarios:
  -
    type: Ping
    options:
      packetsize: 200
    host: athena.demo
    target: ares.demo

    runner:
      type: Duration
      duration: 60
      interval: 1

    sla:
      max_rtt: 10
      action: monitor

  context:
    name: demo
    image: cirros-0.3.3
    flavor: m1.tiny
    user: cirros

    placement_groups:
      pgrp1:
        policy: "availability"

    servers:
      athena:
        floating_ip: true
        placement: "pgrp1"
      ares:
        placement: "pgrp1"

    networks:
      test:
        cidr: '10.0.1.0/24'


Test case coding
----------------

An actual NFV test case is realized by a test scenario Python file, or
files. The test class name should be the same as the test type name.
Typical class definitions are the init() and run() methods. Additional
support methods can also be added to the class.
Also a (simple) _test() design method can be added to the respective file.

A comment field describing the different valid input parameters in the
above YAML file should also be included, such as possible dependencies
parameter value boundaries and parameter defaults.

The Yardstick internal unit tests are located under *yardstick/tests/unit/*.
The unit tests are run at each Gerrit commit to verify correct behavior and
code coverage. They are also run when Yardstick is deployed onto an
environment/POD. At each new commit up to a total of 10 new lines of uncovered
code is accepted, otherwise the commit will be refused.

Example of NFV test case from *ping.py*:
::

  class Ping(base.Scenario):
      """Execute ping between two hosts

  Parameters
      packetsize - number of data bytes to send
          type:    int
          unit:    bytes
          default: 56
      """
   .
   .
   .
   def __init__(self, scenario_cfg, context_cfg):
       <Initialize test case, variables to use in run() method and so on>
   .
   .
   .
   def run(self, result):
       <Run the test, evaluate results and produce output>
   .
   .
   .


Example of internal test method of NFV test code from *ping.py*:
::

  def _test():
      """internal test function"""
       <Create the context and run test case>


Snippet of unit test code from *test_ping.py*:
::

  import mock
  import unittest

  from yardstick.benchmark.scenarios.networking import ping

  class PingTestCase(unittest.TestCase):

      def setUp(self):
          self.ctx = {
              'host': {
                  'ip': '172.16.0.137',
                  'user': 'cirros',
                  'key_filename': "mykey.key"
              },
              "target": {
                  "ipaddr": "10.229.17.105",
              }
          }

      @mock.patch('yardstick.benchmark.scenarios.networking.ping.ssh')
      def test_ping_successful_no_sla(self, mock_ssh):

          args = {
              'options': {'packetsize': 200},
              }
          result = {}

          p = ping.Ping(args, self.ctx)

          mock_ssh.SSH().execute.return_value = (0, '100', '')
          p.run(result)
          self.assertEqual(result, {'rtt': 100.0})
  .
  .
  .

  def main():
      unittest.main()

  if __name__ == '__main__':
      main()



The vTC part of Yardstick complies to its own testing and coverage rules,
see ApexLake_.


The Yardstick NFV test image
----------------------------

The Yardstick test/guest VM image, deployed onto the system under test and where
tests are executed from, must contain all the necessary tools for all supported
test cases (such as ping, perf, lmbench and so on). Hence, any required packages
in this dedicated Yardstick Ubuntu image should be added to the script that
builds it. See more information in :ref:`guest-image`.


NFV test case output
--------------------

Yardstick NFV test results are each output in JSON format.
These are by default dispatched to the file */tmp/yardstick.out*, which
is overwritten by each new test scenario. This is practical when doing test
design and local test verification, but not when releasing test scenarios for
public use and evaluation. For this purpose test output can be dispatched to
either a Yardstick internal *InfluxDB* database, and visualized by *Grafana*,
or to the official OPNFV *MongoDB* database which uses *Bitergia* as
visualization tool.

InfluxDB is populated by the dispatcher using an http line protocol specified
by InfluxDB_.

Set the *DISPATCHER_TYPE* parameter to chose where to dispatch all test result
output. It can be set to either *file*, *influxdb* or *http*. Default is
*file*.

Examples of which log dispatcher parameters to set:
::

  To file:
    DISPATCHER_TYPE=file
    DISPATCHER_FILE_NAME="/tmp/yardstick.out"

  To OPNFV MongoDB/Bitergia:
    DISPATCHER_TYPE=http
    DISPATCHER_HTTP_TARGET=http://130.211.154.108

  To Yardstick InfluxDB/Grafana:
    DISPATCHER_TYPE=influxdb
    DISPATCHER_INFLUXDB_TARGET=http://10.118.36.90


Before doing Gerrit commit
--------------------------

The script *run_tests.sh* in the top Yardstick directory must be run cleanly
through before doing a commit into Gerrit.


Continuous integration with Yardstick
-------------------------------------

Yardstick is part of daily and weekly continuous integration (CI) loops at
different OPNFV PODs. The POD integration is kept together via the OPNFV
Releng project, which uses Jenkins as the main tool for this activity.

The daily and weekly test suites have different timing constraints to align to.
Hence, Yardstick NFV test suite time boundaries should be kept in mind when
doing new test design or when doing modifications to existing test cases or
test suite configurations.

The daily test suites contain tests that are relatively fast to execute, and
provide enough results to have an enough certainty level that the complete
OPNFV deployment is not broken.

The weekly tests suites can run for longer than the daily test suites.
Test cases that need to run for longer and/or with more iterations and/or
granularity are included here, and run as complements to the daily test suites.

For the OPNFV R2 release a complete daily Yardstick test suite at a POD must
complete in approximately 3 hours, while a weekly test suite at a POD may run
for up to 24 hours until completion.

It should also be noted that since CI PODs can run either virtual or BM the
test suite for the respective POD must be planned and configured with
test scenarios suitable for the respective type of deployment. It is possible
to set a precondition statement in the test scenario if there are certain
requirements.

Example of a precondition configuration:
::

  precondition:
    installer_type: compass
    deploy_scenarios: os-nosdn

For further details on modifying test suites please consult the project.


Test case documentation
-----------------------

Each test case should be described in a separate file in reStructuredText
format. There is a template for this in the *docs* directory to guide you.
These documents must also be added to the build scripts to hint to the OPNFV
build system to generate appropriate html and pdf files out of them.
