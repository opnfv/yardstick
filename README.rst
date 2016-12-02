.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

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


Yardstick Installation Instructions
===================================

This is a step by step guide of how to install Yardstick.
For detailed information please visit Yardstick user guide:
http://artifacts.opnfv.org/yardstick/colorado/3.0/docs/userguide/index.html


Installing Yardstick using Docker
---------------------------------


Pulling the Yardstick Docker image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

  docker pull opnfv/yardstick:stable


After pulling the Docker image, check that it is available with the
following docker command:

::

  [yardsticker@jumphost ~]$ docker images
  REPOSITORY         TAG       IMAGE ID        CREATED      SIZE
  opnfv/yardstick    stable    a4501714757a    1 day ago    915.4 MB


Run the Docker image
^^^^^^^^^^^^^^^^^^^^

::

  docker run --privileged=true -it opnfv/yardstick:stable /bin/bash

In the container the Yardstick repository is located in the /home/opnfv/repos
directory.


OpenStack parameters and credentials
------------------------------------

Environment variables
^^^^^^^^^^^^^^^^^^^^^
Before running Yardstick it is necessary to export OpenStack environment variables
from the OpenStack *openrc* file (using the ``source`` command) and export the
external network name ``export EXTERNAL_NETWORK="external-network-name"``,
the default name for the external network is ``net04_ext``.

Credential environment variables in the *openrc* file have to include at least:

* OS_AUTH_URL
* OS_USERNAME
* OS_PASSWORD
* OS_TENANT_NAME

A sample openrc file may look like this:

* export OS_PASSWORD=console
* export OS_TENANT_NAME=admin
* export OS_AUTH_URL=http://172.16.1.222:35357/v2.0
* export OS_USERNAME=admin
* export OS_VOLUME_API_VERSION=2
* export EXTERNAL_NETWORK=net04_ext


Creating Yardstick-flavor
-------------------------

::

  nova flavor-create yardstick-flavor 100 512 3 1


Building custom image
---------------------

::

  export YARD_IMG_ARCH="amd64"
  sudo echo "Defaults env_keep += \"YARD_IMG_ARCH\"" >> /etc/sudoers
  sudo ./tools/yardstick-img-modify tools/ubuntu-server-cloudimg-modify.sh

**Warning:** the script will create files by default in:
``/tmp/workspace/yardstick`` and the files will be owned by root!

If you are building this guest image in inside a docker container make sure the
container is granted with privilege.


Add Yardstick custom image to OpenStack
---------------------------------------

::

  glance --os-image-api-version 1 image-create \
  --name yardstick-image --is-public true \
  --disk-format qcow2 --container-format bare \
  --file /tmp/workspace/yardstick/yardstick-image.img

Some Yardstick test cases use a Cirros image, you can find one at
http://download.cirros-cloud.net/0.3.3/cirros-0.3.3-x86_64-disk.img


Automatic flavor and image creation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yardstick has a script for automatic creating yardstick flavor and building
guest images. This script is mainly used in CI, but you can still use it in
your local environment.

Example command:

::

  export YARD_IMG_ARCH="amd64"
  sudo echo "Defaults env_keep += \"YARD_IMG_ARCH\"" >> /etc/sudoers
  source $YARDSTICK_REPO_DIR/tests/ci/load_images.sh


Yardstick default key pair
--------------------------
Yardstick uses a SSH key pair to connect to the guest image. This key pair can
be found in the ``resources/files`` directory. To run the ``ping-hot.yaml`` test
sample, this key pair needs to be imported to the OpenStack environment.


Run Yardstick test
=================

Examples and verifying the install
----------------------------------

It is recommended to verify that Yardstick was installed successfully
by executing some simple commands and test samples. Before executing yardstick
test cases make sure yardstick flavor and building yardstick-trusty-server
image can be found in glance and openrc file is sourced. Below is an example
invocation of yardstick help command and ping.py test sample:

::

  yardstick –h
  yardstick task start samples/ping.yaml

Each testing tool supported by Yardstick has a sample configuration file.
These configuration files can be found in the **samples** directory.

Default location for the output is ``/tmp/yardstick.out``.


Deploy InfluxDB and Grafana locally
------------------------------------

.. pull docker images

Pull docker images
^^^^^^^^^^^^^^^^^^

::

  docker pull tutum/influxdb
  docker pull grafana/grafana

Run influxdb and config
^^^^^^^^^^^^^^^^^^^^^^^
Run influxdb
::

  docker run -d --name influxdb \
  -p 8083:8083 -p 8086:8086 --expose 8090 --expose 8099 \
  tutum/influxdb
  docker exec -it influxdb bash

Config influxdb
::

  influx
  >CREATE USER root WITH PASSWORD 'root' WITH ALL PRIVILEGES
  >CREATE DATABASE yardstick;
  >use yardstick;
  >show MEASUREMENTS;

Run grafana and config
^^^^^^^^^^^^^^^^^^^^^^
Run grafana
::

  docker run -d --name grafana -p 3000:3000 grafana/grafana

Config grafana
::

  http://{YOUR_IP_HERE}:3000
  log on using admin/admin and config database resource to be {YOUR_IP_HERE}:8086

More details can be found at https://wiki.opnfv.org/display/yardstick/How+to+deploy+InfluxDB+and+Grafana+locally

Config yardstick conf
^^^^^^^^^^^^^^^^^^^^^
cp ./etc/yardstick/yardstick.conf.sample /etc/yardstick/yardstick.conf

vi /etc/yardstick/yardstick.conf
Config yardstick.conf
::

  [DEFAULT]
  debug = True
  dispatcher = influxdb

  [dispatcher_influxdb]
  timeout = 5
  target = http://{YOUR_IP_HERE}:8086
  db_name = yardstick
  username = root
  password = root
