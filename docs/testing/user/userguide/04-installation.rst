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

Description of the parameters used with ``docker run`` command

  +------------------------+--------------------------------------------------+
  | Parameters             | Detail                                           |
  +========================+==================================================+
  | -itd                   |  -i: interactive, Keep STDIN open even if not    |
  |                        |  attached                                        |
  |                        +--------------------------------------------------+
  |                        |  -t: allocate a pseudo-TTY detached mode, in the |
  |                        |  background                                      |
  +------------------------+--------------------------------------------------+
  | --privileged           | If you want to build ``yardstick-image`` in      |
  |                        | Yardstick container, this parameter is needed    |
  +------------------------+--------------------------------------------------+
  | -p 8888:5000           | Redirect the a host port (8888) to a container   |
  |                        | port (5000)                                      |
  +------------------------+--------------------------------------------------+
  | -v /var/run/docker.sock| If you want to use yardstick env                 |
  | :/var/run/docker.sock  | grafana/influxdb to create a grafana/influxdb    |
  |                        | container out of Yardstick container             |
  +------------------------+--------------------------------------------------+
  | --name yardstick       | The name for this container                      |
  +------------------------+--------------------------------------------------+


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
