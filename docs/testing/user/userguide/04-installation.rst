.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB, Huawei Technologies Co.,Ltd and others.

======================
Yardstick Installation
======================


Yardstick supports installation by Docker or directly in Ubuntu. The
installation procedure for Docker and direct installation are detailed in
the sections below.

To use Yardstick you should have access to an OpenStack environment, with at
least Nova, Neutron, Glance, Keystone and Heat installed.

The steps needed to run Yardstick are:

1. Install Yardstick.
2. Load OpenStack environment variables.
3. Create Yardstick flavor.
4. Build a guest image and load it into the OpenStack environment.
5. Create the test configuration ``.yaml`` file and run the test case/suite.


Prerequisites
-------------

The OPNFV deployment is out of the scope of this document and can be found in
`User Guide & Configuration Guide`_. The OPNFV platform is considered as the
System Under Test (SUT) in this document.

Several prerequisites are needed for Yardstick:

1. A Jumphost to run Yardstick on
2. A Docker daemon or a virtual environment installed on the Jumphost
3. A public/external network created on the SUT
4. Connectivity from the Jumphost to the SUT public/external network

.. note:: *Jumphost* refers to any server which meets the previous
requirements. Normally it is the same server from where the OPNFV
deployment has been triggered.

.. warning:: Connectivity from Jumphost is essential and it is of paramount
importance to make sure it is working before even considering to install
and run Yardstick. Make also sure you understand how your networking is
designed to work.

.. note:: If your Jumphost is operating behind a company http proxy and/or
Firewall, please first consult `Proxy Support`_ section which is towards the
end of this document. That section details some tips/tricks which *may* be of
help in a proxified environment.


Install Yardstick using Docker (first option) (**recommended**)
---------------------------------------------------------------

Yardstick has a Docker image. It is recommended to use this Docker image to run
Yardstick test.

Prepare the Yardstick container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install docker on your guest system with the following command, if not done
yet::

   wget -qO- https://get.docker.com/ | sh

Pull the Yardstick Docker image (``opnfv/yardstick``) from the public dockerhub
registry under the OPNFV account in dockerhub_, with the following docker
command::

   sudo -EH docker pull opnfv/yardstick:stable

After pulling the Docker image, check that it is available with the
following docker command::

   [yardsticker@jumphost ~]$ docker images
   REPOSITORY         TAG       IMAGE ID        CREATED      SIZE
   opnfv/yardstick    stable    a4501714757a    1 day ago    915.4 MB

Run the Docker image to get a Yardstick container::

   docker run -itd --privileged -v /var/run/docker.sock:/var/run/docker.sock \
      -p 8888:5000 --name yardstick opnfv/yardstick:stable

.. table:: Description of the parameters used with ``docker run`` command

   ======================= ====================================================
   Parameters              Detail
   ======================= ====================================================
   -itd                    -i: interactive, Keep STDIN open even if not
                           attached
                           -t: allocate a pseudo-TTY detached mode, in the
                           background
   ======================= ====================================================
   --privileged            If you want to build ``yardstick-image`` in
                           Yardstick container, this parameter is needed
   ======================= ====================================================
   -p 8888:5000            Redirect the a host port (8888) to a container port
                           (5000)
   ======================= ====================================================
   -v /var/run/docker.sock If you want to use yardstick env grafana/influxdb to
   :/var/run/docker.sock   create a grafana/influxdb container out of Yardstick
                           container
   ======================= ====================================================
   --name yardstick        The name for this container

If the host is restarted
^^^^^^^^^^^^^^^^^^^^^^^^

The yardstick container must be started if the host is rebooted::

    docker start yardstick

Configure the Yardstick container environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are three ways to configure environments for running Yardstick, explained
in the following sections. Before that, access the Yardstick container::

   docker exec -it yardstick /bin/bash

and then configure Yardstick environments in the Yardstick container.

Using the CLI command ``env prepare`` (first way) (**recommended**)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the Yardstick container, the Yardstick repository is located in the
``/home/opnfv/repos`` directory. Yardstick provides a CLI to prepare OpenStack
environment variables and create Yardstick flavor and guest images
automatically::

   yardstick env prepare

.. note:: Since Euphrates release, the above command will not be able to
automatically configure the ``/etc/yardstick/openstack.creds`` file. So before
running the above command, it is necessary to create the
``/etc/yardstick/openstack.creds`` file and save OpenStack environment
variables into it manually. If you have the openstack credential file saved
outside the Yardstick Docker container, you can do this easily by mapping the
credential file into Yardstick container using::

   '-v /path/to/credential_file:/etc/yardstick/openstack.creds'

