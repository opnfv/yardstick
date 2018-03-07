.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

============
Introduction
============

**Welcome to Yardstick's documentation !**

.. _Pharos: https://wiki.opnfv.org/pharos
.. _Yardstick: https://wiki.opnfv.org/yardstick
.. _Presentation: https://wiki.opnfv.org/download/attachments/2925202/opnfv_summit_-_yardstick_project.pdf?version=1&modificationDate=1458848320000&api=v2

Yardstick_ is an OPNFV Project.

The project's goal is to verify infrastructure compliance, from the perspective
of a Virtual Network Function (:term:`VNF`).

The Project's scope is the development of a test framework, *Yardstick*, test
cases and test stimuli to enable Network Function Virtualization Infrastructure
(:term:`NFVI`) verification.

*Yardstick* is used in OPNFV for verifying the OPNFV infrastructure and some of
the OPNFV features. The *Yardstick* framework is deployed in several OPNFV
community labs. It is *installer*, *infrastructure* and *application*
independent.

.. seealso:: Pharos_ for information on OPNFV community labs and this
   Presentation_ for an overview of *Yardstick*


About This Document
===================

This document consists of the following chapters:

* Chapter :doc:`01-introduction` provides a brief introduction to *Yardstick*
  project's background and describes the structure of this document.

* Chapter :doc:`02-methodology` describes the methodology implemented by the
  *Yardstick* Project for :term:`NFVI` verification.

* Chapter :doc:`03-architecture` provides information on the software
  architecture of *Yardstick*.

* Chapter :doc:`04-installation` provides instructions to install *Yardstick*.

* Chapter :doc:`06-yardstick-plugin` provides information on how to integrate
  other OPNFV testing projects into *Yardstick*.

* Chapter :doc:`07-result-store-InfluxDB` provides inforamtion on how to run
  plug-in test cases and store test results into community's InfluxDB.

* Chapter :doc:`08-grafana` provides inforamtion on *Yardstick* grafana
  dashboard and how to add a dashboard into *Yardstick* grafana dashboard.

* Chapter :doc:`09-api` provides inforamtion on *Yardstick* ReST API and how to
  use *Yardstick* API.

* Chapter :doc:`10-yardstick-user-interface` provides inforamtion on how to use
  yardstick report CLI to view the test result in table format and also values
  pinned on to a graph

* Chapter :doc:`11-vtc-overview` provides information on the :term:`VTC`.

* Chapter :doc:`12-nsb-overview` describes the methodology implemented by the
  Yardstick - Network service benchmarking to test real world usecase for a
  given VNF.

* Chapter :doc:`13-nsb_installation` provides instructions to install
  *Yardstick - Network Service Benchmarking (NSB) testing*.

* Chapter :doc:`14-nsb-operation` provides information on running *NSB*

* Chapter :doc:`15-list-of-tcs` includes a list of available *Yardstick* test
  cases.

Contact Yardstick
=================

Feedback? `Contact us`_

.. _Contact us: mailto:opnfv-users@lists.opnfv.org&subject="[yardstick]"
