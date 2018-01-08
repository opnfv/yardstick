Introduction
=============

Yardstick is a project dealing with performance testing. Yardstick produces its own test cases but can also be considered as a framework to support feature project testing.

Yardstick developed a test API that can be used by any OPNFV project. Therefore there are many ways to contribute to Yardstick.

You can:

* Develop new test cases
* Review codes
* Develop Yardstick API / framework
* Develop Yardstick grafana dashboards and  Yardstick reporting page
* Write Yardstick documentation

This developer guide describes how to interact with the Yardstick project.
The first section details the main working areas of the project. The Second
part is a list of “How to” to help you to join the Yardstick family whatever
your field of interest is.

Where can I find some help to start?
--------------------------------------

.. _`user guide`: http://artifacts.opnfv.org/yardstick/danube/1.0/docs/stesting_user_userguide/index.html
.. _`wiki page`: https://wiki.opnfv.org/display/yardstick/

This guide is made for you. You can have a look at the `user guide`_.
There are also references on documentation, video tutorials, tips in the
project `wiki page`_. You can also directly contact us by mail with [Yardstick] prefix in the title at opnfv-tech-discuss@lists.opnfv.org or on the IRC chan #opnfv-yardstick.


Yardstick developer areas
==========================

Yardstick framework
--------------------

Yardstick can be considered as a framework. Yardstick is release as a docker
file, including tools, scripts and a CLI to prepare the environement and run
tests. It simplifies the integration of external test suites in CI pipeline
and provide commodity tools to collect and display results.

Since Danube, test categories also known as tiers have been created to group
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
===========

How Yardstick works?
---------------------

The installation and configuration of the Yardstick is described in the `user guide`_.

How to work with test cases?
----------------------------


**Sample Test cases**

Yardstick provides many sample test cases which are located at "samples" directory of repo.

Sample test cases are designed as following goals:

1. Helping user better understand yardstick features(including new feature and new test capacity).

2. Helping developer to debug his new feature and test case before it is offical released.

3. Helping other developers understand and verify the new patch before the patch merged.

So developers should upload your sample test case as well when they are trying to upload a new patch which is about the yardstick new test case or new feature.


**OPNFV Release Test cases**

OPNFV Release test cases which are located at "tests/opnfv/test_cases" of repo.
those test cases are runing by OPNFV CI jobs, It means those test cases should be more mature than sample test cases.
OPNFV scenario owners can select related test cases and add them into the test suites which is represent the scenario.


**Test case Description File**

This section will introduce the meaning of the Test case description file.
we will use ping.yaml as a example to show you how to understand the test case description file.
In this Yaml file, you can easily find it consists of two sections. One is “Scenarios”,  the other is “Context”.::

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


"Contexts" section is the description of pre-condition of testing. As ping.yaml shown, you can configure the image, flavor , name ,affinity and network of Test VM(servers),  with this section, you will get a pre-condition env for Testing.
Yardstick will automatic setup the stack which are described in this section.
In fact, yardstick use convert this section to heat template and setup the VMs by heat-client (Meanwhile, yardstick can support to convert this section to Kubernetes template to setup containers).

Two Test VMs(athena and ares) are configured by keyword "servers".
"flavor" will determine how many vCPU, how much memory for test VMs.
As "yardstick-flavor" is a basic flavor which will be automatically created when you run command "yardstick env prepare". "yardstick-flavor" is "1 vCPU 1G RAM,3G Disk".
"image" is the image name of test VMs. if you use cirros.3.5.0, you need fill the username of this image into "user". the "policy" of placement of Test VMs have two values (affinity and availability).
"availability" means anti-affinity. In "network" section, you can configure which provide network and physical_network you want Test VMs use.
you may need to configure segmentation_id when your network is vlan.

Moreover, you can configure your specific flavor as below, yardstick will setup the stack for you. ::

  flavor:
    name: yardstick-new-flavor
    vcpus: 12
    ram: 1024
    disk: 2


Besides default heat stack, yardstick also allow you to setup other two types stack. they are "Node" and "Kubernetes". ::

  context:
    type: Kubernetes
    name: k8s

and ::

  context:
    type: Node
    name: LF



"Scenarios" section is the description of testing step, you can orchestrate the complex testing step through orchestrate scenarios.

Each scenario will do one testing step, In one scenario, you can configure the type of scenario(operation), runner type and SLA of the scenario.

For TC002, We only have one step , that is Ping from host VM to target VM. In this step, we also have some detail operation implement ( such as ssh to VM, ping from VM1 to VM2. Get the latency, verify the SLA, report the result).

If you want to get this detail implement , you can check with the scenario.py file. For Ping scenario, you can find it in yardstick repo ( yardstick / yardstick / benchmark / scenarios / networking / ping.py)

