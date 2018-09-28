.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) 2018 Viosoft Corporation.

**********************************************
Yardstick Test Case Description: NSB VIMS
**********************************************

+-----------------------------------------------------------------------------+
|NSB VIMS test for vIMS characterization                                      |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | tc_vims_{context}_sipp                                       |
|              |                                                              |
|              | * context = baremetal or heat;                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | * Successful registration per second;                        |
|              | * Total number of active registration per server;            |
|              | * Successful de-registrations per second;                    |
|              | * Successful sessions establishment per second;              |
|              | * Total number of active sessions per server;                |
|              | * Mean session setup time originated;                        |
|              | * Successful re-registration per second;                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The vIMS test handles registration rate, call rate,          |
|              | round trip delay, and message statistics of vIMS system.     |
|              |                                                              |
|              | The vIMS test cases are implemented to run in baremetal      |
|              | and heat context default configuration.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | The vIMS test cases are listed below:                        |
|              |                                                              |
|              | * tc_vims_baremetal.yaml                                     |
|              | * tc_vims_heat.yaml                                          |
|              |                                                              |
|              | Each test runs one time and collects all the KPIs.           |
|              | The configure of vIMS and SIPp can be changed in each test.  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | SIPp                                                         |
|              |                                                              |
|              | SIPp is a application that can simulate SIP scenarios        |
|              | and can generate RTP traffic and used for vIMS               |
|              | characterization                                             |
+--------------+--------------------------------------------------------------+
|applicability | The SIPp test cases can be configured with different:        |
|              |                                                              |
|              | * number of user;                                            |
|              | * initial rate of SIP test;                                  |
|              | * test durations;                                            |
|              | * RTP configure;                                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | For Openstack test case, only vIMS is deployed by external   |
|conditions    | heat template, SIPp needs pod.yaml file with the necessary   |
|              | system and NIC information                                   |
|              |                                                              |
|              | For Baremetal tests cases SIPp and vIMS must be installed in |
|              | the hosts where the test is executed. The pod.yaml file must |
|              | have the necessary system and NIC information                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | For Baremetal test: The TG and VNF are started on the hosts  |
|              | based on the pod file.                                       |
|              |                                                              |
|              | For Heat test: One host VM for vIMS is booted, based on      |
|              | the test flavor. Another host for SIPp is booted as          |
|              | traffic generator, based on pod.yaml file                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the vIMS and SIPp by using ssh.  |
|              | The test will resolve the topology and instantiate the vIMS  |
|              | and SIPp and collect the KPIs/metrics.                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | The SIPp will run scenario tests with parameters are         |
|              | configured in test case files (tc_baremetal_vims.yaml        |
|              | and tc_heat_vims.yaml files).                                |
|              | This is done until the KPIs of SIPp are within an acceptable |
|              | threshold.                                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | In Baremetal test: The test quits the application.           |
|              |                                                              |
|              | In Heat test: The host VM of vIMS is deleted on test         |
|              | completion.                                                  |
+--------------+--------------------------------------------------------------+
|test verdict  | The test case will achieve the KPIs and plot on Grafana.     |
+--------------+--------------------------------------------------------------+

