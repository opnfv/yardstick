.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC084
*************************************

.. _spec_cpu_2006: https://www.spec.org/cpu2006/

+-----------------------------------------------------------------------------+
|Compute Performance                                                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC084_SPEC CPU 2006 FOR VM                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | compute-intensive performance                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC084 is to evaluate the IaaS compute         |
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
|              | benchmark tests and the SPECfp 2006 benchmark contains 19    |
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
|description   | compute-intensive performance of VMs.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc084.yaml                             |
|              |                                                              |
|              | benchmark_subset is set to int.                              |
|              |                                                              |
|              | SLA is not available in this test case.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * benchmark_subset - a subset of SPEC CPU 2006 benchmarks   |
|              |    to run;                                                   |
|              |  * SPECint_benchmark - a SPECint benchmark to run;           |
|              |  * SPECint_benchmark - a SPECfp benchmark to run;            |
|              |  * output_format - desired report format;                    |
|              |  * runspec_config - SPEC CPU 2006 config file provided to    |
|              |    the runspec binary;                                       |
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
|              | on virtual machines. The SPECint 2006 benchmark takes        |
|              | approximately 5 hours. (The time may vary due to different   |
|              | VM cpu configurations)                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | spec_cpu_2006_                                               |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | To run and install SPEC CPU 2006, the following are          |
|conditions    | required:                                                    |
|              |  * For SPECint 2006: Both C99 and C++98 compilers are        |
|              |    installed in VM images;                                   |
|              |  * For SPECfp 2006: All three of C99, C++98 and Fortran-95   |
|              |    compilers installed in VM images;                         |
|              |  * At least 4GB of disk space availabile on VM.              |
|              |                                                              |
|              |  gcc 4.8.* and g++ 4.8.* version have been tested in Ubuntu  |
|              |  14.04, Ubuntu 16.04 and Redhat Enterprise Linux 7.4 image.  |
|              |  Higher gcc and g++ version may cause compiling error.       |
|              |                                                              |
|              |  For more SPEC CPU 2006 dependencies please visit            |
|              |  (https://www.spec.org/cpu2006/Docs/techsupport.html)        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | cpu2006-1.2.iso has been saved under the yardstick/resources |
|              | folder (e.g. /home/opnfv/repos/yardstick/yardstick/resources |
|              | /cpu2006-1.2.iso). Additionally, to use your custom runspec  |
|              | config file you can save it under the yardstick/resources/   |
|              | files folder and specify the config file name in the         |
|              | runspec_config parameter.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Upload SPEC CPU 2006 ISO to the target VM using scp and      |
|              | install SPEC CPU 2006.                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Connect to the target server using SSH.                      |
|              | If custom runspec config file is used, copy this file from   |
|              | yardstick to the target VM via the SSH tunnel.               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | SPEC CPU 2006 benchmark is invoked and SPEC CPU 2006 metrics |
|              | are generated.                                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | Text, HTML, CSV, PDF, and Configuration file outputs for the |
|              | SPEC CPU 2006 metrics are fetched from the VM and stored     |
|              | under /tmp/result folder.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. SPEC CPU 2006 results are collected and stored.        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
