
.. _ETSI: https://docbox.etsi.org/ISG/NFV/Open/Drafts/TST001_-_Pre-deployment_Validation/
.. _Yardstick: https://wiki.opnfv.org/yardstick

Introduction
============

Yardstick is a testing framework. It is a project within the OPNFV
community introduced in the OPNFV R2 Brahmaputra release. Yardstick is
aligned to ETSI specifications, see ETSI_.

The Yardstick-project at OPNFV can be found here: Yardstick_

Currently Yardstick is limited to running virtualized on OpenStack only.

Yardstick verifies non-functional areas from the aspect of a VNF application,
such as performance and characteristics of the underlying IaaS. Typical
testing areas are networking, storage and CPU. The main testing aspects
are performance and characteristics, e.g. bandwidth, speed, latency,
jitter and scaling.

Examples of more specific areas covered by Yardstick are KVM, vSwitch,
ODL with Service Function Chaining, IPv6, High Availability. The
virtual Traffic Classifier (vTC) with ApexLake is also covered,
please see <TODO>.

Much of the idea behind Yardstick is also to be able to compare test
suites on different (HW and SW) configurations, as well as to be able
to spot trends over time. For these purposes some Yardstick test results
are included the general OPNFV test visualization framework.
For more detailed test results the Yardstick internal database and
visualization tools must be used. These are based on Influx and Grafana.

All of the tools used and included in Yardstick are open source.

Yardstick is mainly written in Python, and test configurations are made
in YAML. Documentation is written in reStructuredText format, i.e. .rst
files.

Yardstick can currently be deployed using Apex, Compass, Fuel, or Joid,
and is primarily supported to be deployed onto the virtualized IaaS via
a Docker container.

Typical test execution is done by deploying one or several VMs on to the
IaaS invoking the test from there with no stimuli from outside the
IaaS.

Included here is documentation describing how to install Yardstick on to
different deployment configurations, how to run individual test cases and
test suites, how to pick and chose which specific tests to run and where
and how to fetch and visualize test results from the databases.

Yardstick can be run on its own on top of a deployed OPNFV IaaS, which is
mainly how it is run inside the OPNFV community labs in regular daily and
weekly OPNFV builds. It can also run in parallel to a deployed VNF.

Yardstick comes with default configured test cases and test suites. These
can be picked and chosen from, and also modified.

Test cases are invoked using the "yardstick" command suite, which resembles
the Rally framework command suite to a large extent.
