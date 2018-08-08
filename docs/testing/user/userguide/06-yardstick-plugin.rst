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


Step 1: Plug-in configuration file preparation
----------------------------------------------

To install a plug-in, first you need to prepare a plug-in configuration file in
YAML format and store it in the "plugin" directory. The plugin configration
file work as the input of yardstick "plugin" command. Below is the Storperf
plug-in configuration file sample:
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
--------------------------------------------------

In ``yardstick/resource/scripts`` directory, there are two folders: an
``install`` folder and a ``remove`` folder. You need to store the plug-in
install/remove scripts in these two folders respectively.

The detailed installation or remove operation should de defined in these two
scripts. The name of both install and remove scripts should match the plugin-in
name that you specified in the plug-in configuration file.

For example, the install and remove scripts for Storperf are both named
``storperf.bash``.

Step 3: Install and remove Storperf
-----------------------------------

To install Storperf, simply execute the following command::

  # Install Storperf
  yardstick plugin install plugin/storperf.yaml

Removing Storperf from yardstick
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To remove Storperf, simply execute the following command::

  # Remove Storperf
  yardstick plugin remove plugin/storperf.yaml

What Yardstick plugin command does is using the username and password to log
into the deployment target and then execute the corresponding install or remove
script.