when running the Yardstick container. For details of the required OpenStack
environment variables please refer to section `Export OpenStack environment
variables`_.

The ``env prepare`` command may take up to 6-8 minutes to finish building
yardstick-image and other environment preparation. Meanwhile if you wish to
monitor the env prepare process, you can enter the Yardstick container in a new
terminal window and execute the following command::

  tail -f /var/log/yardstick/uwsgi.log


Manually exporting the env variables and initializing OpenStack (second way)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Export OpenStack environment variables
######################################

Before running Yardstick it is necessary to export OpenStack environment
variables::

   source openrc

Environment variables in the ``openrc`` file have to include at least::

   OS_AUTH_URL
   OS_USERNAME
   OS_PASSWORD
   OS_PROJECT_NAME
   EXTERNAL_NETWORK

A sample ``openrc`` file may look like this::

  export OS_PASSWORD=console
  export OS_PROJECT_NAME=admin
  export OS_AUTH_URL=http://172.16.1.222:35357/v2.0
  export OS_USERNAME=admin
  export OS_VOLUME_API_VERSION=2
  export EXTERNAL_NETWORK=net04_ext


Manual creation of Yardstick flavor and guest images
####################################################

Before executing Yardstick test cases, make sure that Yardstick flavor and
guest image are available in OpenStack. Detailed steps about creating the
Yardstick flavor and building the Yardstick guest image can be found below.

Most of the sample test cases in Yardstick are using an OpenStack flavor called
``yardstick-flavor`` which deviates from the OpenStack standard ``m1.tiny``
flavor by the disk size; instead of 1GB it has 3GB. Other parameters are the
same as in ``m1.tiny``.

Create ``yardstick-flavor``::

   openstack flavor create --disk 3 --vcpus 1 --ram 512 --swap 100 \
      yardstick-flavor

Most of the sample test cases in Yardstick are using a guest image called
``yardstick-image`` which deviates from an Ubuntu Cloud Server image
containing all the required tools to run test cases supported by Yardstick.
Yardstick has a tool for building this custom image. It is necessary to have
``sudo`` rights to use this tool.

Also you may need install several additional packages to use this tool, by
follwing the commands below::

   sudo -EH apt-get update && sudo -EH apt-get install -y qemu-utils kpartx

This image can be built using the following command in the directory where
Yardstick is installed::

   export YARD_IMG_ARCH='amd64'
   echo "Defaults env_keep += \'YARD_IMG_ARCH\'" | sudo tee --append \
      /etc/sudoers > /dev/null
   sudo -EH tools/yardstick-img-modify tools/ubuntu-server-cloudimg-modify.sh

.. warning:: Before building the guest image inside the Yardstick container,
make sure the container is granted with privilege. The script will create files
by default in ``/tmp/workspace/yardstick`` and the files will be owned by root.

The created image can be added to OpenStack using the OpenStack client or via
the OpenStack Dashboard::

   openstack image create --disk-format qcow2 --container-format bare \
      --public --file /tmp/workspace/yardstick/yardstick-image.img \
       yardstick-image


Some Yardstick test cases use a `Cirros 0.3.5`_ image and/or a `Ubuntu 16.04`_
image. Add Cirros and Ubuntu images to OpenStack::

   openstack image create --disk-format qcow2 --container-format bare \
      --public --file $cirros_image_file cirros-0.3.5
   openstack image create --disk-format qcow2 --container-format bare \
      --file $ubuntu_image_file Ubuntu-16.04


Automatic initialization of OpenStack (third way)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similar to the second way, the first step is also to
`Export OpenStack environment variables`_. Then the following steps should be
done.

Automatic creation of Yardstick flavor and guest images
#######################################################

Yardstick has a script for automatically creating Yardstick flavor and building
Yardstick guest images. This script is mainly used for CI and can be also used
in the local environment::

   source $YARDSTICK_REPO_DIR/tests/ci/load_images.sh


The Yardstick container GUI
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Euphrates release, Yardstick implemented a GUI for Yardstick Docker
container. After booting up Yardstick container, you can visit the GUI at
``<container_host_ip>:8888/gui/index.html``.

For usage of Yardstick GUI, please watch our demo video at
`Yardstick GUI demo`_.

.. note:: The Yardstick GUI is still in development, the GUI layout and
features may change.

Delete the Yardstick container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to uninstall Yardstick, just delete the Yardstick container::

   sudo docker stop yardstick && docker rm yardstick



