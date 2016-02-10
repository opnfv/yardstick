.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Intel Corporation and others.

*************************************
Yardstick Test Case Description TC021
*************************************

.. _DPDKpktgen: https://github.com/Pktgen/Pktgen-DPDK/
.. _rfc2544: https://www.ietf.org/rfc/rfc2544.txt

+-----------------------------------------------------------------------------+
|Network Performance                                                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC0021_Virtual Traffic Classifier            |
|              | Instantiation Test in Presence of Noisy Neighbours           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Failure                                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To verify that a newly instantiated vTC is 'alive' and       |
|              | functional and its instantiation is correctly supported by   |
|              | the infrastructure in the presence of noisy neighbours.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc021.yaml                             |
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
|              | num_of_neighbours: Number of noisy neighbours (VMs) to be    |
|              |     instantiated during the experiment.                      |
|              |     Allowed values: range (1, 10)                            |
|              |                                                              |
|              | amount_of_ram: RAM to be used by each neighbor.              |
|              |     Allowed values: ['250M', '1G', '2G', '3G', '4G', '5G',   |
|              |                      '6G', '7G', '8G', '9G', '10G']          |
|              |     Deault value: 256M                                       |
|              |                                                              |
|              | number_of_cores: Number of noisy neighbours (VMs) to be      |
|              |     instantiated during the experiment.                      |
|              |     Allowed values: range (1, 10)                            |
|              |     Default value: 1                                         |
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
|references    | DPDK Pktgen: DPDK Pktgen: DPDKpktgen_                        |
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
|              |      Installation and configuration of smcroute is required  |
|              |      before to run the test case.                            |
|              |      (For further instructions please refer to the ApexLake  |
|              |      documentation).                                         |
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
|step 1        | The noisy neighbours are deployed as required by the user.   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | The vTC is deployed, according to the configuration provided |
|              | by the user.                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | The vTC is correctly deployed and configured as necessary.   |
|              | The initialization script has been correctly executed and    |
|              | the vTC is ready to receive and process the traffic.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | Test case is executed with the selected parameters:          |
|              | - vTC flavor                                                 |
|              | - vNIC type                                                  |
|              | A constant rate traffic is sent to the vTC for 10 seconds.   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | The vTC instance tags all the packets and sends them back to |
|              | the packet generator for 10 seconds.                         |
|              |                                                              |
|              | The framework checks if the packet generator receives back   |
|              | all the packets with the correct tag from the vTC.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  |  The vTC is deemed to be successfully instantiated if all    |
|              |  packets are sent back with the right tag as requested,      |
|              |  else it is deemed DoA (Dead on arrival)                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
