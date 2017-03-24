.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB, Huawei Technologies Co.,Ltd and others.

Yardstick Installation
======================


Abstract
--------

Yardstick supports installation by Docker or directly in Ubuntu. The
installation procedure for Docker and direct installation are detailed in
the section below.

To use Yardstick you should have access to an OpenStack environment, with at
least Nova, Neutron, Glance, Keystone and Heat installed.

The steps needed to run Yardstick are:

1. Install Yardstick.
2. Load OpenStack environment variables.
3. Create a Neutron external network.
4. Build Yardstick flavor and a guest image.
5. Load the guest image into the OpenStack environment.
6. Create the test configuration .yaml file.
7. Run the test case.


Prerequisites
-------------

The OPNFV deployment is out of the scope of this document but it can be
found in http://artifacts.opnfv.org/opnfvdocs/colorado/docs/configguide/index.html.
The OPNFV platform is considered as the System Under Test (SUT) in this
document.

Several prerequisites are needed for Yardstick:

    #. A Jumphost to run Yardstick on
    #. A Docker daemon shall be installed on the Jumphost
    #. A public/external network created on the SUT
    #. Connectivity from the Jumphost to the SUT public/external network

WARNING: Connectivity from Jumphost is essential and it is of paramount
importance to make sure it is working before even considering to install
and run Yardstick. Make also sure you understand how your networking is
designed to work.

NOTE: **Jumphost** refers to any server which meets the previous
requirements. Normally it is the same server from where the OPNFV
deployment has been triggered previously.

NOTE: If your Jumphost is operating behind a company http proxy and/or
Firewall, please consult first the section `Proxy Support`_, towards
the end of this document. The section details some tips/tricks which
*may* be of help in a proxified environment.


Installing Yardstick using Docker
---------------------------------

Yardstick has a Docker image,
**It is recommended to use this Docker image to run Yardstick test**.

Pulling the Yardstick Docker image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _dockerhub: https://hub.docker.com/r/opnfv/yardstick/

Pull the Yardstick Docker image (**opnfv/yardstick**) from the public dockerhub
registry under the OPNFV account: [dockerhub_], with the following docker
command::

  docker pull opnfv/yardstick:stable

After pulling the Docker image, check that it is available with the
following docker command::

  [yardsticker@jumphost ~]$ docker images
  REPOSITORY         TAG       IMAGE ID        CREATED      SIZE
  opnfv/yardstick    stable    a4501714757a    1 day ago    915.4 MB

Run the Docker image to get a Yardstick container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

  docker run -itd --privileged -v /var/run/docker.sock:/var/run/docker.sock -p 8888:5000 -e INSTALLER_IP=192.168.200.2 -e INSTALLER_TYPE=compass --name yardstick opnfv/yardstick:stable

note:

+----------------------------------------------+------------------------------+
| parameters                                   | Detail                       |
+==============================================+==============================+
| -itd                                         | -i: interactive, Keep STDIN  |
|                                              | open even if not attached.   |
|                                              | -t: allocate a pseudo-TTY.   |
|                                              | -d: run container in         |
|                                              | detached mode, in the        |
|                                              | background.                  |
+----------------------------------------------+------------------------------+
| --privileged                                 | If you want to build         |
|                                              | yardstick-image in yardstick |
|                                              | container, this parameter is |
|                                              | needed.                      |
+----------------------------------------------+------------------------------+
| -e INSTALLER_IP=192.168.200.2                | If you want to use yardstick |
|                                              | env prepare command(or       |
| -e INSTALLER_TYPE=compass                    | related API) to load the     |
|                                              | images that yardstick needs, |
|                                              | these parameters should be   |
|                                              | provided.                    |
|                                              | The INSTALLER_IP and         |
|                                              | INSTALLER_TYPE are depending |
|                                              | on your OpenStack installer, |
|                                              | currently apex, compass,     |
|                                              | fuel and joid are supported. |
|                                              | If you use other installers, |
|                                              | such as devstack, these      |
|                                              | parameters can be ignores.   |
+----------------------------------------------+------------------------------+
| -p 8888:5000                                 | If you want to call          |
|                                              | yardstick API out of         |
|                                              | yardstick container, this    |
|                                              | parameter is needed.         |
+----------------------------------------------+------------------------------+
| -v /var/run/docker.sock:/var/run/docker.sock | If you want to use yardstick |
|                                              | env grafana/influxdb to      |
|                                              | create a grafana/influxdb    |
|                                              | container out of yardstick   |
|                                              | container, this parameter is |
|                                              | needed.                      |
+----------------------------------------------+------------------------------+
| --name yardstick                             | The name for this container, |
|                                              | not needed and can be        |
|                                              | defined by the user.         |
+----------------------------------------------+------------------------------+

