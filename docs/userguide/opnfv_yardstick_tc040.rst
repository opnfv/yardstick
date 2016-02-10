.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC040
*************************************

.. _Parser: https://wiki.opnfv.org/parser

+-----------------------------------------------------------------------------+
|Verify Parser Yang-to-Tosca                                                  |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC040 Verify Parser Yang-to-Tosca            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | 1. tosca file which is converted from yang file by Parser    |
|              | 2. result whether the output is same with expected outcome   |
+--------------+--------------------------------------------------------------+
|test purpose  | To verify the function of Yang-to-Tosca in Parser.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc040.yaml                             |
|              |                                                              |
|              | yangfile: the path of the yangfile which you want to convert |
|              | toscafile: the path of the toscafile which is your expected  |
|              | outcome.                                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Parser                                                       |
|              |                                                              |
|              | (Parser is not part of a Linux distribution, hence it        |
|              | needs to be installed. As an example see the                 |
|              | /yardstick/benchmark/scenarios/parser/parser_setup.sh for    |
|              | how to install it manual. Of course, it will be installed    |
|              | and uninstalled automatically when you run this test case    |
|              | by yardstick)                                                |
+--------------+--------------------------------------------------------------+
|references    | Parser_                                                      |
|              |                                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different path of yangfile and   |
|              | toscafile to fit your real environment to verify Parser      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      |  No POD specific requirements have been identified.          |
|conditions    |  it can be run without VM                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | parser is installed without VM, running Yang-to-Tosca module |
|              | to convert yang file to tosca file, validating output against|
|              | expected outcome.                                            |
|              |                                                              |
|              | Result: Logs are stored.                                     |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if output is different with expected outcome      |
|              | or if there is a test case execution problem.                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