Install Yardstick directly in Ubuntu (second option)
----------------------------------------------------

.. _install-framework:

Alternatively you can install Yardstick framework directly in Ubuntu or in an
Ubuntu Docker image. No matter which way you choose to install Yardstick, the
following installation steps are identical.

If you choose to use the Ubuntu Docker image, you can pull the Ubuntu
Docker image from Docker hub::

   sudo -EH docker pull ubuntu:16.04


Install Yardstick
^^^^^^^^^^^^^^^^^

Prerequisite preparation::

   sudo -EH apt-get update && sudo -EH apt-get install -y \
      git python-setuptools python-pip
   sudo -EH easy_install -U setuptools==30.0.0
   sudo -EH pip install appdirs==1.4.0
   sudo -EH pip install virtualenv

Download the source code and install Yardstick from it::

   git clone https://gerrit.opnfv.org/gerrit/yardstick
   export YARDSTICK_REPO_DIR=~/yardstick
   cd ~/yardstick
   sudo -EH ./install.sh

If the host is ever restarted, nginx and uwsgi need to be restarted::

   service nginx restart
   uwsgi -i /etc/yardstick/yardstick.ini

Configure the Yardstick environment (**Todo**)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For installing Yardstick directly in Ubuntu, the ``yardstick env`` command is
not available. You need to prepare OpenStack environment variables and create
Yardstick flavor and guest images manually.


Uninstall Yardstick
^^^^^^^^^^^^^^^^^^^

For uninstalling Yardstick, just delete the virtual environment::

   rm -rf ~/yardstick_venv


Install Yardstick directly in OpenSUSE
--------------------------------------

.. _install-framework:

You can install Yardstick framework directly in OpenSUSE.


Install Yardstick
^^^^^^^^^^^^^^^^^

Prerequisite preparation::

   sudo -EH zypper -n install -y gcc \
      wget \
      git \
      sshpass \
      qemu-tools \
      kpartx \
      libffi-devel \
      libopenssl-devel \
      python \
      python-devel \
      python-virtualenv \
      libxml2-devel \
      libxslt-devel \
      python-setuptools-git

Create a virtual environment::

   virtualenv ~/yardstick_venv
   export YARDSTICK_VENV=~/yardstick_venv
   source ~/yardstick_venv/bin/activate
   sudo -EH easy_install -U setuptools

Download the source code and install Yardstick from it::

   git clone https://gerrit.opnfv.org/gerrit/yardstick
   export YARDSTICK_REPO_DIR=~/yardstick
   cd yardstick
   sudo -EH python setup.py install
   sudo -EH pip install -r requirements.txt

Install missing python modules::

   sudo -EH pip install pyyaml \
      oslo_utils \
      oslo_serialization \
      oslo_config \
      paramiko \
      python.heatclient \
      python.novaclient \
      python.glanceclient \
      python.neutronclient \
      scp \
      jinja2


Configure the Yardstick environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Source the OpenStack environment variables::

   source DEVSTACK_DIRECTORY/openrc

Export the Openstack external network. The default installation of Devstack
names the external network public::

   export EXTERNAL_NETWORK=public
   export OS_USERNAME=demo

Change the API version used by Yardstick to v2.0 (the devstack openrc sets it
to v3)::

   export OS_AUTH_URL=http://PUBLIC_IP_ADDRESS:5000/v2.0


Uninstall Yardstick
^^^^^^^^^^^^^^^^^^^

For unistalling Yardstick, just delete the virtual environment::

   rm -rf ~/yardstick_venv


Verify the installation
-----------------------

It is recommended to verify that Yardstick was installed successfully
by executing some simple commands and test samples. Before executing Yardstick
test cases make sure ``yardstick-flavor`` and ``yardstick-image`` can be found
in OpenStack and the ``openrc`` file is sourced. Below is an example invocation
of Yardstick ``help`` command and ``ping.py`` test sample::

   yardstick -h
   yardstick task start samples/ping.yaml

.. note:: The above commands could be run in both the Yardstick container and
the Ubuntu directly.

Each testing tool supported by Yardstick has a sample configuration file.
These configuration files can be found in the ``samples`` directory.

Default location for the output is ``/tmp/yardstick.out``.


Deploy InfluxDB and Grafana using Docker
----------------------------------------

Without InfluxDB, Yardstick stores results for running test case in the file
``/tmp/yardstick.out``. However, it's inconvenient to retrieve and display
test results. So we will show how to use InfluxDB to store data and use
Grafana to display data in the following sections.

