.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.


Yardstick
=========


Overview
--------

Yardstick is a framework to test non functional characteristics of an NFV
Infrastructure as perceived by an application.

An application is a set of virtual machines deployed using the orchestrator of
the target cloud, for example OpenStack Heat.

Yardstick measures a certain service performance but can also validate the
service performance to be within a certain level of agreement.

For more information on Yardstick project, please visit:

    https://wiki.opnfv.org/display/yardstick/Yardstick
    http://artifacts.opnfv.org/yardstick/colorado/3.0/docs/userguide/index.html#document-01-introduction


Architecture
------------

Yardstick is a command line tool written in python inspired by Rally. Yardstick
is intended to run on a computer with access and credentials to a cloud. The
test case is described in a configuration file given as an argument.

How it works: the benchmark task configuration file is parsed and converted into
an internal model. The context part of the model is converted into a Heat
template and deployed into a stack. Each scenario is run using a runner, either
serially or in parallel. Each runner runs in its own subprocess executing
commands in a VM using SSH. The output of each command is written as json
records to a file.

For more information on Yardstick architecture, please read:

    http://artifacts.opnfv.org/yardstick/colorado/3.0/docs/userguide/index.html#document-03-architecture


Installation
------------

Yardstick supports installation on Ubuntu 14.04 or via a Docker image.

To learn how to install Yardstick, consult the documentation available online
at:

    http://artifacts.opnfv.org/yardstick/colorado/3.0/docs/userguide/index.html#document-07-installation


Developers
----------
For information on how to contribute to Yardstick, please visit:

    https://wiki.opnfv.org/display/yardstick/Get+started+as+a+Yardstick+developer
