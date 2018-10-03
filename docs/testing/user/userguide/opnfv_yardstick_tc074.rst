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
|test purpose  | To evaluate and report on the Cinder volume performance.     |
|              |                                                              |
|              | This testcase integrates with OPNFV StorPerf to measure      |
|              | block performance of the underlying Cinder drivers.  Many    |
|              | options are supported, and even the root disk (Glance        |
|              | ephemeral storage can be profiled.                           |
|              |                                                              |
|              | The fundamental concept of the test case is to first fill    |
|              | the volumes with random data to ensure reported metrics      |
|              | are indicative of continued usage and not skewed by          |
|              | transitional performance while the underlying storage        |
|              | driver allocates blocks.                                     |
|              | The metrics for filling the volumes with random data         |
|              | are not reported in the final results.  The test also        |
|              | ensures the volumes are performing at a consistent level     |
|              | of performance by measuring metrics every minute, and        |
|              | comparing the trend of the metrics over the run.  By         |
|              | evaluating the min and max values, as well as the slope of   |
|              | the trend, it can make the determination that the metrics    |
|              | are stable, and not fluctuating beyond industry standard     |
|              | norms.                                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc074.yaml                             |
|              |                                                              |
|              | * agent_count: 1 - the number of VMs to be created           |
|              | * agent_image: "Ubuntu-14.04" - image used for creating VMs  |
|              | * public_network: "ext-net" - name of public network         |
|              | * volume_size: 2 - cinder volume size                        |
|              | * block_sizes: "4096" - data block size                      |
|              | * queue_depths: "4" - the number of simultaneous I/Os        |
|              |   to perform at all times                                    |
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
|              | https://hub.docker.com/r/opnfv/storperf-master/tags/.        |
|              |                                                              |
|              | The underlying tool used is FIO, and StorPerf supports       |
|              | any FIO option in order to tailor the test to the exact      |
|              | workload needed.                                             |
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
|              |                                                              |
|              |      - rs: 100% Read, sequential data                        |
|              |      - ws: 100% Write, sequential data                       |
|              |      - rr: 100% Read, random access                          |
|              |      - wr: 100% Write, random access                         |
|              |      - rw: 70% Read / 30% write, random access               |
|              |                                                              |
|              |   measurements.                                              |
|              |                                                              |
|              | * workloads={json maps}                                      |
|              |   This parameter supercedes the workload and calls the V2.0  |
|              |   API in StorPerf. It allows for greater control of the      |
|              |   parameters to be passed to FIO.  For example, running a    |
|              |   random read/write with a mix of 90% read and 10% write     |
|              |   would be expressed as follows:                             |
|              |   {"9010randrw": {"rw":"randrw","rwmixread": "90"}}          |
|              |   Note: This must be passed in as a string, so don't forget  |
|              |   to escape or otherwise properly deal with the quotes.      |
|              |                                                              |
|              | * report= [job_id]                                           |
|              |   Query the status of the supplied job_id and report on      |
|              |   metrics. If a workload is supplied, will report on only    |
|              |   that subset.                                               |
|              |                                                              |
|              |   There are default values for each above-mentioned option.  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | If you do not have an Ubuntu 14.04 image in Glance, you will |
|conditions    | need to add one.                                             |
|              |                                                              |
|              | Storperf is required to be installed in the environment.     |
|              | There are two possible methods for Storperf installation:    |
|              |                                                              |
|              |     - Run container on Jump Host                             |
|              |     - Run container in a VM                                  |
|              |                                                              |
|              | Running StorPerf on Jump Host                                |
|              | Requirements:                                                |
|              |                                                              |
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
|              |                                                              |
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
|step 1        | Yardstick calls StorPerf to create the heat stack with the   |
|              | number of VMs and size of Cinder volumes specified.  The     |
|              | VMs will be on their own private subnet, and take floating   |
|              | IP addresses from the specified public network.              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick calls StorPerf to fill all the volumes with        |
|              | random data.                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Yardstick calls StorPerf to perform the series of tests      |
|              | specified by the workload, queue depths and block sizes.     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | Yardstick calls StorPerf to delete the stack it created.     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. Storage performance results are fetched and stored.    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
