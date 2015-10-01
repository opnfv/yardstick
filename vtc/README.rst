=========
Yardstick
=========

Overview of the virtual Traffic Classifier
========
The virtual Traffic Classifier VNF, comprises in the current version of 1 VNFC.
The VNFC contains both the Traffic Inspection module, and the Traffic forwarding module, needed to run the VNF.


Concepts
========
Traffic Inspection
Traffic Forwarding
Rule Application

Architecture
============

The Traffic Inspection module is the most computationally intensive component of the VNF. 
It implements filtering and packet matching algorithms in order to support the enhanced traffic forwarding capability of the VNF.
The component supports a flow table (exploiting hashing algorithms for fast indexing of flows) and an inspection engine for traffic classification. 
The implementation used for these experiments exploits the nDPI library.
The packet capturing mechanism is implemented using libpcap.
When the DPI engine identifies a new flow, the flow register is updated with the appropriate information and transmitted across the Traffic Forwarding module, 
which then applies any required policy updates. 
The Traffic Forwarding moudle is responsible for routing and packet forwarding.
It accepts incoming network traffic, consults the flow table for classification information for each incoming flow and then applies pre-defined policies marking 
e.g. type of Service/Differentiated Services Code Point (TOS/DSCP) multimedia traffic for QoS enablement on the forwarded traffic.
It is assumed that the traffic is forwarded using the default policy until it is identified and new policies are enforced. 
The expected response delay is considered to be negligible, as only a small number of packets are required to identify each flow.

Install
=======

run the build.sh with root privileges

Run
===

TBD

Custom Image
============

TBD

Development Environment
=======================

Ubuntu 14.04 >= VM


