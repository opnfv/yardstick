..
      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

      Convention for heading levels in Yardstick documentation:

      =======  Heading 0 (reserved for the title in a document)
      -------  Heading 1
      ~~~~~~~  Heading 2
      +++++++  Heading 3
      '''''''  Heading 4

      Avoid deeper levels because they do not render well.

Introduction
------------

Yardstick is a project dealing with performance testing. Yardstick produces
its own test cases but can also be considered as a framework to support feature
project testing.

Yardstick developed a test API that can be used by any OPNFV project. Therefore
there are many ways to contribute to Yardstick.

You can:

* Develop new test cases
* Review codes
* Develop Yardstick API / framework
* Develop Yardstick grafana dashboards and Yardstick reporting page
* Write Yardstick documentation

This developer guide describes how to interact with the Yardstick project.
The first section details the main working areas of the project. The Second
part is a list of “How to” to help you to join the Yardstick family whatever
your field of interest is.

Where can I find some help to start?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _`user guide`: http://artifacts.opnfv.org/yardstick/danube/1.0/docs/stesting_user_userguide/index.html
.. _`wiki page`: https://wiki.opnfv.org/display/yardstick/

This guide is made for you. You can have a look at the `user guide`_.
There are also references on documentation, video tutorials, tips in the
project `wiki page`_. You can also directly contact us by mail with [Yardstick]
prefix in the subject at opnfv-tech-discuss@lists.opnfv.org or on the IRC chan
#opnfv-yardstick.


Yardstick developer areas
-------------------------

Yardstick framework
~~~~~~~~~~~~~~~~~~~

Yardstick can be considered as a framework. Yardstick is released as a docker
file, including tools, scripts and a CLI to prepare the environement and run
tests. It simplifies the integration of external test suites in CI pipelines
and provides commodity tools to collect and display results.

Since Danube, test categories (also known as tiers) have been created to group
similar tests, provide consistant sub-lists and at the end optimize test
duration for CI (see How To section).

The definition of the tiers has been agreed by the testing working group.

The tiers are:

* smoke
* features
* components
* performance
* vnf


How Todos?
----------

How Yardstick works?
~~~~~~~~~~~~~~~~~~~~

The installation and configuration of the Yardstick is described in the `user guide`_.

How to work with test cases?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sample Test cases
+++++++++++++++++

Yardstick provides many sample test cases which are located at ``samples`` directory of repo.

Sample test cases are designed with the following goals:

1. Helping user better understand Yardstick features (including new feature and
   new test capacity).

2. Helping developer to debug a new feature and test case before it is
   offically released.

3. Helping other developers understand and verify the new patch before the
   patch is merged.

Developers should upload their sample test cases as well when they are
uploading a new patch which is about the Yardstick new test case or new feature.


OPNFV Release Test cases
++++++++++++++++++++++++

OPNFV Release test cases are located at ``yardstick/tests/opnfv/test_cases``.
These test cases are run by OPNFV CI jobs, which means these test cases should
be more mature than sample test cases.
OPNFV scenario owners can select related test cases and add them into the test
suites which represent their scenario.


Test case Description File
++++++++++++++++++++++++++

This section will introduce the meaning of the Test case description file.
we will use ping.yaml as a example to show you how to understand the test case
description file.
This ``yaml`` file consists of two sections. One is ``scenarios``,  the other
is ``context``.::

  ---
    # Sample benchmark task config file
    # measure network latency using ping

    schema: "yardstick:task:0.1"

    {% set provider = provider or none %}
    {% set physical_network = physical_network or 'physnet1' %}
    {% set segmentation_id = segmentation_id or none %}
    scenarios:
    -
      type: Ping
      options:
        packetsize: 200
      host: athena.demo
      target: ares.demo

      runner:
        type: Duration
        duration: 60
        interval: 1

      sla:
        max_rtt: 10
        action: monitor

    context:
      name: demo
      image: yardstick-image
      flavor: yardstick-flavor
      user: ubuntu

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
          physical_network: {{physical_network}}
            {% if segmentation_id %}
          segmentation_id: {{segmentation_id}}
            {% endif %}
         {% endif %}


