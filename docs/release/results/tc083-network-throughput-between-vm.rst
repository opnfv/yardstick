.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


=====================================================
Test results for TC083 network throughput between VMs
=====================================================

.. toctree::
   :maxdepth: 2


Overview of test case
=====================

TC083 measures network latency and throughput between VMs using netperf.
The test results shown below are for UDP throughout.

Metric: UDP stream throughput
Unit: 10^6bits/s


Euphrates release
-----------------

Test results per scenario and pod (higher is better):

{

    "os-nosdn-nofeature-ha:lf-pod1:apex": [2204.42],

    "os-nosdn-nofeature-ha:intel-pod18:joid": [1835.55],

    "os-nosdn-nofeature-ha:lf-pod2:fuel": [1676.705],

    "os-nosdn-nofeature-ha:intel-pod5:joid": [1612.555],

    "os-nosdn-nofeature-ha:flex-pod2:apex": [1370.23],

    "os-nosdn-nofeature-ha:huawei-pod12:joid": [1300.12],

    "os-nosdn-nofeature-ha:huawei-pod2:compass": [1070.455],

    "os-nosdn-nofeature-ha:ericsson-pod1:fuel": [1004.32],

    "os-nosdn-nofeature-ha:huawei-virtual9:compass": [753.46],

    "os-nosdn-nofeature-ha:huawei-virtual4:compass": [735.07],

    "os-odl-nofeature-ha:arm-pod5:fuel": [531.63],

    "os-nosdn-nofeature-ha:huawei-virtual3:compass": [493.985],

    "os-nosdn-nofeature-ha:arm-pod5:fuel": [448.82],

    "os-nosdn-nofeature-ha:arm-pod6:fuel": [193.43],

    "os-nosdn-nofeature-ha:huawei-virtual1:compass": [189.99],

    "os-nosdn-nofeature-ha:huawei-virtual2:compass": [80.15]

}


The influence of the scenario
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: images/tc083_scenario.png
   :width: 800px
   :alt: TC083 influence of scenario

the influence of the scenario

{

    "os-nosdn-nofeature-ha": [1109.12],

    "os-odl-nofeature-ha": [531.63]

}


The influence of the POD
^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: images/tc083_pod.png
   :width: 800px
   :alt: TC083 influence of the POD

the influence of the POD

{

    "lf-pod1": [2204.42],

    "intel-pod18": [1835.55],

    "lf-pod2": [1676.705],

    "intel-pod5": [1612.555],

    "flex-pod2": [1370.23],

    "huawei-pod12": [1300.12],

    "huawei-pod2": [1070.455],

    "ericsson-pod1": [1004.32],

    "huawei-virtual9": [753.46],

    "huawei-virtual4": [735.07],

    "huawei-virtual3": [493.985],

    "arm-pod5": [451.38],

    "arm-pod6": [193.43],

    "huawei-virtual1": [189.99],

    "huawei-virtual2": [80.15]

}


Fraser release
--------------
