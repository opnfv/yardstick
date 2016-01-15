
.. _Yardstick: https://wiki.opnfv.org/yardstick
.. _ApexLake: <TODO>

============
Introduction
============

Yardstick is a testing framework. The Yardstick-project at OPNFV can be
found here: Yardstick_

Yardstick primarily verifies non-functional areas from the aspects of
a VNF application, such as performance and characteristics of the underlying
IaaS. Typical testing areas are networking, storage and CPU. The main testing
aspects of performance and characteristics are e.g. bandwidth, speed, latency,
jitter and scaling. Also other aspects are included, for instance High
Availability (HA).

It is also possible to connect Yardstick to other testing frameworks, for
example ApexLake_.

Much of the idea behind Yardstick is also to be able to compare test
suites on different (HW and SW) configurations, as well as to be able
to spot trends over time. For these purposes some Yardstick test results
are included in the general OPNFV test storage and visualization framework
by using MongoDB and Bitergia. For more detailed test results the Yardstick
internal database and visualization tools must be used. These are based on
InfluxDB and Grafana.

All of the tools used and included in Yardstick are open source, also the
tools developed by the Yardstick project.

Yardstick is mainly written in Python, and test configurations are made
in YAML. Documentation is written in reStructuredText format, i.e. .rst
files.

Yardstick is designed to support a variety of different installers.
Examples of such installers could be Apex, Compass, Fuel, or Joid,
The Yardstick environment is mainly intended to be installed via
a container framework, but it is also possible to install Yardstick
directly as well, see :doc:`03-installation`.

Typical test execution is done by deploying one or several VMs on to the
IaaS invoking the test from there with no stimuli from outside the
IaaS. Yardstick can also run on bare metal deployments.

Included here is documentation describing how to install Yardstick on to
different deployment configurations, how to run individual test cases and
test suites, how to pick and chose which specific tests to run and where
and how to fetch and visualize test results from the databases.

Yardstick can be run on its own on top of a deployed OPNFV IaaS, which is
mainly how it is run inside the OPNFV community labs in regular daily and
weekly OPNFV builds. It can also run in parallel to a deployed VNF.

Yardstick comes with default configured test cases, test suites and test
samples. These can be picked and chosen from, and also modified to fit
specific use cases.