The ``contexts`` section is the description of pre-condition of testing. As
``ping.yaml`` shows, you can configure the image, flavor, name, affinity and
network of Test VM (servers),  with this section, you will get a pre-condition
env for Testing.
Yardstick will automatically setup the stack which are described in this
section.
Yardstick converts this section to heat template and sets up the VMs with
heat-client (Yardstick can also support to convert this section to Kubernetes
template to setup containers).

In the examples above, two Test VMs (athena and ares) are configured by
keyword ``servers``.
``flavor`` will determine how many vCPU, how much memory for test VMs.
As ``yardstick-flavor`` is a basic flavor which will be automatically created
when you run command ``yardstick env prepare``. ``yardstick-flavor`` is
``1 vCPU 1G RAM,3G Disk``.
``image`` is the image name of test VMs. If you use ``cirros.3.5.0``, you need
fill the username of this image into ``user``.
The ``policy`` of placement of Test VMs have two values (``affinity`` and
``availability``). ``availability`` means anti-affinity.
In the ``network`` section, you can configure which ``provider`` network and
``physical_network`` you want Test VMs to use.
You may need to configure ``segmentation_id`` when your network is vlan.

Moreover, you can configure your specific flavor as below, Yardstick will setup
the stack for you. ::

  flavor:
    name: yardstick-new-flavor
    vcpus: 12
    ram: 1024
    disk: 2


Besides default ``Heat`` context, Yardstick also allows you to setup two other
types of context. They are ``Node`` and ``Kubernetes``. ::

  context:
    type: Kubernetes
    name: k8s

and ::

  context:
    type: Node
    name: LF


The ``scenarios`` section is the description of testing steps, you can
orchestrate the complex testing step through scenarios.

Each scenario will do one testing step.
In one scenario, you can configure the type of scenario (operation), ``runner``
type and ``sla`` of the scenario.

For TC002, We only have one step, which is Ping from host VM to target VM. In
this step, we also have some detailed operations implemented (such as ssh to
VM, ping from VM1 to VM2. Get the latency, verify the SLA, report the result).

If you want to get this implementation details implement, you can check with
the scenario.py file. For Ping scenario, you can find it in Yardstick repo
(``yardstick/yardstick/benchmark/scenarios/networking/ping.py``).

After you select the type of scenario (such as Ping), you will select one type
of ``runner``, there are 4 types of runner. ``Iteration`` and ``Duration`` are
the most commonly used, and the default is ``Iteration``.

For ``Iteration``, you can specify the iteration number and interval of iteration. ::

  runner:
    type: Iteration
    iterations: 10
    interval: 1

That means Yardstick will repeat the Ping test 10 times and the interval of
each iteration is one second.

For ``Duration``, you can specify the duration of this scenario and the
interval of each ping test. ::

  runner:
    type: Duration
    duration: 60
    interval: 10

That means Yardstick will run the ping test as loop until the total time of
this scenario reaches 60s and the interval of each loop is ten seconds.


SLA is the criterion of this scenario. This depends on the scenario. Different
scenarios can have different SLA metric.


How to write a new test case
++++++++++++++++++++++++++++

Yardstick already provides a library of testing steps (i.e. different types of
scenario).

Basically, what you need to do is to orchestrate the scenario from the library.

Here, we will show two cases. One is how to write a simple test case, the other
is how to write a quite complex test case.

