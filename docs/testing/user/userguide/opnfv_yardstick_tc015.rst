.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Orange and others.

*************************************
Yardstick Test Case Description TC015
*************************************

.. _unixbench: https://github.com/kdlucas/byte-unixbench/blob/master/UnixBench

+-----------------------------------------------------------------------------+
| Processing speed with impact on energy consumption and CPU load             |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC015_PROCESSING SPEED                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | score of single cpu running,                                 |
|              | score of parallel running,                                   |
|              | energy consumption                                           |
|              | cpu load                                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC015 is to evaluate the IaaS compute         |
|              | performance with regards to CPU processing speed with        |
|              | its impact on the energy consumption                         |
|              | It measures score of single cpu running and parallel         |
|              | running. Energy consumption and cpu load are monitored while |
|              | the cpu test is running.                                     |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations,      |
|              | different server types.                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | UnixBench                                                    |
|              |                                                              |
|              | Unixbench is the most used CPU benchmarking software tool.   |
|              | It can measure the performance of bash scripts, CPUs in      |
|              | multithreading and single threading. It can also measure the |
|              | performance for parallel tasks. Also, specific disk IO for   |
|              | small and large files are performed. You can use it to       |
|              | measure either linux dedicated servers and linux vps         |
|              | servers, running CentOS, Debian, Ubuntu, Fedora and other    |
|              | distros.                                                     |
|              |                                                              |
|              | (UnixBench is not always part of a Linux distribution, hence |
|              | it needs to be installed. As an example see the              |
|              | /yardstick/tools/ directory for how to generate a Linux      |
|              | image with UnixBench included.)                              |
|              |                                                              |
|              | Redfish API                                                  |
|              | This HTTPS interface is provided by BMC of every telco grade |
|              | server. Is is a standard interface.                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | The UnixBench runs system benchmarks on a compute, getting   |
|description   | information on the CPUs in the system. If the system has     |
|              | more than one CPU, the tests will be run twice -- once with  |
|              | a single copy of each test running at once, and once with N  |
|              | N copies, where N is the number of CPUs.                     |
|              |                                                              |
|              | UnixBench will process a set of results from a single test   |
|              | by averaging the individual pass results into a single final |
|              | value.                                                       |
|              |                                                              |
|              | While the cpu test is running Energy scenario run in         |
|              | background to monitor the number of watt consumed by the     |
|              | compute server on the fly. The same is done using Cpuload    |
|              | scenario to monitor the overall percentage of CPU used on    |
|              | the fly. This enables to balance the CPU score with its      |
|              | impact on energy consumption. Synchronized measurements      |
|              | enables to look at any relation between CPU load and energy  |
|              | consumption.                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc015.yaml                             |
|              |                                                              |
|              | run_mode:                                                    |
|              |    Run Energy and Cpuload in background                      |
|              |    Run unixbench in quiet mode or verbose mode               |
|              |    test_type: dhry2reg, whetstone and so on                  |
|              |                                                              |
|              | Duration and Interval are set globally for Energy and        |
|              | Cpuload, aligned with duration of UnixBench test.            |
|              | SLA can be set for each scenario type. Default is NA.        |
|              | For SLA with single_score and parallel_score, both can be    |
|              | set by user, default is NA.                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test shall be applied to node context only                   |
|              | It can be configured with different:                         |
|              |                                                              |
|              |  * test types: dhry2reg, whetstone                           |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
|              | SLA (optional) : min_score: The minimun UnixBench score that |
|              | is accepted.                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|usability     | This test case is one of Yardstick's generic test. Thus it   |
|              | is runnable on most of the scenarios.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | unixbench_                                                   |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The target shall have unixbench installed on it.             |
|conditions    |                                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | Yardstick is connected with the target node using ssh.       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Energy and Cpuload are launched silently in background one   |
|              | after the other.                                             |
|              | Then UnixBench is invoked. All the tests are executed using  |
|              | the "Run" script in the top-level of UnixBench directory.    |
|              | The "Run" script will run a standard "index" test, and save  |
|              | the report in the "results" directory. Then the report is    |
|              | processed by "unixbench_benchmark" and checked against the   |
|              | SLA.                                                         |
|              | While unibench runs energy and cpu load are catched          |
|              | periodically according to interval value.                    |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
