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
the sections below.

To use Yardstick you should have access to an OpenStack environment, with at
least Nova, Neutron, Glance, Keystone and Heat installed.

The steps needed to run Yardstick are:

1. Install Yardstick.
2. Load OpenStack environment variables.
#. Create Yardstick flavor.
#. Build a guest image and load it into the OpenStack environment.
#. Create the test configuration ``.yaml`` file and run the test case/suite.


Prerequisites
-------------

The OPNFV deployment is out of the scope of this document and can be found `here <http://artifacts.opnfv.org/opnfvdocs/colorado/docs/configguide/index.html>`_. The OPNFV platform is considered as the System Under Test (SUT) in this document.

Several prerequisites are needed for Yardstick:

#. A Jumphost to run Yardstick on
#. A Docker daemon or a virtual environment installed on the Jumphost
#. A public/external network created on the SUT
#. Connectivity from the Jumphost to the SUT public/external network

**NOTE:** *Jumphost* refers to any server which meets the previous
requirements. Normally it is the same server from where the OPNFV
deployment has been triggered.

**WARNING:** Connectivity from Jumphost is essential and it is of paramount
importance to make sure it is working before even considering to install
and run Yardstick. Make also sure you understand how your networking is
designed to work.

**NOTE:** If your Jumphost is operating behind a company http proxy and/or
Firewall, please consult first the section `Proxy Support (**Todo**)`_, towards
the end of this document. That section details some tips/tricks which
*may* be of help in a proxified environment.


Install Yardstick using Docker (**recommended**)
---------------------------------------------------

Yardstick has a Docker image. It is recommended to use this Docker image to run Yardstick test.

Prepare the Yardstick container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _dockerhub: https://hub.docker.com/r/opnfv/yardstick/

Install docker on your guest system with the following command, if not done yet::

  wget -qO- https://get.docker.com/ | sh

Pull the Yardstick Docker image (``opnfv/yardstick``) from the public dockerhub
registry under the OPNFV account: dockerhub_, with the following docker
command::

  docker pull opnfv/yardstick:stable

After pulling the Docker image, check that it is available with the
following docker command::

  [yardsticker@jumphost ~]$ docker images
  REPOSITORY         TAG       IMAGE ID        CREATED      SIZE
  opnfv/yardstick    stable    a4501714757a    1 day ago    915.4 MB

Run the Docker image to get a Yardstick container::

  docker run -itd --privileged -v /var/run/docker.sock:/var/run/docker.sock -p 8888:5000 -e INSTALLER_IP=192.168.200.2 -e INSTALLER_TYPE=compass --name yardstick opnfv/yardstick:stable

Note:

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
|                                              | ``yardstick-image`` in       |
|                                              | Yardstick container, this    |
|                                              | parameter is needed.         |
+----------------------------------------------+------------------------------+
| -e INSTALLER_IP=192.168.200.2                | If you want to use yardstick |
|                                              | env prepare command(or       |
| -e INSTALLER_TYPE=compass                    | related API) to load the     |
|                                              | images that Yardstick needs, |
|                                              | these parameters should be   |
|                                              | provided.                    |
|                                              | The INSTALLER_IP and         |
|                                              | INSTALLER_TYPE are depending |
|                                              | on your OpenStack installer. |
|                                              | Currently Apex, Compass,     |
|                                              | Fuel and Joid are supported. |
|                                              | If you use other installers, |
|                                              | such as devstack, these      |
|                                              | parameters can be ignores.   |
+----------------------------------------------+------------------------------+
| -p 8888:5000                                 | If you want to call          |
|                                              | Yardstick API out of         |
|                                              | Yardstick container, this    |
|                                              | parameter is needed.         |
+----------------------------------------------+------------------------------+
| -v /var/run/docker.sock:/var/run/docker.sock | If you want to use yardstick |
|                                              | env grafana/influxdb to      |
|                                              | create a grafana/influxdb    |
|                                              | container out of Yardstick   |
|                                              | container, this parameter is |
|                                              | needed.                      |
+----------------------------------------------+------------------------------+
| --name yardstick                             | The name for this container, |
|                                              | not needed and can be        |
|                                              | defined by the user.         |
+----------------------------------------------+------------------------------+

Configure the Yardstick container environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are three ways to configure environments for running Yardstick, which will be shown in the following sections. Before that, enter the Yardstick container::

  docker exec -it yardstick /bin/bash

and then configure Yardstick environments in the Yardstick container.

The first way (**recommended**)
###################################

In the Yardstick container, the Yardstick repository is located in the ``/home/opnfv/repos`` directory. Yardstick provides a CLI to prepare OpenStack environment variables and create Yardstick flavor and guest images automatically::

  yardstick env prepare

**NOTE**: The above command works for four OPNFV installers -- **Apex**, **Compass**, **Fuel** and **Joid**.
For Non-OPNFV installer OpenStack environment, the above command can also be used to configure the environment.
But before running the above command in a Non-OPNFV installer environment, it is necessary to create the /etc/yardstick/openstack.creds file and
save OpenStack environment variables in it. For details of the required OpenStack environment variables please refer to
section **Export OpenStack environment variables**