Write a new simple test case
''''''''''''''''''''''''''''

First, you can image a basic test case description as below.

+-----------------------------------------------------------------------------+
|Storage Performance                                                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|metric        | IOPS (Average IOs performed per second),                     |
|              | Throughput (Average disk read/write bandwidth rate),         |
|              | Latency (Average disk read/write latency)                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC005 is to evaluate the IaaS storage         |
|              | performance with regards to IOPS, throughput and latency.    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | fio test is invoked in a host VM on a compute blade, a job   |
|description   | file as well as parameters are passed to fio and fio will    |
|              | start doing what the job file tells it to do.                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc005.yaml                             |
|              |                                                              |
|              | IO types is set to read, write, randwrite, randread, rw.     |
|              | IO block size is set to 4KB, 64KB, 1024KB.                   |
|              | fio is run for each IO type and IO block size scheme,        |
|              | each iteration runs for 30 seconds (10 for ramp time, 20 for |
|              | runtime).                                                    |
|              |                                                              |
|              | For SLA, minimum read/write iops is set to 100,              |
|              | minimum read/write throughput is set to 400 KB/s,            |
|              | and maximum read/write latency is set to 20000 usec.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | This test case can be configured with different:             |
|              |                                                              |
|              |   * IO types;                                                |
|              |   * IO block size;                                           |
|              |   * IO depth;                                                |
|              |   * ramp time;                                               |
|              |   * test duration.                                           |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
|              | SLA is optional. The SLA in this test case serves as an      |
|              | example. Considerably higher throughput and lower latency    |
|              | are expected. However, to cover most configurations, both    |
|              | baremetal and fully virtualized  ones, this value should be  |
|              | possible to achieve and acceptable for black box testing.    |
|              | Many heavy IO applications start to suffer badly if the      |
|              | read/write bandwidths are lower than this.                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with fio included in it.                                     |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | A host VM with fio installed is booted.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the host VM by using ssh.        |
|              | 'fio_benchmark' bash script is copyied from Jump Host to     |
|              | the host VM via the ssh tunnel.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | 'fio_benchmark' script is invoked. Simulated IO operations   |
|              | are started. IOPS, disk read/write bandwidth and latency are |
|              | recorded and checked against the SLA. Logs are produced and  |
|              | stored.                                                      |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | The host VM is deleted.                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+

TODO

How can I contribute to Yardstick?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are already a contributor of any OPNFV project, you can contribute to
Yardstick. If you are totally new to OPNFV, you must first create your Linux
Foundation account, then contact us in order to declare you in the repository
database.

We distinguish 2 levels of contributors:

* the standard contributor can push patch and vote +1/0/-1 on any Yardstick patch
* The commitor can vote -2/-1/0/+1/+2 and merge

Yardstick commitors are promoted by the Yardstick contributors.

Gerrit & JIRA introduction
++++++++++++++++++++++++++

.. _Gerrit: https://www.gerritcodereview.com/
.. _`OPNFV Gerrit`: http://gerrit.opnfv.org/
.. _link: https://identity.linuxfoundation.org/
.. _JIRA: https://jira.opnfv.org/secure/Dashboard.jspa

OPNFV uses Gerrit_ for web based code review and repository management for the
Git Version Control System. You can access `OPNFV Gerrit`_. Please note that
you need to have Linux Foundation ID in order to use OPNFV Gerrit. You can get
one from this link_.

OPNFV uses JIRA_ for issue management. An important principle of change
management is to have two-way trace-ability between issue management
(i.e. JIRA_) and the code repository (via Gerrit_). In this way, individual
commits can be traced to JIRA issues and we also know which commits were used
to resolve a JIRA issue.

If you want to contribute to Yardstick, you can pick a issue from Yardstick's
JIRA dashboard or you can create you own issue and submit it to JIRA.

Install Git and Git-reviews
+++++++++++++++++++++++++++

Installing and configuring Git and Git-Review is necessary in order to submit
code to Gerrit. The
`Getting to the code <https://wiki.opnfv.org/display/DEV/Developer+Getting+Started>`_
page will provide you with some help for that.


Verify your patch locally before submitting
+++++++++++++++++++++++++++++++++++++++++++

Once you finish a patch, you can submit it to Gerrit for code review. A
developer sends a new patch to Gerrit will trigger patch verify job on Jenkins
CI. The yardstick patch verify job includes python pylint check, unit test and
code coverage test. Before you submit your patch, it is recommended to run the
patch verification in your local environment first.

Open a terminal window and set the project's directory to the working
directory using the ``cd`` command. Assume that ``YARDSTICK_REPO_DIR`` is the
path to the Yardstick project folder on your computer::

  cd $YARDSTICK_REPO_DIR

Verify your patch::

  tox

It is used in CI but also by the CLI.

For more details on ``tox`` and tests, please refer to the `Running tests`_
and `working with tox`_ sections below, which describe the different available
environments.

Submit the code with Git
++++++++++++++++++++++++

Tell Git which files you would like to take into account for the next commit.
This is called 'staging' the files, by placing them into the staging area,
using the ``git add`` command (or the synonym ``git stage`` command)::

  git add $YARDSTICK_REPO_DIR/samples/sample.yaml

Alternatively, you can choose to stage all files that have been modified (that
is the files you have worked on) since the last time you generated a commit,
by using the `-a` argument::

  git add -a

Git won't let you push (upload) any code to Gerrit if you haven't pulled the
latest changes first. So the next step is to pull (download) the latest
changes made to the project by other collaborators using the ``pull`` command::

  git pull

Now that you have the latest version of the project and you have staged the
files you wish to push, it is time to actually commit your work to your local
Git repository::

  git commit --signoff -m "Title of change"

  Test of change that describes in high level what was done. There is a lot of
  documentation in code so you do not need to repeat it here.

  JIRA: YARDSTICK-XXX

.. _`this document`: http://chris.beams.io/posts/git-commit/

The message that is required for the commit should follow a specific set of
rules. This practice allows to standardize the description messages attached
to the commits, and eventually navigate among the latter more easily.

`This document`_ happened to be very clear and useful to get started with that.

Push the code to Gerrit for review
++++++++++++++++++++++++++++++++++

Now that the code has been comitted into your local Git repository the
following step is to push it online to Gerrit for it to be reviewed. The
command we will use is ``git review``::

  git review

This will automatically push your local commit into Gerrit. You can add
Yardstick committers and contributors to review your codes.

.. image:: images/review.PNG
   :width: 800px
   :alt: Gerrit for code review

You can find a list Yardstick people
`here <https://wiki.opnfv.org/display/yardstick/People>`_, or use the
``yardstick-reviewers`` and ``yardstick-committers`` groups in gerrit.

Modify the code under review in Gerrit
++++++++++++++++++++++++++++++++++++++

At the same time the code is being reviewed in Gerrit, you may need to edit it
to make some changes and then send it back for review. The following steps go
through the procedure.

Once you have modified/edited your code files under your IDE, you will have to
stage them. The ``git status`` command is very helpful at this point as it
provides an overview of Git's current state::

  git status

This command lists the files that have been modified since the last commit.

You can now stage the files that have been modified as part of the Gerrit code
review addition/modification/improvement using ``git add`` command. It is now
time to commit the newly modified files, but the objective here is not to
create a new commit, we simply want to inject the new changes into the
previous commit. You can achieve that with the '--amend' option on the
``git commit`` command::

  git commit --amend

If the commit was successful, the ``git status`` command should not return the
updated files as about to be commited.

The final step consists in pushing the newly modified commit to Gerrit::

  git review

Backporting changes to stable branches
--------------------------------------
During the release cycle, when master and the ``stable/<release>`` branch have
diverged, it may be necessary to backport (cherry-pick) changes top the
``stable/<release>`` branch once they have merged to master.
These changes should be identified by the committers reviewing the patch.
Changes should be backported **as soon as possible** after merging of the
original code.

..note::
  Besides the commit and review process below, the Jira tick must be updated to
  add dual release versions and indicate that the change is to be backported.

The process for backporting is as follows:

* Committer A merges a change to master (process for normal changes).
* Committer A cherry-picks the change to ``stable/<release>`` branch (if the
  bug has been identified for backporting).
* The original author should review the code and verify that it still works
  (and give a ``+1``).
* Committer B reviews the change, gives a ``+2`` and merges to
  ``stable/<release>``.

A backported change needs a ``+1`` and a ``+2`` from a committer who didn’t
propose the change (i.e. minimum 3 people involved).

Development guidelines
----------------------
This section provides guidelines and best practices for feature development
and bug fixing in Yardstick.

In general, bug fixes should be submitted as a single patch.

When developing larger features, all commits on the local topic branch can be
submitted together, by running ``git review`` on the tip of the branch. This
creates a chain of related patches in gerrit.

Each commit should contain one logical change and the author should aim for no
more than 300 lines of code per commit. This helps to make the changes easier
to review.

Each feature should have the following:

* Feature/bug fix code
* Unit tests (both positive and negative)
* Functional tests (optional)
* Sample testcases (if applicable)
* Documentation
* Update to release notes

Coding style
~~~~~~~~~~~~
.. _`OpenStack Style Guidelines`: https://docs.openstack.org/hacking/latest/user/hacking.html
.. _`OPNFV coding guidelines`: https://wiki.opnfv.org/display/DEV/Contribution+Guidelines

Please follow the `OpenStack Style Guidelines`_ for code contributions (the
section on Internationalization (i18n) Strings is not applicable).

When writing commit message, the `OPNFV coding guidelines`_ on git commit
message style should also be used.

Running tests
~~~~~~~~~~~~~
Once your patch has been submitted, a number of tests will be run by Jenkins
CI to verify the patch. Before submitting your patch, you should run these
tests locally. You can do this using ``tox``, which has a number of different
test environments defined in ``tox.ini``.
Calling ``tox`` without any additional arguments runs the default set of
tests (unit tests, functional tests, coverage and pylint).

If some tests are failing, you can save time and select test environments
individually, by passing one or more of the following command-line options to
``tox``:

* ``-e py27``: Unit tests using Python 2.7
* ``-e py3``: Unit tests using Python 3
* ``-e pep8``: Linter and style checks on updated files
* ``-e functional``: Functional tests using Python 2.7
* ``-e functional-py3``: Functional tests using Python 3
* ``-e coverage``: Code coverage checks

.. note:: You need to stage your changes prior to running coverage for those
   changes to be checked.

In addition to the tests run by Jenkins (listed above), there are a number of
other test environments defined.

* ``-e pep8-full``: Linter and style checks are run on the whole repo (not
  just on updated files)
* ``-e os-requirements``: Check that the requirements are compatible with
  OpenStack requirements.

Working with tox
++++++++++++++++
.. _virtualenv: https://virtualenv.pypa.io/en/stable/

``tox`` uses `virtualenv`_ to create isolated Python environments to run the
tests in. The test environments are located at
``.tox/<environment_name>`` e.g. ``.tox/py27``.

If requirements are changed, you will need to recreate the tox test
environment to make sure the new requirements are installed. This is done by
passing the additional ``-r`` command-line option to ``tox``::

    tox -r -e ...

This can also be achieved by deleting the test environments manually before
running ``tox``::

   rm -rf .tox/<environment_name>
   rm -rf .tox/py27

Writing unit tests
~~~~~~~~~~~~~~~~~~
For each change submitted, a set of unit tests should be submitted, which
should include both positive and negative testing.

In order to help identify which tests are needed, follow the guidelines below.

* In general, there should be a separate test for each branching point, return
  value and input set.
* Negative tests should be written to make sure exceptions are raised and/or
  handled appropriately.

The following convention should be used for naming tests::

    test_<method_name>_<some_comment>

The comment gives more information on the nature of the test, the side effect
being checked, or the parameter being modified::

    test_my_method_runtime_error
    test_my_method_invalid_credentials
    test_my_method_param1_none

Mocking
+++++++
The ``mock`` library is used for unit testing to stub out external libraries.

The following conventions are used in Yardstick:

* Use ``mock.patch.object`` instead of ``mock.patch``.

* When naming mocked classes/functions, use ``mock_<class_and_function_name>``
  e.g. ``mock_subprocess_call``

* Avoid decorating classes with mocks. Apply the mocking in ``setUp()``::

    @mock.patch.object(ssh, 'SSH')
    class MyClassTestCase(unittest.TestCase):

  should be::

    class MyClassTestCase(unittest.TestCase):
        def setUp(self):
            self._mock_ssh = mock.patch.object(ssh, 'SSH')
            self.mock_ssh = self._mock_ssh.start()

            self.addCleanup(self._stop_mocks)

        def _stop_mocks(self):
            self._mock_ssh.stop()

Plugins
-------

For information about Yardstick plugins, refer to the chapter
**Installing a plug-in into Yardstick** in the `user guide`_.