Enter Yardstick container
^^^^^^^^^^^^^^^^^^^^^^^^^

::

  docker exec -it yardstick /bin/bash

In the container, the Yardstick repository is located in the /home/opnfv/repos
directory.

In Danube release, we have improved the Yardstick installation steps.
Now Yardstick provides a CLI to prepare openstack environment variables and
load yardstick images::

  yardstick env prepare

If you ues this command. you can skip the following sections about how to
prepare openstack environment variables, load yardstick images and load
yardstick flavor manually.


Installing Yardstick directly in Ubuntu
---------------------------------------

.. _install-framework:

Alternatively you can install Yardstick framework directly in Ubuntu or in an Ubuntu Docker
image. No matter which way you choose to install Yardstick framework, the
following installation steps are identical.

If you choose to use the Ubuntu Docker image, You can pull the Ubuntu
Docker image from Docker hub:

::

  docker pull ubuntu:16.04


Installing Yardstick framework
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Download source code and install Yardstick framework:

::

  git clone https://gerrit.opnfv.org/gerrit/yardstick
  cd yardstick
  ./install.sh

For installing yardstick directly in Ubuntu, the **yardstick env command** is not available.
You need to prepare openstack environment variables, load yardstick images and load
yardstick flavor manually.


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


Yardstick falvor and guest images
---------------------------------

Before executing Yardstick test cases, make sure that yardstick guest image and
yardstick flavor are available in OpenStack.
Detailed steps about creating yardstick flavor and building yardstick-trusty-server
image can be found below.

Yardstick-flavor
^^^^^^^^^^^^^^^^
Most of the sample test cases in Yardstick are using an OpenStack flavor called
*yardstick-flavor* which deviates from the OpenStack standard m1.tiny flavor by the
disk size - instead of 1GB it has 3GB. Other parameters are the same as in m1.tiny.

Create yardstick-flavor:

::

  nova flavor-create yardstick-flavor 100 512 3 1


.. _guest-image:

Building a guest image
^^^^^^^^^^^^^^^^^^^^^^
Most of the sample test cases in Yardstick are using a guest image called
*yardstick-trusty-server* which deviates from an Ubuntu Cloud Server image
containing all the required tools to run test cases supported by Yardstick.
Yardstick has a tool for building this custom image. It is necessary to have
sudo rights to use this tool.

Also you may need install several additional packages to use this tool, by
follwing the commands below:

::

  apt-get update && apt-get install -y \
      qemu-utils \
      kpartx

This image can be built using the following command while in the directory where
Yardstick is installed (``~/yardstick`` if the framework is installed
by following the commands above):

::

  sudo ./tools/yardstick-img-modify tools/ubuntu-server-cloudimg-modify.sh

**Warning:** the script will create files by default in:
``/tmp/workspace/yardstick`` and the files will be owned by root!

If you are building this guest image in inside a docker container make sure the
container is granted with privilege.

The created image can be added to OpenStack using the ``glance image-create`` or
via the OpenStack Dashboard.

Example command:

::

  glance --os-image-api-version 1 image-create \
  --name yardstick-image --is-public true \
  --disk-format qcow2 --container-format bare \
  --file /tmp/workspace/yardstick/yardstick-image.img

Some Yardstick test cases use a Cirros image and a Ubuntu 14.04 image, you can find one at
http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img, https://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img

Add cirros and ubuntu image to OpenStack:

