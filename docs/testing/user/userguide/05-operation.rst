.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Intel, Ericsson AB, Huawei Technologies Co. Ltd and others.

..
      Convention for heading levels in Yardstick:
      =======  Heading 0 (reserved for the title in a document)
      -------  Heading 1
      ^^^^^^^  Heading 2
      +++++++  Heading 3
      '''''''  Heading 4
      Avoid deeper levels because they do not render well.

===============
Yardstick Usage
===============

Once you have yardstick installed, you can start using it to run testcases
immediately, through the CLI. You can also define and run new testcases and
test suites. This chapter details basic usage (running testcases), as well as
more advanced usage (creating your own testcases).

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
test case:

.. literalinclude::
   ../../../../tests/opnfv/test_cases/opnfv_yardstick_tc002.yaml
   :lines: 9-

Run a Yardstick test case
^^^^^^^^^^^^^^^^^^^^^^^^^

If you want run a test case, then you need to use ``yardstick task start
<test_case_path>`` this command support some parameters as below:

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

We also have a guide about `How to run Yardstick in a local environment`_.
This work is contributed by Tapio Tallgren.

Create a new testcase for Yardstick
-----------------------------------

As a user, you may want to define a new testcase in addition to the ones
already available in Yardstick. This section will show you how to do this.

Each testcase consists of two sections:

* ``scenarios`` describes what will be done by the test
* ``context`` describes the environment in which the test will be run.

Defining the testcase scenarios
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO

Defining the testcase context(s)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each testcase consists of one or more contexts, which describe the environment
in which the testcase will be run.
Current available contexts are:

* ``Dummy``: this is a no-op context, and is used when there is no environment
  to set up e.g. when testing whether OpenStack services are available
* ``Node``: this context is used to perform operations on baremetal servers
* ``Heat``: uses OpenStack to provision the required hosts, networks, etc.
* ``Kubernetes``: uses Kubernetes to provision the resources required for the
  test.

Regardless of the context type, the ``context`` section of the testcase will
consist of the following::

   context:
     name: demo
     type: Dummy|Node|Heat|Kubernetes

The content of the ``context`` section will vary based on the context type.

Dummy Context
+++++++++++++

No additional information is required for the Dummy context::

  context:
    name: my_context
    type: Dummy

Node Context
++++++++++++

TODO

Heat Context
++++++++++++

In addition to ``name`` and ``type``, a Heat context requires the following
arguments:

* ``image``: the image to be used to boot VMs
* ``flavor``: the flavor to be used for VMs in the context
* ``user``: the username for connecting into the VMs
* ``networks``: The networks to be created, networks are identified by name

  * ``name``: network name (required)
  * (TODO) Any optional attributes

* ``servers``: The servers to be created

  * ``name``: server name
  * (TODO) Any optional attributes

In addition to the required arguments, the following optional arguments can be
passed to the Heat context:

* ``placement_groups``:

  * ``name``: the name of the placement group to be created
  * ``policy``: either ``affinity`` or ``availability``
* ``server_groups``:

  * ``name``: the name of the server group
  * ``policy``: either ``affinity`` or ``anti-affinity``

Combining these elements together, a sample Heat context config looks like:

.. literalinclude::
   ../../../../yardstick/tests/integration/dummy-scenario-heat-context.yaml
   :start-after: ---
   :empahsise-lines: 14-

Using exisiting HOT Templates
'''''''''''''''''''''''''''''

TODO

Kubernetes Context
++++++++++++++++++

TODO

Using multiple contexts in a testcase
+++++++++++++++++++++++++++++++++++++

When using multiple contexts in a testcase, the ``context`` section is replaced
by a ``contexts`` section, and each context is separated with a ``-`` line::

  contexts:
  -
    name: context1
    type: Heat
    ...
  -
    name: context2
    type: Node
    ...


Reusing a context
+++++++++++++++++

Typically, a context is torn down after a testcase is run, however, the user
may wish to keep an context intact after a testcase is complete.

.. note::
  This feature has been implemented for the Heat context only

To keep or reuse a context, the ``flags`` option must be specified:

* ``no_setup``: skip the deploy stage, and fetch the details of a deployed
   context/Heat stack.
* ``no_teardown``: skip the undeploy stage, thus keeping the stack intact for
   the next test

If either of these ``flags`` are ``True``, the context information must still
be given. By default, these flags are disabled::

  context:
    name: mycontext
    type: Heat
    flags:
      no_setup: True
      no_teardown: True
    ...

Create a test suite for Yardstick
---------------------------------

A test suite in Yardstick is a .yaml file which includes one or more test
cases. Yardstick is able to support running test suite task, so you can
customize your own test suite and run it in one task.

``tests/opnfv/test_suites`` is the folder where Yardstick puts CI test suite.
A typical test suite is like below (the ``fuel_test_suite.yaml`` example):

.. literalinclude::
   ../../../../tests/opnfv/test_suites/fuel_test_suite.yaml
   :lines: 9-

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

References
----------

.. _`How to run Yardstick in a local environment`: https://wiki.opnfv.org/display/yardstick/How+to+run+Yardstick+in+a+local+environment
