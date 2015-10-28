..
   TODO As things will change, then this document has to be revised before the
   next release. Steps:
   1. Verify that the instructions below are correct and have not been changed.
   2. Add everything that is currently missing and should be included in this document.
   3. Make sure each title has a paragraph or an introductory sentence under it.
   4. Make sure each sentence is grammatically correct and easily understandable.
   5. Remove this comment section.

Installation
==============

Yardstick currently supports installation on Ubuntu 14.04 or by using a Docker
image. Detailed steps about installing Yardstick using both of these options
can be found below.

To use Yardstick you should have access to an OpenStack environment,
with at least Nova, Neutron, Glance, Keystone and Heat installed.

The steps needed to run Yardstick are:

1. Install Yardstick and create the test configuration .yaml file.
2. Build a guest image and load the image into the OpenStack environment.
3. Create a Neutron external network and load OpenStack environment variables.
4. Run the test case.


Installing Yardstick on Ubuntu 14.04
------------------------------------

.. _install-framework:

Installing Yardstick framework
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Install dependencies:
::

  sudo apt-get install python-virtualenv python-dev
  sudo apt-get install libffi-dev libssl-dev git

Create a python virtual environment, source it and update setuptools:
::

  virtualenv ~/yardstick_venv
  source ~/yardstick_venv/bin/activate
  easy_install -U setuptools

Download source code and install python dependencies:
::

  git clone https://gerrit.opnfv.org/gerrit/yardstick
  cd yardstick
  python setup.py install

There is also a YouTube video, showing the above steps:

.. image:: http://img.youtube.com/vi/4S4izNolmR0/0.jpg
   :alt: http://www.youtube.com/watch?v=4S4izNolmR0
   :target: http://www.youtube.com/watch?v=4S4izNolmR0

Installing extra tools
^^^^^^^^^^^^^^^^^^^^^^
yardstick-plot
""""""""""""""
Yardstick has an internal plotting tool ``yardstick-plot``, which can be installed
using the following command:
::

  python setup.py develop easy_install yardstick[plot]

.. _guest-image:

Building a guest image
^^^^^^^^^^^^^^^^^^^^^^
Yardstick has a tool for building an Ubuntu Cloud Server image containing all
the required tools to run test cases supported by Yardstick. It is necessary to
have sudo rights to use this tool.

This image can be built using the following command while in the directory where
Yardstick is installed (``~/yardstick`` if the framework is installed
by following the commands above):
::

  sudo ./tools/yardstick-img-modify tools/ubuntu-server-cloudimg-modify.sh

**Warning:** the script will create files by default in:
``/tmp/workspace/yardstick`` and the files will be owned by root!

The created image can be added to OpenStack using the ``glance image-create`` or
via the OpenStack Dashboard.

Example command:
::

  glance image-create --name yardstick-trusty-server --is-public true \
  --disk-format qcow2 --container-format bare \
  --file /tmp/workspace/yardstick/yardstick-trusty-server.img


Installing Yardstick using Docker
---------------------------------

Yardstick has two Docker images, first one (**Yardstick-framework**) serves as a
replacement for installing the Yardstick framework in a virtual environment (for
example as done in :ref:`install-framework`), while the other image is mostly for
CI purposes (**Yardstick-CI**).

Yardstick-framework image
^^^^^^^^^^^^^^^^^^^^^^^^^
Download the source code:

::

  git clone https://gerrit.opnfv.org/gerrit/yardstick

Build the Docker image and tag it as *yardstick-framework*:

::

  cd yardstick
  docker build -t yardstick-framework .

Run the Docker instance:

::

  docker run --name yardstick_instance -i -t yardstick-framework

To build a guest image for Yardstick, see :ref:`guest-image`.

Yardstick-CI image
^^^^^^^^^^^^^^^^^^
Pull the Yardstick-CI Docker image from Docker hub:

::

  docker pull opnfv/yardstick-ci

Run the Docker image:

::

  docker run \
   --privileged=true \
    --rm \
    -t \
    -e "INSTALLER_TYPE=${INSTALLER_TYPE}" \
    -e "INSTALLER_IP=${INSTALLER_IP}" \
    opnfv/yardstick-ci \
    run_benchmarks

Where ``${INSTALLER_TYPE}`` can be fuel, foreman or compass and ``${INSTALLER_IP}``
is the installer master node IP address (i.e. 10.20.0.2 is default for fuel).

Basic steps performed by the **Yardstick-CI** container:

1. clone yardstick and releng repos
2. setup OS credentials (releng scripts)
3. install yardstick and dependencies
4. build yardstick cloud image and upload it to glance
5. upload cirros-0.3.3 cloud image to glance
6. run yardstick test scenarios
7. cleanup


OpenStack parameters and credentials
------------------------------------

Yardstick-flavor
^^^^^^^^^^^^^^^^
Most of the sample test cases in Yardstick are using an OpenStack flavor called
*yardstick-flavor* which deviates from the OpenStack standard m1.tiny flavor by the
disk size - instead of 1GB it has 3GB. Other parameters are the same as in m1.tiny.

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

Yardstick default key pair
^^^^^^^^^^^^^^^^^^^^^^^^^^
Yardstick uses a SSH key pair to connect to the guest image. This key pair can
be found in the ``resources/files`` directory. To run the ``ping-hot.yaml`` test
sample, this key pair needs to be imported to the OpenStack environment.


Examples and verifying the install
----------------------------------

It is recommended to verify that Yardstick was installed successfully
by executing some simple commands and test samples. Below is an example invocation
of yardstick help command and ping.py test sample:
::

  yardstick –h
  yardstick task start samples/ping.yaml

Each testing tool supported by Yardstick has a sample configuration file.
These configuration files can be found in the **samples** directory.

Example invocation of ``yardstick-plot`` tool:
::

  yardstick-plot -i /tmp/yardstick.out -o /tmp/plots/

Default location for the output is ``/tmp/yardstick.out``.

More info about the tool can be found by executing:
::

  yardstick-plot -h
