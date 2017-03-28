.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB, Huawei Technologies Co.,Ltd and others.

===================================
Installing a plug-in into Yardstick
===================================


Abstract
========

Yardstick provides a ``plugin`` CLI command to support integration with other
OPNFV testing projects. Below is an example invocation of Yardstick plugin
command and Storperf plug-in sample.


Installing Storperf into Yardstick
==================================

Storperf is delivered as a Docker container from
https://hub.docker.com/r/opnfv/storperf/tags/.

There are two possible methods for installation in your environment:

* Run container on Jump Host
* Run container in a VM

In this introduction we will install Storperf on Jump Host.


Step 0: Environment preparation
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

Running Storperf on Jump Host
Requirements:

* Docker must be installed
* Jump Host must have access to the OpenStack Controller API
* Jump Host must have internet connectivity for downloading docker image
* Enough floating IPs must be available to match your agent count

Before installing Storperf into yardstick you need to check your openstack
environment and other dependencies:

1. Make sure docker is installed.
2. Make sure Keystone, Nova, Neutron, Glance, Heat are installed correctly.
3. Make sure Jump Host have access to the OpenStack Controller API.
4. Make sure Jump Host must have internet connectivity for downloading docker image.
5. You need to know where to get basic openstack Keystone authorization info, such as
   OS_PASSWORD, OS_TENANT_NAME, OS_AUTH_URL, OS_USERNAME.
6. To run a Storperf container, you need to have OpenStack Controller environment
   variables defined and passed to Storperf container. The best way to do this is to
   put environment variables in a "storperf_admin-rc" file. The storperf_admin-rc
   should include credential environment variables at least:

* OS_AUTH_URL
* OS_USERNAME
* OS_PASSWORD
* OS_TENANT_ID
* OS_TENANT_NAME
* OS_PROJECT_NAME
* OS_PROJECT_ID
* OS_USER_DOMAIN_ID

*Yardstick* has a "prepare_storperf_admin-rc.sh" script which can be used to
generate the "storperf_admin-rc" file, this script is located at
test/ci/prepare_storperf_admin-rc.sh

::

  #!/bin/bash
  # Prepare storperf_admin-rc for StorPerf.
  AUTH_URL=${OS_AUTH_URL}
  USERNAME=${OS_USERNAME:-admin}
  PASSWORD=${OS_PASSWORD:-console}

  TENANT_NAME=${OS_TENANT_NAME:-admin}
  TENANT_ID=`openstack project show admin|grep '\bid\b' |awk -F '|' '{print $3}'|sed -e 's/^[[:space:]]*//'`
  PROJECT_NAME=${OS_PROJECT_NAME:-$TENANT_NAME}
  PROJECT_ID=`openstack project show admin|grep '\bid\b' |awk -F '|' '{print $3}'|sed -e 's/^[[:space:]]*//'`
  USER_DOMAIN_ID=${OS_USER_DOMAIN_ID:-default}

  rm -f ~/storperf_admin-rc
  touch ~/storperf_admin-rc

  echo "OS_AUTH_URL="$AUTH_URL >> ~/storperf_admin-rc
  echo "OS_USERNAME="$USERNAME >> ~/storperf_admin-rc
  echo "OS_PASSWORD="$PASSWORD >> ~/storperf_admin-rc
  echo "OS_PROJECT_NAME="$PROJECT_NAME >> ~/storperf_admin-rc
  echo "OS_PROJECT_ID="$PROJECT_ID >> ~/storperf_admin-rc
  echo "OS_TENANT_NAME="$TENANT_NAME >> ~/storperf_admin-rc
  echo "OS_TENANT_ID="$TENANT_ID >> ~/storperf_admin-rc
  echo "OS_USER_DOMAIN_ID="$USER_DOMAIN_ID >> ~/storperf_admin-rc


The generated "storperf_admin-rc" file will be stored in the root directory. If
you installed *Yardstick* using Docker, this file will be located in the
container. You may need to copy it to the root directory of the Storperf
deployed host.

Step 1: Plug-in configuration file preparation
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

To install a plug-in, first you need to prepare a plug-in configuration file in
YAML format and store it in the "plugin" directory. The plugin configration file
work as the input of yardstick "plugin" command. Below is the Storperf plug-in
configuration file sample:
::

  ---
  # StorPerf plugin configuration file
  # Used for integration StorPerf into Yardstick as a plugin
  schema: "yardstick:plugin:0.1"
  plugins:
    name: storperf
  deployment:
    ip: 192.168.23.2
    user: root
    password: root

In the plug-in configuration file, you need to specify the plug-in name and the
plug-in deployment info, including node ip, node login username and password.
Here the Storperf will be installed on IP 192.168.23.2 which is the Jump Host
in my local environment.

Step 2: Plug-in install/remove scripts preparation
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

In "yardstick/resource/scripts" directory, there are two folders: a "install"
folder and a "remove" folder. You need to store the plug-in install/remove
scripts in these two folders respectively.

The detailed installation or remove operation should de defined in these two
scripts. The name of both install and remove scripts should match the plugin-in
name that you specified in the plug-in configuration file.

For example, the install and remove scripts for Storperf are both named to
"storperf.bash".

Step 3: Install and remove Storperf
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

To install Storperf, simply execute the following command::

  # Install Storperf
  yardstick plugin install plugin/storperf.yaml

removing Storperf from yardstick
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To remove Storperf, simply execute the following command::

  # Remove Storperf
  yardstick plugin remove plugin/storperf.yaml

What yardstick plugin command does is using the username and password to log
into the deployment target and then execute the corresponding install or remove
script.
