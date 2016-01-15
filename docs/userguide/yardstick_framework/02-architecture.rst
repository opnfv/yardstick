Architecture
============

Concepts
--------
Below is a list of common Yardstick concepts and a short description of each.

**benchmark configuration file** - Describes a single test case in YAML format.

**runner** - Logic that determines how a scenario is run, for example number
of iterations, input value stepping or test duration.

**scenario** - Type of measurement (the tool), such as Ping, Pktgen, Iperf,
LmBench, Fio.

**context** - The set of Cloud resources used by a scenario. A context is
converted into a simplified Heat template.

**SLA** - Relates to what boundary a test case must meet to pass. For
example a latency limit, lost packets and so on. Action based on SL
can be set, either just to log (monitor) or to stop further testing (assert)


Test execution flow
-------------------

Each benchmark configuration YAML-file (the test case) is parsed and converted
into a Yardstick-internal model. When the test case is invoked (i.e. when a
task is started) then first the context part of the model is converted
into a Heat template and deployed into a stack (in OpenStack). This includes
for instance VM deployment, network setup, and user authentication. Once the
context is up an running the scenario is run using a runner, either serially
or in parallel, or a combination of both.

Each runner runs in its own subprocess executing commands in a VM using SSH,
for example invoking ping from inside the VM acting as the VNF application.
The output of each command is written as JSON records to a file that is output
into either a file (/tmp/yardstick.out by default), or in the case of running
in a POD into a database instead.

When a test case is finished everything is cleaned out to prepare for the
next test case. A manually aborted test case is also cleaned out.


Directory structure
-------------------

**yardstick/** - Yardstick main directory.

*ci/* - Used for continuous integration of Yardstick at different PODs and
with support for different installers (Apex, Compass, Fuel etc.)

*docs/* - All documentation is stored here, such as configuration guides,
user guides and Yardstick descriptions.

*etc/* - Used for test cases requiring specific POD configurations.

*samples/* - Test case samples are stored here. These are only samples, and
not run during VNF verifications.

*tests/* - Here both Yardstick internal tests (*functional/* and *unit/*) as
well as the test cases run to verify the VNFs are stored (*opnfv/*).

*tools/* - Various tools to run Yardstick. Currently contains how to
create the yardstick-trusty-server image with the different tools that
are needed from within the image.

*vTC/* - Contains the files for running the virtual Traffic Classifier tests.

*yardstick/* - Contains the internals of Yardstick: Runners, CLI parsing,
authentication keys, plotting tools, database and so on.