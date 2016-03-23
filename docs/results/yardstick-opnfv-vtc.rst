.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0

.. _Dashboard006: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-tc006
.. _Dashboard007: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-tc007
.. _Dashboard020: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-tc020
.. _Dashboard021: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-tc021

====================================
Test Results for yardstick-opnfv-vtc
====================================

.. toctree::
   :maxdepth: 2


Details
=======

.. after this doc is filled, remove all comments and include the scenario in
.. results.rst by removing the comment on the file name.


Overview of test results
------------------------

.. general on metrics collected, number of iterations

The virtual Traffic Classifier (vtc) Scenario supported by Yardstick is used by 4 Test Cases:

- TC006
- TC007
- TC020
- TC021


* TC006

TC006 is the Virtual Traffic Classifier Data Plane Throughput Benchmarking Test.
It collects measures about the end-to-end throughput supported by the
virtual Traffic Classifier (vTC).
Results of the test are shown in the Dashboard006_
The throughput is expressed as percentage of the available bandwidth on the NIC.


* TC007

TC007 is the Virtual Traffic Classifier Data Plane Throughput Benchmarking in presence of
noisy neighbors Test.
It collects measures about the end-to-end throughput supported by the
virtual Traffic Classifier when a user-defined number of noisy neighbors is deployed.
Results of the test are shown in the Dashboard007_
The throughput is expressed as percentage of the available bandwidth on the NIC.


* TC020

TC020 is the Virtual Traffic Classifier Instantiation Test.
It verifies that a newly instantiated vTC is alive and functional and its instantiation
is correctly supported by the underlying infrastructure.
Results of the test are shown in the Dashboard020_


* TC021
            
TC021 is the Virtual Traffic Classifier Instantiation in presence of noisy neighbors Test.
It verifies that a newly instantiated vTC is alive and functional and its instantiation
is correctly supported by the underlying infrastructure when noisy neighbors are present.
Results of the test are shown in the Dashboard021_


Detailed test results
---------------------

* TC006

The results for TC006 have been obtained using the following test case 
configuration:

- Context: Dummy
- Scenario: vtc_throughput
- Network Techology: SR-IOV
- vTC Flavor: m1.large


* TC007

The results for TC007 have been obtained using the following test case 
configuration:

- Context: Dummy
- Scenario: vtc_throughput_noisy
- Network Techology: SR-IOV
- vTC Flavor: m1.large
- Number of noisy neighbors: 2
- Number of cores per neighbor: 2
- Amount of RAM per neighbor: 1G


* TC020

The results for TC020 have been obtained using the following test case 
configuration:

The results listed in previous section have been obtained using the following
test case configuration:

- Context: Dummy
- Scenario: vtc_instantiation_validation
- Network Techology: SR-IOV
- vTC Flavor: m1.large


           
* TC021

The results listed in previous section have been obtained using the following
test case configuration:

- Context: Dummy
- Scenario: vtc_instantiation_validation
- Network Techology: SR-IOV
- vTC Flavor: m1.large
- Number of noisy neighbors: 2
- Number of cores per neighbor: 2
- Amount of RAM per neighbor: 1G


For all the test cases, the user can specify different values for the parameters.

Rationale for decisions
-----------------------

* TC006

The result of the test is a number between 0 and 100 which represents the percentage of bandwidth
available on the NIC that corresponds to the supported throughput by the vTC.


* TC007

The result of the test is a number between 0 and 100 which represents the percentage of bandwidth
available on the NIC that corresponds to the supported throughput by the vTC.

* TC020

The execution of the test is done as described in the following:

- The vTC is deployed on the OpenStack testbed;
- Some traffic is sent to the vTC;
- The vTC changes the header of the packets and sends them back to the packet generator;
- The packet generator checks that all the packets are received correctly and have been changed
correctly by the vTC.

The test is declared as PASSED if all the packets are correcly received by the packet generator
and they have been modified by the virtual Traffic Classifier as required.


* TC021

The execution of the test is done as described in the following:

- The vTC is deployed on the OpenStack testbed;
- The noisy neighbors are deployed as requested by the user;
- Some traffic is sent to the vTC;
- The vTC change the header of the packets and sends them back to the packet generator;
- The packet generator checks that all the packets are received correctly and have been changed
correctly by the vTC

The test is declared as PASSED if all the packets are correcly received by the packet generator
and they have been modified by the virtual Traffic Classifier as required.


Conclusions and recommendations
-------------------------------

* TC006

The obtained results show that the virtual Traffic Classifier can support up to 4 Gbps
(40% of the available bandwidth) correspond to the expected behaviour of the virtual
Traffic Classifier.
Using the configuration with SR-IOV and large flavor, the expected throughput should 
generally be in the range between 3 and 4 Gbps.


* TC007 

These results correspond to the configuration in which the virtual Traffic Classifier uses SR-IOV
Virtual Functions and the flavor is set to large for the virtual machine.
The throughput is in the range between 2.5 Gbps and 3.7 Gbps.
This shows that the effect of 2 noisy neighbors reduces the throughput of
the service between 10 and 20%.
Increasing number of neihbours would have a higher impact on the performance.


* TC020

The obtained results correspond to the expected behaviour of the virtual Traffic Classifier.
Using the configuration with SR-IOV and large flavor, the expected result is that the vTC is
correctly instantiated, it is able to receive and send packets using SR-IOV technology
and to forward packets back to the packet generator changing the TCP/IP header as required.


* TC021

The obtained results correspond to the expected behaviour of the virtual Traffic Classifier.
Using the configuration with SR-IOV and large flavor, the expected result is that the vTC is
correctly instantiated, it is able to receive and send packets using SR-IOV technology
and to forward packets back to the packet generator changing the TCP/IP header as required,
also in presence of noisy neighbors.