The env prepare command may take up to 6-8 minutes to finish building
yardstick-image and other environment preparation. Meanwhile if you wish to
monitor the env prepare process, you can enter the Yardstick container in a new
terminal window and execute the following command::

  tail -f /var/log/yardstick/uwsgi.log


The second way
################

Export OpenStack environment variables
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

Before running Yardstick it is necessary to export OpenStack environment variables::

  source openrc

Environment variables in the ``openrc`` file have to include at least:

* ``OS_AUTH_URL``
* ``OS_USERNAME``
* ``OS_PASSWORD``
* ``OS_TENANT_NAME``
* ``EXTERNAL_NETWORK``

A sample `openrc` file may look like this::

  export OS_PASSWORD=console
  export OS_TENANT_NAME=admin
  export OS_AUTH_URL=http://172.16.1.222:35357/v2.0
  export OS_USERNAME=admin
  export OS_VOLUME_API_VERSION=2
  export EXTERNAL_NETWORK=net04_ext

Manually create Yardstick falvor and guest images
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

Before executing Yardstick test cases, make sure that Yardstick flavor and guest image are available in OpenStack. Detailed steps about creating the Yardstick flavor and building the Yardstick guest image can be found below.

Most of the sample test cases in Yardstick are using an OpenStack flavor called
``yardstick-flavor`` which deviates from the OpenStack standard ``m1.tiny`` flavor by the disk size - instead of 1GB it has 3GB. Other parameters are the same as in ``m1.tiny``.

Create ``yardstick-flavor``::

  nova flavor-create yardstick-flavor 100 512 3 1

Most of the sample test cases in Yardstick are using a guest image called
``yardstick-image`` which deviates from an Ubuntu Cloud Server image
containing all the required tools to run test cases supported by Yardstick.
Yardstick has a tool for building this custom image. It is necessary to have
``sudo`` rights to use this tool.

Also you may need install several additional packages to use this tool, by
follwing the commands below::

  sudo apt-get update && sudo apt-get install -y qemu-utils kpartx

This image can be built using the following command in the directory where Yardstick is installed::

  export YARD_IMG_ARCH='amd64'
  sudo echo "Defaults env_keep += \'YARD_IMG_ARCH\'" >> /etc/sudoers
  sudo tools/yardstick-img-modify tools/ubuntu-server-cloudimg-modify.sh

**Warning:** Before building the guest image inside the Yardstick container, make sure the container is granted with privilege. The script will create files by default in ``/tmp/workspace/yardstick`` and the files will be owned by root!

The created image can be added to OpenStack using the ``glance image-create`` or via the OpenStack Dashboard. Example command is::

  glance --os-image-api-version 1 image-create \
  --name yardstick-image --is-public true \
  --disk-format qcow2 --container-format bare \
  --file /tmp/workspace/yardstick/yardstick-image.img

.. _`Cirros 0.3.5`: http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img
.. _`Ubuntu 16.04`: https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img

Some Yardstick test cases use a `Cirros 0.3.5`_ image and/or a `Ubuntu 16.04`_ image. Add Cirros and Ubuntu images to OpenStack::

  openstack image create \
      --disk-format qcow2 \
      --container-format bare \
      --file $cirros_image_file \
      cirros-0.3.5

  openstack image create \
      --disk-format qcow2 \
      --container-format bare \
      --file $ubuntu_image_file \
      Ubuntu-16.04


The third way
################

Similar to the second way, the first step is also to `Export OpenStack environment variables`_. Then the following steps should be done.

Automatically create Yardstcik flavor and guest images
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

Yardstick has a script for automatically creating Yardstick flavor and building
Yardstick guest images. This script is mainly used for CI and can be also used in the local environment::

  source $YARDSTICK_REPO_DIR/tests/ci/load_images.sh


Delete the Yardstick container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to uninstall Yardstick, just delete the Yardstick container::

   docker stop yardstick && docker rm yardstick


Install Yardstick directly in Ubuntu
---------------------------------------

.. _install-framework:

Alternatively you can install Yardstick framework directly in Ubuntu or in an Ubuntu Docker image. No matter which way you choose to install Yardstick, the following installation steps are identical.

If you choose to use the Ubuntu Docker image, you can pull the Ubuntu
Docker image from Docker hub::

  docker pull ubuntu:16.04


Install Yardstick
^^^^^^^^^^^^^^^^^^^^^

Prerequisite preparation::

  apt-get update && apt-get install -y git python-setuptools python-pip
  easy_install -U setuptools==30.0.0
  pip install appdirs==1.4.0
  pip install virtualenv

Create a virtual environment::

  virtualenv ~/yardstick_venv
  export YARDSTICK_VENV=~/yardstick_venv
  source ~/yardstick_venv/bin/activate

Download the source code and install Yardstick from it::

  git clone https://gerrit.opnfv.org/gerrit/yardstick
  export YARDSTICK_REPO_DIR=~/yardstick
  cd yardstick
  ./install.sh


Configure the Yardstick environment (**Todo**)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For installing Yardstick directly in Ubuntu, the ``yardstick env`` command is not available. You need to prepare OpenStack environment variables and create Yardstick flavor and guest images manually.


