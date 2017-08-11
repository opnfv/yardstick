.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC079
*************************************

.. _bonnie++: http://www.coker.com.au/bonnie++/

+-----------------------------------------------------------------------------+
|Storage Performance                                                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC079_Bonnie++                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Sequential Input/Output and Sequential/Random Create speed   |
|              | and CPU useage.                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC078 is to evaluate the IaaS storage         |
|              | performance with regards to Sequential Input/Output and      |
|              | Sequential/Random Create speed and CPU useage statistics.    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Bonnie++                                                     |
|              |                                                              |
|              | Bonnie++ is a disk and file system benchmarking tool for     |
|              | measuring I/O performance. With Bonnie++ you can quickly and |
|              | easily produce a meaningful value to represent your current  |
|              | file system performance.                                     |
|              |                                                              |
|              | Bonnie++ is not always part of a Linux distribution, hence   |
|              | it needs to be installed in the test image.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | This test case uses Bonnie++ to perform the tests below:     |
|description   |  * Create files in sequential order                          |
|              |  * Stat files in sequential order                            |
|              |  * Delete files in sequential order                          |
|              |  * Create files in random order                              |
|              |  * Stat files in random order                                |
|              |  * Delete files in random order                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: bonnie++.yaml (in the 'samples' directory)             |
|              |                                                              |
|              | file_size is set to 1024; ram_size is set to 512;            |
|              | test_dir is set to '/tmp'; concurrency is set to 1.          |
|              |                                                              |
|              | SLA is not available in this test case.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * file_size - size fo the test file in MB. File size should |
|              |    be double RAM for good results;                           |
|              |  * ram_size - specify RAM size in MB to use, this is used to |
|              |    reduce testing time;                                      |
|              |  * test_dir - this directory is where bonnie++ will create   |
|              |    the benchmark operations;                                 |
|              |  * test_user - the user who should perform the test. This is |
|              |    not required if you are not running as root;              |
|              |  * concurrency - number of thread to perform test;           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|usability     | This test case is used for executing Bonnie++ benchmark in   |
|              | VMs.                                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | bonnie++_                                                    |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The Bonnie++ distribution includes a 'bon_csv2html' Perl     |
|conditions    | script, which takes the comma-separated values reported by   |
|              | Bonnie++ and generates an HTML page displaying them.         |
|              | To use this feature, bonnie++ is required to be install with |
|              | yardstick (e.g. in yardstick docker).                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | A host VM with fio installed is booted.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the host VM by using ssh.        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Bonnie++ benchmark is invoked. Simulated IO operations are   |
|              | started. Logs are produced and stored.                       |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | An HTML report is generated using bonnie++ benchmark results |
|              | and stored under /tmp/bonnie.html.                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | The host VM is deleted.                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. Bonnie++ html report is generated.                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
