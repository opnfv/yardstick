=========
Yardstick
=========

Overview of the virtual Traffic Classifier
========
The virtual Traffic Classifier VNF [1], comprises in the current version of
1 VNFC [2]. The VNFC contains both the Traffic Inspection module, and the
Traffic forwarding module, needed to run the VNF. The exploitation of DPI
methods for traffic classification is built around two basic assumptions:
(i) third parties unaffiliated with either source or recipient are able to
inspect each IP packet’s payload and
(ii) the classifier knows the relevant syntax of each application’s packet
payloads (protocol signatures, data patterns, etc.).
The proposed DPI based approach will only use an indicative, small number of the
initial packets from each flow in order to identify the content and not inspect
each packet.
In this respect it follows the Packet Based per Flow State (PBFS).
This method uses a table to track each session based on the 5-tuples
(src address,dest address,src port,dest port,transport protocol)
that is maintained for each flow.

Concepts
========
Traffic Inspection: The process of packet analysis and application
identification of network traffic that passes through the vTC.

Traffic Forwarding: The process of packet forwarding from an incoming
network interface to a pre-defined outgoing network interface.

Traffic Rule Application: The process of packet tagging, based on a
predefined set of rules. Packet tagging may include e.g. ToS field modification.

Architecture
============

The Traffic Inspection module is the most computationally intensive component
of the VNF. It implements filtering and packet matching algorithms in order to
support the enhanced traffic forwarding capability of the VNF. The component
supports a flow table (exploiting hashing algorithms for fast indexing of flows)
and an inspection engine for traffic classification. The implementation used for
these experiments exploits the nDPI library. The packet capturing mechanism is
implemented using libpcap. When the DPI engine identifies a new flow, the flow
register is updated with the appropriate information and transmitted across the
Traffic Forwarding module, which then applies any required policy updates.
The Traffic Forwarding moudle is responsible for routing and packet forwarding.
It accepts incoming network traffic, consults the flow table for classification
information for each incoming flow and then applies pre-defined policies marking
e.g. type of Service/Differentiated Services Code Point (TOS/DSCP) multimedia
traffic for QoS enablement on the forwarded traffic. It is assumed that the
traffic is forwarded using the default policy until it is identified and new
policies are enforced. The expected response delay is considered to be
negligible,as only a small number of packets are required to identify each flow.

Graphical Overview
==================

+----------------------------+
|                            |
| Virtual Traffic Classifier |
|                            |
|     Analysing/Forwarding   |
|         +-------->         |
|     ethA          ethB     |
+------+--------------+------+
       |              ^
       |              |
       |              |
       |              |
       v              |
+------+--------------+------+
|                            |
|     Virtual Switch         |
|                            |
+----------------------------+


Install
=======

run the build.sh with root privileges

Run
===

sudo ./pfbridge -a eth1 -b eth2

Custom Image
============

TBD

Development Environment
=======================

Ubuntu 14.04 >= VM
