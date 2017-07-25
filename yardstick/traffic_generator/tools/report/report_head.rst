.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Intel Corporation, AT&T and others.

Introduction
============
The objective of the OPNFV project titled **"Characterise vSwitch Performance
for Telco NFV Use Cases"**, is to evaluate a virtual switch to identify its
suitability for a Telco Network Function Virtualization (NFV) environment. As
well as this, the project aims to identify any gaps or bottlenecks in order to
drive architectural changes to improve virtual switch performance and
determinism. The purpose of this document is to summarize the results of the
tests carried out on the virtual switch in the Network Function Virtualization
Infrastructure (NFVI) and, from these results, provide evaluations and
recommendations for the virtual switch. Test results will be outlined in
details-of-LTR_, preceded by the document-identifier_ and the scope_ and
references_).

This document is currently in draft form.

.. _document-identifier:

Document identifier
-------------------
The document id will be used to uniquely identify versions of the LTR. The
format for the document id will be:
OPNFV\_vswitchperf\_LTR\_rel\_STATUS, the status is one of: DRAFT, REVIEWED,
CORRECTED or FINAL. The document id for this version of the LTR is:
OPNFV\_vswitchperf\_LTR\_Brahmaputra\_DRAFT.

.. _scope:

Scope
-----
The scope of this report is to detail the results of the tests that have been
performed on the virtual switch. This report will also evaluate the results of
these tests and, based on these evaluations, provide recommendations on the
suitability of the virtual switch for use in a Telco NFV environment.

.. _references:

References
----------
`OPNFV_vswitchperf_LTD_Brahmaputra_REVIEWED
<http://artifacts.opnfv.org/vswitchperf/docs/requirements/vswitchperf_ltd.html>`__

.. _details-of-LTR:

Details of the Level Test Report
================================
This section provides a test-results-overview_. Also included are the rationale_
and the conclusions_.

.. _test-results-overview:

