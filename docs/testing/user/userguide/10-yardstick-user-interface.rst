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

1. When the command is triggered, the relevant values for the
   provided task-id and testcase name are retrieved from the
   database (`InfluxDB`_ in this particular case).

2. The values are then formatted and provided to the html
   template to be rendered using `Jinja2`_.

3. Then the rendered template is written into a html file.

The graph is framed with Timestamp on x-axis and output values
(differ from testcase to testcase) on y-axis with the help of
`Highcharts`_.

.. _InfluxDB: https://www.influxdata.com/time-series-platform/influxdb/
.. _Jinja2: http://jinja.pocoo.org/docs/2.10/
.. _Highcharts: https://www.highcharts.com/products/highcharts/
