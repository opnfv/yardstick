========================
Yardstick User Interface
========================

This interface provides a user to view the test result
in table format and also values pinned on to a graph.


Command
=======
::

    yardstick report generate <task-ID> <testcase-filename>


Description
===========

1. When the command is triggered using the task-id and the testcase
name provided the respective values are retrieved from the
database (influxdb in this particular case).

2. The values are then formatted and then provided to the html
template framed with complete html body using Django Framework.

3. Then the whole template is written into a html file.

The graph is framed with Timestamp on x-axis and output values
(differ from testcase to testcase) on y-axis with the help of
"Highcharts".
