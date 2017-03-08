.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Intel Corporation and others.

*************************************
Yardstick Test Case Description TC006
*************************************

.. _DPDKpktgen: https://github.com/Pktgen/Pktgen-DPDK/
.. _rfc2544: https://www.ietf.org/rfc/rfc2544.txt

+-----------------------------------------------------------------------------+
|Network Performance                                                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC006_Virtual Traffic Classifier Data Plane  |
|              | Throughput Benchmarking Test.                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Throughput                                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To measure the throughput supported by the virtual Traffic   |
|              | Classifier according to the RFC2544 methodology for a        |
|              | user-defined set of vTC deployment configurations.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: file: opnfv_yardstick_tc006.yaml                       |
|              |                                                              |
|              | packet_size: size of the packets to be used during the       |
|              |      throughput calculation.                                 |
|              |      Allowe values: [64, 128, 256, 512, 1024, 1280, 1518]    |
|              |                                                              |
|              | vnic_type: type of VNIC to be used.                          |
|              |      Allowed values are:                                     |
|              |           - normal: for default OvS port configuration       |
|              |           - direct: for SR-IOV port configuration            |
|              |      Default value: None                                     |
|              |                                                              |
|              | vtc_flavor: OpenStack flavor to be used for the vTC          |
|              |      Default available values are: m1.small, m1.medium,      |
|              |      and m1.large, but the user can create his/her own       |
|              |      flavor and give it as input                             |
|              |      Default value: None                                     |
|              |                                                              |
|              | vlan_sender: vlan tag of the network on which the vTC will   |
|              |      receive traffic (VLAN Network 1).                       |
|              |      Allowed values: range (1, 4096)                         |
|              |                                                              |
|              | vlan_receiver: vlan tag of the network on which the vTC      |
|              |      will send traffic back to the packet generator          |
|              |      (VLAN Network 2).                                       |
|              |      Allowed values: range (1, 4096)                         |
|              |                                                              |
|              | default_net_name: neutron name of the defaul network that    |
|              |      is used for access to the internet from the vTC         |
|              |      (vNIC 1).                                               |
|              |                                                              |
|              | default_subnet_name: subnet name for vNIC1                   |
|              |      (information available through Neutron).                |
|              |                                                              |
|              | vlan_net_1_name: Neutron Name for VLAN Network 1             |
|              |      (information available through Neutron).                |
|              |                                                              |
|              | vlan_subnet_1_name: Subnet Neutron name for VLAN Network 1   |
|              |      (information available through Neutron).                |
|              |                                                              |
|              | vlan_net_2_name: Neutron Name for VLAN Network 2             |
|              |      (information available through Neutron).                |
|              |                                                              |
|              | vlan_subnet_2_name: Subnet Neutron name for VLAN Network 2   |
|              |      (information available through Neutron).                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | DPDK pktgen                                                  |
|              |                                                              |
|              | DPDK Pktgen is not part of a Linux distribution,             |
|              | hence it needs to be installed by the user.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | DPDK Pktgen: DPDKpktgen_                                     |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
|              | RFC 2544: rfc2544_                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different flavors, vNIC type     |
|              | and packet sizes. Default values exist as specified above.   |
|              | The vNIC type and flavor MUST be specified by the user.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The vTC has been successfully instantiated and configured.   |
|              | The user has correctly assigned the values to the deployment |
|              |  configuration parameters.                                   |
|              |                                                              |
|              | - Multicast traffic MUST be enabled on the network.          |
|              |      The Data network switches need to be configured in      |
|              |      order to manage multicast traffic.                      |
|              | - In the case of SR-IOV vNICs use, SR-IOV compatible NICs    |
|              |      must be used on the compute node.                       |
|              | - Yarsdtick needs to be installed on a host connected to the |
|              |      data network and the host must have 2 DPDK-compatible   |
|              |      NICs. Proper configuration of DPDK and DPDK pktgen is   |
|              |      required before to run the test case.                   |
|              |      (For further instructions please refer to the ApexLake  |
|              |      documentation).                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | Description and expected results                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step  1       | The vTC is deployed, according to the user-defined           |
|              | configuration                                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step  2       | The vTC is correctly deployed and configured as necessary    |
|              | The initialization script has been correctly executed and    |
|              | vTC is ready to receive and process the traffic.             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step  3       | Test case is executed with the selected parameters:          |
|              | - vTC flavor                                                 |
|              | - vNIC type                                                  |
|              | - packet size                                                |
|              | The traffic is sent to the vTC using the maximum available   |
|              | traffic rate for 60 seconds.                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | The vTC instance forwards all the packets back to the packet |
|              | generator for 60 seconds, as specified by RFC 2544.          |
|              |                                                              |
|              | Steps 3 and 4 are executed different times, with different   |
|              | rates in order to find the maximum supported traffic rate    |
|              | according to the current definition of throughput in RFC     |
|              | 2544.                                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  |  The result of the test is a number between 0 and 100 which  |
|              |  represents the throughput in terms of percentage of the     |
|              |  available pktgen NIC bandwidth.                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