after you select the type of scenario( such as Ping), you will select one type of runner, there are 4 types of runner. Usually, we use the "Iteration" and "Duration". and Default is "Iteration".
For Iteration, you can specify the iteration number and interval of iteration. ::

  runner:
    type: Iteration
    iterations: 10
    interval: 1

That means yardstick will iterate the 10 times of Ping test and the interval of each iteration is one second.

For Duration, you can specify the duration of this scenario and the interval of each ping test. ::

  runner:
    type: Duration
    duration: 60
    interval: 10

That means yardstick will run the ping test as loop until the total time of this scenario reach the 60s and the interval of each loop is ten seconds.


SLA is the criterion of this scenario. that depends on the scenario. different scenario can have different SLA metric.


**How to write a new test case**

Yardstick already provide a library of testing step. that means yardstick provide lots of type scenario.

Basiclly, What you need to do is to orchestrate the scenario from the library.

Here, We will show two cases. One is how to write a simple test case, the other is how to write a quite complex test case.


Write a new simple test case

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
-----------------------------------

If you are already a contributor of any OPNFV project, you can contribute to
Yardstick. If you are totally new to OPNFV, you must first create your Linux
Foundation account, then contact us in order to declare you in the repository
database.

We distinguish 2 levels of contributors:

* the standard contributor can push patch and vote +1/0/-1 on any Yardstick patch
* The commitor can vote -2/-1/0/+1/+2 and merge

Yardstick commitors are promoted by the Yardstick contributors.

Gerrit & JIRA introduction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _Gerrit: https://www.gerritcodereview.com/
.. _`OPNFV Gerrit`: http://gerrit.opnfv.org/
.. _link: https://identity.linuxfoundation.org/
.. _JIRA: https://jira.opnfv.org/secure/Dashboard.jspa

OPNFV uses Gerrit_ for web based code review and repository management for the
Git Version Control System. You can access `OPNFV Gerrit`_. Please note that
you need to have Linux Foundation ID in order to use OPNFV Gerrit. You can get one from this link_.

OPNFV uses JIRA_ for issue management. An important principle of change
management is to have two-way trace-ability between issue management
(i.e. JIRA_) and the code repository (via Gerrit_). In this way, individual
commits can be traced to JIRA issues and we also know which commits were used
to resolve a JIRA issue.

If you want to contribute to Yardstick, you can pick a issue from Yardstick's
JIRA dashboard or you can create you own issue and submit it to JIRA.

Install Git and Git-reviews
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installing and configuring Git and Git-Review is necessary in order to submit
code to Gerrit. The `Getting to the code <https://wiki.opnfv.org/display/DEV/Developer+Getting+Started>`_ page will provide you with some help for that.


Verify your patch locally before submitting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once you finish a patch, you can submit it to Gerrit for code review. A
developer sends a new patch to Gerrit will trigger patch verify job on Jenkins
CI. The yardstick patch verify job includes python pylint check, unit test and
code coverage test. Before you submit your patch, it is recommended to run the
patch verification in your local environment first.

Open a terminal window and set the project's directory to the working
directory using the ``cd`` command. Assume that ``YARDSTICK_REPO_DIR`` is the path to the Yardstick project folder on your computer::

  cd $YARDSTICK_REPO_DIR

Verify your patch::

  tox

It is used in CI but also by the CLI.

Submit the code with Git
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that the code has been comitted into your local Git repository the
following step is to push it online to Gerrit for it to be reviewed. The
command we will use is ``git review``::

  git review

This will automatically push your local commit into Gerrit. You can add
Yardstick committers and contributors to review your codes.

.. image:: images/review.PNG
   :width: 800px
   :alt: Gerrit for code review

You can find Yardstick people info `here <https://wiki.opnfv.org/display/yardstick/People>`_.

Modify the code under review in Gerrit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

At the same time the code is being reviewed in Gerrit, you may need to edit it
to make some changes and then send it back for review. The following steps go
through the procedure.

Once you have modified/edited your code files under your IDE, you will have to
stage them. The 'status' command is very helpful at this point as it provides
an overview of Git's current state::

  git status

The output of the command provides us with the files that have been modified
after the latest commit.

You can now stage the files that have been modified as part of the Gerrit code
review edition/modification/improvement using ``git add`` command. It is now
time to commit the newly modified files, but the objective here is not to
create a new commit, we simply want to inject the new changes into the
previous commit. You can achieve that with the '--amend' option on the
``git commit`` command::

  git commit --amend

If the commit was successful, the ``git status`` command should not return the
updated files as about to be commited.

The final step consists in pushing the newly modified commit to Gerrit::

  git review


Plugins
==========

For information about Yardstick plugins, refer to the chapter **Installing a plug-in into Yardstick** in the `user guide`_.