Uninstall Yardstick
^^^^^^^^^^^^^^^^^^^^^^

For unistalling Yardstick, just delete the virtual environment::

  rm -rf ~/yardstick_venv


Verify the installation
-----------------------------

It is recommended to verify that Yardstick was installed successfully
by executing some simple commands and test samples. Before executing Yardstick
test cases make sure ``yardstick-flavor`` and ``yardstick-image`` can be found in OpenStack and the ``openrc`` file is sourced. Below is an example
invocation of Yardstick ``help`` command and ``ping.py`` test sample::

  yardstick -h
  yardstick task start samples/ping.yaml

**NOTE:** The above commands could be run in both the Yardstick container and the Ubuntu directly.

Each testing tool supported by Yardstick has a sample configuration file.
These configuration files can be found in the ``samples`` directory.

Default location for the output is ``/tmp/yardstick.out``.


Deploy InfluxDB and Grafana using Docker
-------------------------------------------

Without InfluxDB, Yardstick stores results for runnning test case in the file
``/tmp/yardstick.out``. However, it's unconvenient to retrieve and display
test results. So we will show how to use InfluxDB to store data and use
Grafana to display data in the following sections.

Automatically deploy InfluxDB and Grafana containers (**recommended**)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Firstly, enter the Yardstick container::

  docker exec -it yardstick /bin/bash

Secondly, create InfluxDB container and configure with the following command::

  yardstick env influxdb

Thirdly, create and configure Grafana container::

  yardstick env grafana

Then you can run a test case and visit http://host_ip:3000 (``admin``/``admin``) to see the results.

**NOTE:** Executing ``yardstick env`` command to deploy InfluxDB and Grafana requires Jumphost's docker API version => 1.24. Run the following command to check the docker API version on the Jumphost::

  docker version

Manually deploy InfluxDB and Grafana containers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You could also deploy influxDB and Grafana containers manually on the Jumphost.
The following sections show how to do.

.. pull docker images

Pull docker images
####################

::

  docker pull tutum/influxdb
  docker pull grafana/grafana

Run and configure influxDB
###############################

Run influxDB::

  docker run -d --name influxdb \
  -p 8083:8083 -p 8086:8086 --expose 8090 --expose 8099 \
  tutum/influxdb
  docker exec -it influxdb bash

Configure influxDB::

  influx
  >CREATE USER root WITH PASSWORD 'root' WITH ALL PRIVILEGES
  >CREATE DATABASE yardstick;
  >use yardstick;
  >show MEASUREMENTS;

Run and configure Grafana
###############################

Run Grafana::

  docker run -d --name grafana -p 3000:3000 grafana/grafana

Log on http://{YOUR_IP_HERE}:3000 using ``admin``/``admin`` and configure database resource to be ``{YOUR_IP_HERE}:8086``.

.. image:: images/Grafana_config.png
   :width: 800px
   :alt: Grafana data source configration

Configure ``yardstick.conf``
##############################

::

  docker exec -it yardstick /bin/bash
  cp etc/yardstick/yardstick.conf.sample /etc/yardstick/yardstick.conf
  vi /etc/yardstick/yardstick.conf

Modify ``yardstick.conf``::

  [DEFAULT]
  debug = True
  dispatcher = influxdb

  [dispatcher_influxdb]
  timeout = 5
  target = http://{YOUR_IP_HERE}:8086
  db_name = yardstick
  username = root
  password = root

Now you can run Yardstick test cases and store the results in influxDB.


Deploy InfluxDB and Grafana directly in Ubuntu (**Todo**)
-----------------------------------------------------------


Run Yardstick in a local environment
------------------------------------

We also have a guide about how to run Yardstick in a local environment.
This work is contributed by Tapio Tallgren.
You can find this guide at `here <https://wiki.opnfv.org/display/yardstick/How+to+run+Yardstick+in+a+local+environment>`_.


Create a test suite for Yardstick
------------------------------------

A test suite in yardstick is a yaml file which include one or more test cases.
Yardstick is able to support running test suite task, so you can customize your
own test suite and run it in one task.

``tests/opnfv/test_suites`` is the folder where Yardstick puts CI test suite. A typical test suite is like below (the ``fuel_test_suite.yaml`` example)::

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

As you can see, there are two test cases in the ``fuel_test_suite.yaml``. The
``schema`` and the ``name`` must be specified. The test cases should be listed
via the tag ``test_cases`` and their relative path is also marked via the tag
``test_cases_dir``.

Yardstick test suite also supports constraints and task args for each test
case. Here is another sample (the ``os-nosdn-nofeature-ha.yaml`` example) to
show this, which is digested from one big test suite::

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

As you can see in test case ``opnfv_yardstick_tc043.yaml``, there are two
tags, ``constraint`` and ``task_args``. ``constraint`` is to specify which
installer or pod it can be run in the CI environment. ``task_args`` is to
specify the task arguments for each pod.

All in all, to create a test suite in Yardstick, you just need to create a
yaml file and add test cases, constraint or task arguments if necessary.


Proxy Support (**Todo**)
---------------------------

