.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC006
*************************************

.. _fio: http://bluestop.org/files/fio/HOWTO.txt

+-----------------------------------------------------------------------------+
|Volume storage Performance                                                   |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC006_VOLUME STORAGE PERFORMANCE             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | IOPS (Average IOs performed per second),                     |
|              | Throughput (Average disk read/write bandwidth rate),         |
|              | Latency (Average disk read/write latency)                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC006 is to evaluate the IaaS volume storage  |
|              | performance with regards to IOPS, throughput and latency.    |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | fio                                                          |
|              |                                                              |
|              | fio is an I/O tool meant to be used both for benchmark and   |
|              | stress/hardware verification. It has support for 19          |
|              | different types of I/O engines (sync, mmap, libaio,          |
|              | posixaio, SG v3, splice, null, network, syslet, guasi,       |
|              | solarisaio, and more), I/O priorities (for newer Linux       |
|              | kernels), rate I/O, forked or threaded jobs, and much more.  |
|              |                                                              |
|              | (fio is not always part of a Linux distribution, hence it    |
|              | needs to be installed. As an example see the                 |
|              | /yardstick/tools/ directory for how to generate a Linux      |
|              | image with fio included.)                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | fio test is invoked in a host VM with a volume attached on a |
|description   | compute blade, a job file as well as parameters are passed   |
|              | to fio and fio will start doing what the job file tells it   |
|              | to do.                                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc006.yaml                             |
|              |                                                              |
|              | Fio job file is provided to define the benchmark process     |
|              | Target volume is mounted at /FIO_Test directory              |
|              |                                                              |
|              | For SLA, minimum read/write iops is set to 100,              |
|              | minimum read/write throughput is set to 400 KB/s,            |
|              | and maximum read/write latency is set to 20000 usec.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | This test case can be configured with different:             |
|              |                                                              |
|              |   * Job file;                                                |
|              |   * Volume mount directory.                                  |
|              |                                                              |
|              | SLA is optional. The SLA in this test case serves as an      |
|              | example. Considerably higher throughput and lower latency    |
|              | are expected. However, to cover most configurations, both    |
|              | baremetal and fully virtualized  ones, this value should be  |
|              | possible to achieve and acceptable for black box testing.    |
|              | Many heavy IO applications start to suffer badly if the      |
|              | read/write bandwidths are lower than this.                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|usability     | This test case is one of Yardstick's generic test. Thus it   |
|              | is runnable on most of the scenarios.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | fio_                                                         |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with fio included in it.                                     |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | A host VM with fio installed is booted.                      |
|              | A 200G volume is attached to the host VM                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the host VM by using ssh.        |
|              | 'job_file.ini' is copyied from Jump Host to the host VM via  |
|              | the ssh tunnel. The attached volume is formated and mounted. |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Fio benchmark is invoked. Simulated IO operations are        |
|              | started. IOPS, disk read/write bandwidth and latency are     |
|              | recorded and checked against the SLA. Logs are produced and  |
|              | stored.                                                      |
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
