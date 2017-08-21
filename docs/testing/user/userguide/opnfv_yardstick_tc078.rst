.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC078
*************************************

.. _spec_cpu2006: https://www.spec.org/cpu2006/

+-----------------------------------------------------------------------------+
|Compute Performance                                                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC078_SPEC CPU 2006                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | compute-intensive performance                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC078 is to evaluate the IaaS compute         |
|              | performance by using SPEC CPU 2006 benchmark. The SPEC CPU   |
|              | 2006 benchmark has several different ways to measure         |
|              | computer performance. One way is to measure how fast the     |
|              | computer completes a single task; this is called a speed     |
|              | measurement. Another way is to measure how many tasks        |
|              | computer can accomplish in a certain amount of time; this is |
|              | called a throughput, capacity or rate measurement.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | SPEC CPU 2006                                                |
|              |                                                              |
|              | The SPEC CPU 2006 benchmark is SPEC's industry-standardized, |
|              | CPU-intensive benchmark suite, stressing a system's          |
|              | processor, memory subsystem and compiler. This benchmark     |
|              | suite includes the SPECint benchmarks and the SPECfp         |
|              | benchmarks. The SPECint 2006 benchmark contains 12 different |
|              | enchmark tests and the SPECfp 2006 benchmark contains 19     |
|              | different benchmark tests.                                   |
|              |                                                              |
|              | SPEC CPU 2006 is not always part of a Linux distribution.    |
|              | SPEC requires that users purchase a license and agree with   |
|              | their terms and conditions. For this test case, users must   |
|              | manually download cpu2006-1.2.iso from the SPEC website and  |
|              | save it under the yardstick/resources folder (e.g. /home/    |
|              | opnfv/repos/yardstick/yardstick/resources/cpu2006-1.2.iso)   |
|              | SPEC CPU® 2006 benchmark is available for purchase via the   |
|              | SPEC order form (https://www.spec.org/order.html).           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | This test case uses SPEC CPU 2006 benchmark to measure       |
|description   | compute-intensive performance of hosts.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: spec_cpu.yaml (in the 'samples' directory)             |
|              |                                                              |
|              | benchmark_subset is set to int.                              |
|              |                                                              |
|              | SLA is not available in this test case.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * benchmark_subset - a subset of SPEC CPU2006 benchmarks to |
|              |    run;                                                      |
|              |  * SPECint_benchmark - a SPECint benchmark to run;           |
|              |  * SPECint_benchmark - a SPECfp benchmark to run;            |
|              |  * output_format - desired report format;                    |
|              |  * runspec_config - SPEC CPU2006 config file provided to the |
|              |    runspec binary;                                           |
|              |  * runspec_iterations - the number of benchmark iterations   |
|              |    to execute. For a reportable run, must be 3;              |
|              |  * runspec_tune - tuning to use (base, peak, or all). For a  |
|              |    reportable run, must be either base or all. Reportable    |
|              |    runs do base first, then (optionally) peak;               |
|              |  * runspec_size - size of input data to run (test, train, or |
|              |    ref). Reportable runs ensure that your binaries can       |
|              |    produce correct results with the test and train workloads |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|usability     | This test case is used for executing SPEC CPU 2006 benchmark |
|              | physical servers. The SPECint 2006 benchmark takes           |
|              | approximately 5 hours.                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | spec_cpu2006_                                                |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | To run and install SPEC CPU2006, the following are required: |
|conditions    |  * For SPECint2006: Both C99 and C++98 compilers;            |
|              |  * For SPECfp2006: All three of C99, C++98 and Fortran-95    |
|              |    compilers;                                                |
|              |  * At least 8GB of disk space availabile on the system.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | cpu2006-1.2.iso has been saved under the yardstick/resources |
|              | folder (e.g. /home/opnfv/repos/yardstick/yardstick/resources |
|              | /cpu2006-1.2.iso). Additional, to use your custom runspec    |
|              | config file you can save it under the yardstick/resources/   |
|              | files folder and specify the config file name in the         |
|              | runspec_config parameter.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Upload SPEC CPU2006 ISO to the target server and install     |
|              | SPEC CPU2006 via ansible.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Yardstick is connected with the target server by using ssh.  |
|              | If custom runspec config file is used, this file is copyied  |
|              | from yardstick to the target server via the ssh tunnel.      |
--------------+---------------------------------------------------------------+
|step 4        | SPEC CPU2006 benchmark is invoked and SPEC CPU 2006 metrics  |
|              | are generated.                                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | Text, HTML, CSV, PDF, and Configuration file outputs for the |
|              | SPEC CPU 2006 metrics are fetch from the server and stored   |
|              | under /tmp/result folder.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 6        | uninstall SPEC CPU2006 and remove cpu2006-1.2.iso from the   |
|              | target server .                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. SPEC CPU2006 results are collected and stored.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