Automatic deployment of InfluxDB and Grafana containers (**recommended**)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Firstly, enter the Yardstick container::

   sudo -EH docker exec -it yardstick /bin/bash

Secondly, create InfluxDB container and configure with the following command::

   yardstick env influxdb

Thirdly, create and configure Grafana container::

   yardstick env grafana

Then you can run a test case and visit http://host_ip:1948
(``admin``/``admin``) to see the results.

.. note:: Executing ``yardstick env`` command to deploy InfluxDB and Grafana
requires Jumphost's docker API version => 1.24. Run the following command to
check the docker API version on the Jumphost::

   docker version


Manual deployment of InfluxDB and Grafana containers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also deploy influxDB and Grafana containers manually on the Jumphost.
The following sections show how to do.

Pull docker images::

   sudo -EH docker pull tutum/influxdb
   sudo -EH docker pull grafana/grafana

Run influxDB::

   sudo -EH docker run -d --name influxdb \
      -p 8083:8083 -p 8086:8086 --expose 8090 --expose 8099 \
      tutum/influxdb
   docker exec -it influxdb bash

Configure influxDB::

   influx
      >CREATE USER root WITH PASSWORD 'root' WITH ALL PRIVILEGES
      >CREATE DATABASE yardstick;
      >use yardstick;
      >show MEASUREMENTS;

Run Grafana::

   sudo -EH docker run -d --name grafana -p 1948:3000 grafana/grafana

Log on http://{YOUR_IP_HERE}:1948 using ``admin``/``admin`` and configure
database resource to be ``{YOUR_IP_HERE}:8086``.

.. image:: images/Grafana_config.png
   :width: 800px
   :alt: Grafana data source configuration

Configure ``yardstick.conf``::

   sudo -EH docker exec -it yardstick /bin/bash
   sudo cp etc/yardstick/yardstick.conf.sample /etc/yardstick/yardstick.conf
   sudo vi /etc/yardstick/yardstick.conf

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
---------------------------------------------------------


Yardstick common CLI
--------------------

List test cases
^^^^^^^^^^^^^^^

``yardstick testcase list``: This command line would list all test cases in
Yardstick. It would show like below::

   +---------------------------------------------------------------------------------------
   | Testcase Name         | Description
   +---------------------------------------------------------------------------------------
   | opnfv_yardstick_tc001 | Measure network throughput using pktgen
   | opnfv_yardstick_tc002 | measure network latency using ping
   | opnfv_yardstick_tc005 | Measure Storage IOPS, throughput and latency using fio.
   ...
   +---------------------------------------------------------------------------------------


Show a test case config file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Take opnfv_yardstick_tc002 for an example. This test case measure network
latency. You just need to type in ``yardstick testcase show
opnfv_yardstick_tc002``, and the console would show the config yaml of this
test case::

   ---

   schema: "yardstick:task:0.1"
   description: >
      Yardstick TC002 config file;
      measure network latency using ping;

   {% set image = image or "cirros-0.3.5" %}

   {% set provider = provider or none %}
   {% set physical_network = physical_network or 'physnet1' %}
   {% set segmentation_id = segmentation_id or none %}
   {% set packetsize = packetsize or 100 %}

   scenarios:
   {% for i in range(2) %}
   -
    type: Ping
    options:
      packetsize: {{packetsize}}
    host: athena.demo
    target: ares.demo

    runner:
      type: Duration
      duration: 60
      interval: 10

    sla:
      max_rtt: 10
      action: monitor
   {% endfor %}

   context:
    name: demo
    image: {{image}}
    flavor: yardstick-flavor
    user: cirros

    placement_groups:
      pgrp1:
        policy: "availability"

    servers:
      athena:
        floating_ip: true
        placement: "pgrp1"
      ares:
        placement: "pgrp1"

    networks:
      test:
        cidr: '10.0.1.0/24'
        {% if provider == "vlan" %}
        provider: {{provider}}
        physical_network: {{physical_network}}å
          {% if segmentation_id %}
        segmentation_id: {{segmentation_id}}
          {% endif %}
        {% endif %}


