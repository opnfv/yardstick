.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, National Center of Scientific Research "Demokritos" and others.

==========================
Virtual Traffic Classifier
==========================

Abstract
========

.. _TNOVA: http://www.t-nova.eu/
.. _TNOVAresults: http://www.t-nova.eu/results/
.. _Yardstick: https://wiki.opnfv.org/yardstick

This chapter provides an overview of the virtual Traffic Classifier, a
contribution to OPNFV Yardstick_ from the EU Project TNOVA_.
Additional documentation is available in TNOVAresults_.

Overview
========

The virtual Traffic Classifier (:term:`VTC`) :term:`VNF`, comprises of a
Virtual Network Function Component (:term:`VNFC`). The :term:`VNFC` contains
both the Traffic Inspection module, and the Traffic forwarding module, needed
to run the :term:`VNF`. The exploitation of Deep Packet Inspection
(:term:`DPI`) methods for traffic classification is built around two basic
assumptions:

* third parties unaffiliated with either source or recipient are able to
inspect each IP packet’s payload

* the classifier knows the relevant syntax of each application’s packet
payloads (protocol signatures, data patterns, etc.).

The proposed :term:`DPI` based approach will only use an indicative, small
number of the initial packets from each flow in order to identify the content
and not inspect each packet.

In this respect it follows the Packet Based per Flow State (term:`PBFS`). This
method uses a table to track each session based on the 5-tuples (src address,
dest address, src port,dest port, transport protocol) that is maintained for
each flow.

Concepts
========

* *Traffic Inspection*: The process of packet analysis and application
identification of network traffic that passes through the :term:`VTC`.

* *Traffic Forwarding*: The process of packet forwarding from an incoming
network interface to a pre-defined outgoing network interface.

* *Traffic Rule Application*: The process of packet tagging, based on a
predefined set of rules. Packet tagging may include e.g. Type of Service
(:term:`ToS`) field modification.

Architecture
============

The Traffic Inspection module is the most computationally intensive component
of the :term:`VNF`. It implements filtering and packet matching algorithms in
order to support the enhanced traffic forwarding capability of the :term:`VNF`.
The component supports a flow table (exploiting hashing algorithms for fast
indexing of flows) and an inspection engine for traffic classification.

The implementation used for these experiments exploits the nDPI library.
The packet capturing mechanism is implemented using libpcap. When the
:term:`DPI` engine identifies a new flow, the flow register is updated with the
appropriate information and transmitted across the Traffic Forwarding module,
which then applies any required policy updates.

The Traffic Forwarding moudle is responsible for routing and packet forwarding.
It accepts incoming network traffic, consults the flow table for classification
information for each incoming flow and then applies pre-defined policies
marking e.g. :term:`ToS`/Differentiated Services Code Point (:term:`DSCP`)
multimedia traffic for Quality of Service (:term:`QoS`) enablement on the
forwarded traffic.
It is assumed that the traffic is forwarded using the default policy until it
is identified and new policies are enforced.

The expected response delay is considered to be negligible, as only a small
number of packets are required to identify each flow.

Graphical Overview
==================

.. code-block:: console

  +----------------------------+
  |                            |
  | Virtual Traffic Classifier |
  |                            |
  |     Analysing/Forwarding   |
  |        ------------>       |
  |     ethA          ethB     |
  |                            |
  +----------------------------+
       |              ^
       |              |
       v              |
  +----------------------------+
  |                            |
  |     Virtual Switch         |
  |                            |
  +----------------------------+

Install
=======

run the vTC/build.sh with root privileges

Run
===

::

    sudo ./pfbridge -a eth1 -b eth2


.. note:: Virtual Traffic Classifier is not support in OPNFV Danube release.


Development Environment
=======================

Ubuntu 14.04 Ubuntu 16.04
