.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

Task Template Syntax
====================

Basic template syntax
---------------------
A nice feature of the input task format used in Yardstick is that it supports
the template syntax based on Jinja2.
This turns out to be extremely useful when, say, you have a fixed structure of
your task but you want to parameterize this task in some way.
For example, imagine your input task file (task.yaml) runs a set of Ping
scenarios:

::

  # Sample benchmark task config file
  # measure network latency using ping
  schema: "yardstick:task:0.1"

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
      ...

Let's say you want to run the same set of scenarios with the same runner/
context/sla, but you want to try another packetsize to compare the performance.
The most elegant solution is then to turn the packetsize name into a template
variable:

::

  # Sample benchmark task config file
  # measure network latency using ping

  schema: "yardstick:task:0.1"
  scenarios:
  -
    type: Ping
    options:
      packetsize: {{packetsize}}
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
      ...

and then pass the argument value for {{packetsize}} when starting a task with
this configuration file.
Yardstick provides you with different ways to do that:

1.Pass the argument values directly in the command-line interface (with either
a JSON or YAML dictionary):

::

 yardstick task start samples/ping-template.yaml
 --task-args'{"packetsize":"200"}'

2.Refer to a file that specifies the argument values (JSON/YAML):

::

 yardstick task start samples/ping-template.yaml --task-args-file args.yaml

Using the default values
------------------------
Note that the Jinja2 template syntax allows you to set the default values for
your parameters.
With default values set, your task file will work even if you don't
parameterize it explicitly while starting a task.
The default values should be set using the {% set ... %} clause (task.yaml).
For example:

::

  # Sample benchmark task config file
  # measure network latency using ping
  schema: "yardstick:task:0.1"
  {% set packetsize = packetsize or "100" %}
  scenarios:
  -
    type: Ping
    options:
    packetsize: {{packetsize}}
    host: athena.demo
    target: ares.demo

    runner:
      type: Duration
      duration: 60
      interval: 1
    ...

If you don't pass the value for {{packetsize}} while starting a task, the
default one will be used.

Advanced templates
------------------

Yardstick makes it possible to use all the power of Jinja2 template syntax,
including the mechanism of built-in functions.
As an example, let us make up a task file that will do a block storage
performance test.
The input task file (fio-template.yaml) below uses the Jinja2 for-endfor
construct to accomplish that:

::

  #Test block sizes of 4KB, 8KB, 64KB, 1MB
  #Test 5 workloads: read, write, randwrite, randread, rw
  schema: "yardstick:task:0.1"

   scenarios:
  {% for bs in ['4k', '8k', '64k', '1024k' ] %}
    {% for rw in ['read', 'write', 'randwrite', 'randread', 'rw' ] %}
  -
    type: Fio
    options:
      filename: /home/ubuntu/data.raw
      bs: {{bs}}
      rw: {{rw}}
      ramp_time: 10
    host: fio.demo
    runner:
      type: Duration
      duration: 60
      interval: 60

    {% endfor %}
  {% endfor %}
  context
      ...