::

  openstack image create \
      --disk-format qcow2 \
      --container-format bare \
      --file $cirros_image_file \
      cirros-0.3.5

  openstack image create \
      --disk-format qcow2 \
      --container-format bare \
      --file $ubuntu_image_file \
      Ubuntu-14.04

Automatic flavor and image creation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yardstick has a script for automatic creating yardstick flavor and building
guest images. This script is mainly used in CI, but you can still use it in
your local environment.

Example command:

::

  source $YARDSTICK_REPO_DIR/tests/ci/load_images.sh


Examples and verifying the install
----------------------------------

It is recommended to verify that Yardstick was installed successfully
by executing some simple commands and test samples. Before executing yardstick
test cases make sure yardstick flavor and building yardstick-trusty-server
image can be found in glance and openrc file is sourced. Below is an example
invocation of yardstick help command and ping.py test sample:
::

  yardstick -h
  yardstick task start samples/ping.yaml

Each testing tool supported by Yardstick has a sample configuration file.
These configuration files can be found in the **samples** directory.

Default location for the output is ``/tmp/yardstick.out``.


Deploy InfluxDB and Grafana locally
------------------------------------

The 'yardstick env' command can also help you to build influxDB and Grafana in
your local environment.

Create InfluxDB container and config with the following command::

  yardstick env influxdb


Create Grafana container and config::

  yardstick env grafana

Then you can run a test case and visit http://host_ip:3000(user:admin,passwd:admin) to see the results.

note: Using **yardstick env** command to deploy InfluxDB and Grafana requires
Jump Server's docker API version => 1.24. You can use the following command to
check the docker API version:

::

  docker version

The following sections describe how to deploy influxDB and Grafana manually.

.. pull docker images

Pull docker images

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

  docker pull tutum/influxdb
  docker pull grafana/grafana

Run influxdb and config
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Run grafana
::

  docker run -d --name grafana -p 3000:3000 grafana/grafana

Config grafana
::

  http://{YOUR_IP_HERE}:3000
  log on using admin/admin and config database resource to be {YOUR_IP_HERE}:8086

.. image:: images/Grafana_config.png
   :width: 800px
   :alt: Grafana data source configration

Config yardstick conf
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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

Now you can run yardstick test cases and store the results in influxdb
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Create a test suite for yardstick
------------------------------------

A test suite in yardstick is a yaml file which include one or more test cases.
Yardstick is able to support running test suite task, so you can customize you
own test suite and run it in one task.

"tests/opnfv/test_suites" is where yardstick put ci test-suite. A typical test
suite is like below:

fuel_test_suite.yaml

::

  ---
  # Fuel integration test task suite

  schema: "yardstick:suite:0.1"

  name: "fuel_test_suite"
  test_cases_dir: "samples/"
  test_cases:
  -
    file_name: ping.yaml
  -
    file_name: iperf3.yaml

As you can see, there are two test cases in fuel_test_suite, the syntax is simple
here, you must specify the schema and the name, then you just need to list the
test cases in the tag "test_cases" and also mark their relative directory in the
tag "test_cases_dir".

Yardstick test suite also support constraints and task args for each test case.
Here is another sample to show this, which is digested from one big test suite.

os-nosdn-nofeature-ha.yaml

::

 ---

 schema: "yardstick:suite:0.1"

 name: "os-nosdn-nofeature-ha"
 test_cases_dir: "tests/opnfv/test_cases/"
 test_cases:
 -
     file_name: opnfv_yardstick_tc002.yaml
 -
     file_name: opnfv_yardstick_tc005.yaml
 -
     file_name: opnfv_yardstick_tc043.yaml
        constraint:
           installer: compass
           pod: huawei-pod1
        task_args:
           huawei-pod1: '{"pod_info": "etc/yardstick/.../pod.yaml",
           "host": "node4.LF","target": "node5.LF"}'

As you can see in test case "opnfv_yardstick_tc043.yaml", there are two tags, "constraint" and
"task_args". "constraint" is where you can specify which installer or pod it can be run in
the ci environment. "task_args" is where you can specify the task arguments for each pod.

All in all, to create a test suite in yardstick, you just need to create a suite yaml file
and add test cases and constraint or task arguments if necessary.