Start a task to run yardstick test case
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want run a test case, then you need to use ``yardstick task start
<test_case_path>`` this command support some parameters as below::

   +---------------------+--------------------------------------------------+
   | Parameters          | Detail                                           |
   +=====================+==================================================+
   | -d                  | show debug log of yardstick running              |
   |                     |                                                  |
   +---------------------+--------------------------------------------------+
   | --task-args         | If you want to customize test case parameters,   |
   |                     | use "--task-args" to pass the value. The format  |
   |                     | is a json string with parameter key-value pair.  |
   |                     |                                                  |
   +---------------------+--------------------------------------------------+
   | --task-args-file    | If you want to use yardstick                     |
   |                     | env prepare command(or                           |
   |                     | related API) to load the                         |
   +---------------------+--------------------------------------------------+
   | --parse-only        |                                                  |
   |                     |                                                  |
   |                     |                                                  |
   +---------------------+--------------------------------------------------+
   | --output-file \     | Specify where to output the log. if not pass,    |
   | OUTPUT_FILE_PATH    | the default value is                             |
   |                     | "/tmp/yardstick/yardstick.log"                   |
   |                     |                                                  |
   +---------------------+--------------------------------------------------+
   | --suite \           | run a test suite, TEST_SUITE_PATH specify where  |
   | TEST_SUITE_PATH     | the test suite locates                           |
   |                     |                                                  |
   +---------------------+--------------------------------------------------+


Run Yardstick in a local environment
------------------------------------

We also have a guide about how to run Yardstick in a local environment.
This work is contributed by Tapio Tallgren.
You can find this guide at `How to run Yardstick in a local environment`_.


Create a test suite for Yardstick
------------------------------------

A test suite in yardstick is a yaml file which include one or more test cases.
Yardstick is able to support running test suite task, so you can customize your
own test suite and run it in one task.

``tests/opnfv/test_suites`` is the folder where Yardstick puts CI test suite.
A typical test suite is like below (the ``fuel_test_suite.yaml`` example)::

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


Proxy Support
-------------

To configure the Jumphost to access Internet through a proxy its necessary to
export several variables to the environment, contained in the following
script::

   #!/bin/sh
   _proxy=<proxy_address>
   _proxyport=<proxy_port>
   _ip=$(hostname -I | awk '{print $1}')

   export ftp_proxy=http://$_proxy:$_proxyport
   export FTP_PROXY=http://$_proxy:$_proxyport
   export http_proxy=http://$_proxy:$_proxyport
   export HTTP_PROXY=http://$_proxy:$_proxyport
   export https_proxy=http://$_proxy:$_proxyport
   export HTTPS_PROXY=http://$_proxy:$_proxyport
   export no_proxy=127.0.0.1,localhost,$_ip,$(hostname),<.localdomain>
   export NO_PROXY=127.0.0.1,localhost,$_ip,$(hostname),<.localdomain>

To enable Internet access from a container using ``docker``, depends on the OS
version. On Ubuntu 14.04 LTS, which uses SysVinit, ``/etc/default/docker`` must
be modified::

   .......
   # If you need Docker to use an HTTP proxy, it can also be specified here.
   export http_proxy="http://<proxy_address>:<proxy_port>/"
   export https_proxy="https://<proxy_address>:<proxy_port>/"

Then its necessary to restart the ``docker`` service::

   sudo -EH service docker restart

In Ubuntu 16.04 LTS, which uses Systemd, its necessary to create a drop-in
directory::

   sudo mkdir /etc/systemd/system/docker.service.d

Then, the proxy configuration will be stored in the following file::

   # cat /etc/systemd/system/docker.service.d/http-proxy.conf
   [Service]
   Environment="HTTP_PROXY=https://<proxy_address>:<proxy_port>/"
   Environment="HTTPS_PROXY=https://<proxy_address>:<proxy_port>/"
   Environment="NO_PROXY=localhost,127.0.0.1,<localaddress>,<.localdomain>"

The changes need to be flushed and the ``docker`` service restarted::

   sudo systemctl daemon-reload
   sudo systemctl restart docker

Any container is already created won't contain these modifications. If needed,
stop and delete the container::

   sudo docker stop yardstick
   sudo docker rm yardstick

.. warning:: Be careful, the above ``rm`` command will delete the container
completely. Everything on this container will be lost.

Then follow the previous instructions `Prepare the Yardstick container`_ to
rebuild the Yardstick container.


References
----------

.. _`User Guide & Configuration Guide`: http://docs.opnfv.org/en/latest/release/userguide.introduction.html
.. _dockerhub: https://hub.docker.com/r/opnfv/yardstick/
.. _`Cirros 0.3.5`: http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img
.. _`Ubuntu 16.04`: https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img
.. _`Yardstick GUI demo`: https://www.youtube.com/watch?v=M3qbJDp6QBk
.. _`How to run Yardstick in a local environment`: https://wiki.opnfv.org/display/yardstick/How+to+run+Yardstick+in+a+local+environment
