.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2019 Viosoft Corporation.

***********************************************
Yardstick Test Case Description: NSB vCMTS
***********************************************

+------------------------------------------------------------------------------+
|NSB Pktgen test for vCMTS characterization                                    |
|                                                                              |
+--------------+---------------------------------------------------------------+
|test case id  | tc_vcmts_k8s_pktgen                                           |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|metric        | * Upstream Processing (Per Service Group);                    |
|              | * Downstream Processing (Per Service Group);                  |
|              | * Upstream Throughput;                                        |
|              | * Downstream Throughput;                                      |
|              | * Platform Metrics;                                           |
|              | * Power Consumption;                                          |
|              | * Upstream Throughput Time Series;                            |
|              | * Downstream Throughput Time Series;                          |
|              | * System Summary;                                             |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|test purpose  | * The vCMTS test handles service groups and packet generation |
|              |   containers setup, and metrics collection.                   |
|              |                                                               |
|              | * The vCMTS test case is implemented to run in Kubernetes     |
|              |   environment with vCMTS pre-installed.                       |
+--------------+---------------------------------------------------------------+
|configuration | The vCMTS test case configurable values are listed below      |
|              |                                                               |
|              | * num_sg: Number of service groups (Upstream/Downstream       |
|              |           container pairs).                                   |
|              | * num_tg: Number of Pktgen containers.                        |
|              | * vcmtsd_image: vCMTS container image (feat/perf).            |
|              | * qat_on: QAT status (true/false).                            |
|              |                                                               |
|              | num_sg and num_tg values should be configured in the test     |
|              | case file and in the topology file.                           |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|test tool     | Intel vCMTS Reference Dataplane                               |
|              | Reference implementation of a DPDK-based vCMTS (DOCSIS MAC)   |
|              | dataplane in a Kubernetes-orchestrated Linux Container        |
|              | environment.                                                  |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|applicability | This test cases can be configured with different:             |
|              |                                                               |
|              | * Number of service groups                                    |
|              | * Number of Pktgen instances                                  |
|              | * QAT offloading                                              |
|              | * Feat/Perf Images for performance or features (more data     |
|              |   collection)                                                 |
|              |                                                               |
|              | Default values exist.                                         |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|pre-test      | Intel vCMTS Reference Dataplane should be installed and       |
|conditions    | runnable on 2 nodes Kubernetes environment with modifications |
|              | to the containers to allow yardstick ssh access, and the      |
|              | ConfigMaps from the original vCMTS package deployed.          |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|test sequence | description and expected result                               |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|step 1        | Yardstick is connected to the Kubernetes Master node using    |
|              | the configuration file in /etc/kubernetes/admin.yaml          |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|step 2        | The TG containers are created and started on the traffic      |
|              | generator server (Master node), While the VNF containers are  |
|              | created and started on the data plan server.                  |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|step 3        | Yardstick is connected with the TG and VNF by using ssh.      |
|              | to start vCMTS-d, and Pktgen.                                 |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|step 4        | Yardstick connects to the running Pktgen instances to start   |
|              | generating traffic using the configurations from:             |
|              |  /etc/yardstick/pktgen_values.yaml                            |
|              |                                                               |
|              | and connects to the vCMTS-d containers to start the upstream  |
|              | and downstream processing using the configurations from:      |
|              |  /etc/yardstick/vcmtsd_values.yaml                            |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|step 5        | Yardstick copies the collected data regularly the data from   |
|              | the remote InfluxDB to the local InfluxDB as configured in    |
|              | the options section in the test case file.                    |
|              |                                                               |
+--------------+---------------------------------------------------------------+
|test verdict  | None. The test case will collect the KPIs and plot on         |
|              | Grafana.                                                      |
+--------------+---------------------------------------------------------------+