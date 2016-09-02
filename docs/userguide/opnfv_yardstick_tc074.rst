.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC074
*************************************

.. _Storperf: https://wiki.opnfv.org/display/storperf/Storperf

+-----------------------------------------------------------------------------+
|Storperf                                                                     |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC074_Storperf                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Storage performance                                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | Storperf integration with yardstick. The purpose of StorPerf |
|              | is to provide a tool to measure block and object storage     |
|              | performance in an NFVI. When complemented with a             |
|              | characterization of typical VF storage performance           |
|              | requirements, it can provide pass/fail thresholds for test,  |
|              | staging, and production NFVI environments.                   |
|              |                                                              |
|              | The benchmarks developed for block and object storage will   |
|              | be sufficiently varied to provide a good preview of expected |
|              | storage performance behavior for any type of VNF workload.   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc074.yaml                             |
|              |                                                              |
|              | * agent_count: 1 - the number of VMs to be created           |
|              | * agent_image: "Ubuntu-14.04" - image used for creating VMs  |
|              | * public_network: "ext-net" - name of public network         |
|              | * volume_size: 2 - cinder volume size                        |
|              | * block_sizes: "4096" - data block size                      |
|              | * queue_depths: "4"                                          |
|              | * StorPerf_ip: "192.168.200.2"                               |
|              | * query_interval: 10 - state query interval                  |
|              | * timeout: 600 - maximum allowed job time                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Storperf_                                                    |
|              |                                                              |
|              | StorPerf is a tool to measure block and object storage       |
|              | performance in an NFVI.                                      |
|              |                                                              |
|              | StorPerf is delivered as a Docker container from             |
|              | https://hub.docker.com/r/opnfv/storperf/tags/.               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | Storperf_                                                    |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              | * agent_count                                                |
|              | * volume_size                                                |
|              | * block_sizes                                                |
|              | * queue_depths                                               |
|              | * query_interval                                             |
|              | * timeout                                                    |
|              | * target=[device or path]                                    |
|              |   The path to either an attached storage device              |
|              |   (/dev/vdb, etc) or a directory path  (/opt/storperf) that  |
|              |   will be used to execute the performance test. In the case  |
|              |   of a device, the entire device will be used. If not        |
|              |   specified, the current directory will be used.             |
|              | * workload=[workload module]                                 |
|              |   If not specified, the default is to run all workloads. The |
|              |   workload types are:                                        |
|              |      - rs: 100% Read, sequential data                        |
|              |      - ws: 100% Write, sequential data                       |
|              |      - rr: 100% Read, random access                          |
|              |      - wr: 100% Write, random access                         |
|              |      - rw: 70% Read / 30% write, random access               |
|              | * nossd: Do not perform SSD style preconditioning.           |
|              | * nowarm:  Do not perform a warmup prior to                  |
|              |   measurements.                                              |
|              | * report= [job_id]                                           |
|              |   Query the status of the supplied job_id and report on      |
|              |   metrics. If a workload is supplied, will report on only    |
|              |   that subset.                                               |
|              |                                                              |
|              |   There are default values for each above-mentioned option.  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | If you do not have an Ubuntu 14.04 image in Glance, you will |
|conditions    | need to add one. A key pair for launching agents is also     |
|              | required.                                                    |
|              |                                                              |
|              | Storperf is required to be installed in the environment.     |
|              | There are two possible methods for Storperf installation:    |
|              |     Run container on Jump Host                               |
|              |     Run container in a VM                                    |
|              |                                                              |
|              | Running StorPerf on Jump Host                                |
|              | Requirements:                                                |
|              |     - Docker must be installed                               |
|              |     - Jump Host must have access to the OpenStack Controller |
|              |       API                                                    |
|              |     - Jump Host must have internet connectivity for          |
|              |       downloading docker image                               |
|              |     - Enough floating IPs must be available to match your    |
|              |       agent count                                            |
|              |                                                              |
|              | Running StorPerf in a VM                                     |
|              | Requirements:                                                |
|              |     - VM has docker installed                                |
|              |     - VM has OpenStack Controller credentials and can        |
|              |       communicate with the Controller API                    |
|              |     - VM has internet connectivity for downloading the       |
|              |       docker image                                           |
|              |     - Enough floating IPs must be available to match your    |
|              |       agent count                                            |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The Storperf is installed and Ubuntu 14.04 image is stored   |
|              | in glance. TC is invoked and logs are produced and stored.   |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. Storage performance results are fetched and stored.    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
