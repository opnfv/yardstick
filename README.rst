=========
Yardstick
=========

Overview
========

Yardstick is a framework to test non functional characteristics of an NFV 
Infrastructure as perceived by an application.

An application is a set of virtual machines deployed using the orchestrator of
the target cloud, for example OpenStack Heat.

Yardstick measures a certain service performance but can also validate the
service performance to be within a certain level of agreement.

Yardstick is _not_ about testing OpenStack functionality (tempest) or 
benchmarking OpenStack APIs (rally).

Concepts
========

Benchmark - assess the relative performance of something

Benchmark configuration file - describes a single test case in yaml format

Context
- The set of cloud resources used by a benchmark (scenario)
– Is a simplified Heat template (context is converted into a Heat template)

Data
- Output produced by running a benchmark, written to a file in json format

Runner
- Logic that determines how the test is run
– For example number of iterations, input value stepping, duration etc

Scenario
- Type/class of measurement for example Ping, Pktgen, (Iperf, LmBench, ...)

SLA
- Some limit to be verified (specific to scenario), for example max_latency
– Associated action to automatically take: assert, monitor etc

Architecture
============

Yardstick is a command line tool written in python inspired by Rally. Yardstick
is intended to run on a computer with access and credentials to a cloud. The 
test case is described in a configuration file given as an argument. 

How it works: the benchmark task configuration file is parsed and converted into
an internal model. The context part of the model is converted into a Heat 
template and deployed into a stack. Each scenario is run using a runner, either
serially or in parallel. Each runner runs in its own subprocess executing 
commands in a VM using SSH. The output of each command is written as json 
records to a file.

Install
=======

TBD

Run
===

Example invocation:
$ export OS_AUTH_URL="http://172.16.0.2:5000/v2.0"
$ export OS_TENANT_NAME="yardstick"
$ export OS_USERNAME="yardstick"
$ export OS_PASSWORD="yardstick"
$ export OS_EXTERNAL_NET_ID=net04_ext
$ yardstick -d samples/ping-task.yaml

Custom Image
============

pktgen test requires a ubuntu server cloud image
TBD

Developers
==========

Example setup known to work for development and test:
- Development environment: Ubuntu14.04, eclipse, virtual environment
- Cloud: Mirantis 6.0 deployed using Virtualbox

Create a virtual environment:
$ sudo apt-get install python-virtualenv
$ virtualenv ~/yardstick_venv
$ source ~/yardstick_venv/bin/activate
$ python setup.py develop

