.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC014
*************************************

.. _unixbench: https://github.com/kdlucas/byte-unixbench/blob/master/UnixBench

+-----------------------------------------------------------------------------+
|Processing speed                                                             |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC014_PROCESSING SPEED                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | score of single cpu running,                                 |
|              | score of parallel running                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC014 is to evaluate the IaaS compute         |
|              | performance with regards to CPU processing speed.            |
|              | It measures score of single cpu running and parallel         |
|              | running.                                                     |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | UnixBench                                                    |
|              |                                                              |
|              | Unixbench is the most used CPU benchmarking software tool.   |
|              | It can measure the performance of bash scripts, CPUs in      |
|              | multithreading and single threading. It can also measure the |
|              | performance for parallel taks. Also, specific disk IO for    |
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
+--------------+--------------------------------------------------------------+
|test          | The UnixBench runs system benchmarks in a host VM on a       |
|description   | compute blade, getting information on the CPUs in the        |
|              | system. If the system has more than one CPU, the tests will  |
|              | be run twice -- once with a single copy of each test running |
|              | at once, and once with N copies, where N is the number of    |
|              | CPUs.                                                        |
|              |                                                              |
|              | UnixBench will processs a set of results from a single test  |
|              | by averaging the individal pass results into a single final  |
|              | value.                                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc014.yaml                             |
|              |                                                              |
|              | run_mode: Run unixbench in quiet mode or verbose mode        |
|              | test_type: dhry2reg, whetstone and so on                     |
|              |                                                              |
|              | For SLA with single_score and parallel_score, both can be    |
|              | set by user, default is NA.                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * test types;                                               |
|              |  * dhry2reg;                                                 |
|              |  * whetstone.                                                |
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
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with unixbench included in it.                               |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | A host VM with UnixBench installed is booted.                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the host VM by using ssh.        |
|              | "unixbench_benchmark" bash script is copied from Jump Host   |
|              | to the host VM via ssh tunnel.                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | UnixBench is invoked. All the tests are executed using the   |
|              | "Run" script in the top-level of UnixBench directory.        |
|              | The "Run" script will run a standard "index" test, and save  |
|              | the report in the "results" directory. Then the report is    |
|              | processed by "unixbench_benchmark" and checked againsted the |
|              | SLA.                                                         |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | The host VM is deleted.                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
