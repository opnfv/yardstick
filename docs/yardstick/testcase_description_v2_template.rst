.. Template to be used for test case descriptions in Yardstick Project.
   Write one .rst per test case.
   Upload the .rst for the test case in /docs/source/yardstick directory.
   Review in Gerrit.

*************************************
Yardstick Test Case Description TCXXX
*************************************

+-----------------------------------------------------------------------------+
|test case slogan e.g. Network Latency                                        |
+==============+==============================================================+
|test case id  | e.g. OPNFV_YARDSTICK_TC001_NW Latency                        |
+--------------+--------------------------------------------------------------+
|metric        | what will be measured, e.g. latency                          |
+--------------+--------------------------------------------------------------+
|test purpose  | describe what is the purpose of the test case                |
+--------------+--------------------------------------------------------------+
|configuration | what .yaml file to use, state SLA if applicable, state       |
|              | test duration, list and describe the scenario options used in|
|              | this TC and also list the options using default values.      |
+--------------+--------------------------------------------------------------+
|test tool     | e.g. ping                                                    |
+--------------+--------------------------------------------------------------+
|references    | e.g. RFCxxx, ETSI-NFVyyy                                     |
+--------------+--------------------------------------------------------------+
|applicability | describe variations of the test case which can be            |
|              | performend, e.g. run the test for different packet sizes     |
+--------------+--------------------------------------------------------------+
|pre-test      | describe configuration in the tool(s) used to perform        |
|conditions    | the measurements (e.g. fio, pktgen), POD-specific            |
|              | configuration required to enable running the test            |
+--------------+------+----------------------------------+--------------------+
|test sequence | step | description                      | result             |
|              +------+----------------------------------+--------------------+
|              |  1   | use this to describe tests that  | what happens in    |
|              |      | require several steps e.g.       | this step          |
|              |      | step 1 collect logs              | e.g. logs collected|
|              +------+----------------------------------+--------------------+
|              |  2   | remove interface                 | interface down     |
|              +------+----------------------------------+--------------------+
|              |  N   | what is done in step N           | what happens       |
+--------------+------+----------------------------------+--------------------+
|test verdict  | expected behavior, or SLA, pass/fail criteria                |
+--------------+--------------------------------------------------------------+
