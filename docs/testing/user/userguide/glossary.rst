.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

========
Glossary
========

.. glossary::
   :sorted:

   API
     Application Programming Interface

   Barometer
     OPNFV NFVi Service Assurance project. Barometer upstreams changes to
     collectd, OpenStack, etc to improve features related to NFVi monitoring
     and service assurance.
     More info on: https://opnfv-barometer.readthedocs.io/en/latest/

   collectd
      collectd is a system statistics collection daemon.
      More info on: https://collectd.org/

   context
      A context describes the environment in which a yardstick testcase will
      be run. It can refer to a pre-provisioned environment, or an environment
      that will be set up using OpenStack or Kubernetes.

   Docker
     Docker provisions and manages containers. Yardstick and many other OPNFV
     projects are deployed in containers. Docker is required to launch the
     containerized versions of these projects.

   DPDK
     Data Plane Development Kit

   DPI
     Deep Packet Inspection

   DSCP
     Differentiated Services Code Point

   flavor
      A specification of virtual resources used by OpenStack in the creation
      of a VM instance.

   Grafana
      A visualization tool, used in Yardstick to retrieve test data from
      InfluxDB and display it. Grafana works by defining dashboards, which are
      combinations of visualization panes (e.g. line charts and gauges) and
      forms that assist the user in formulating SQL-like queries for InfluxDB.
      More info on: https://grafana.com/

   IGMP
     Internet Group Management Protocol

   InfluxDB
      One of the Dispatchers supported by Yardstick, it allows test results to
      be reported to a time-series database.
      More info on: https://www.influxdata.com/

   IOPS
     Input/Output Operations Per Second
     A performance measurement used to benchmark storage devices.

   KPI
     Key Performance Indicator

   Kubernetes
     k8s
     Kubernetes is an open-source container-orchestration system for automating
     deployment, scaling and management of containerized applications.
     It is one of the contexts supported in Yardstick.

   MPLS
      Multiprotocol Label Switching

   NFV
     Network Function Virtualization
     NFV is an initiative to take network services which were traditionally run
     on proprietary, dedicated hardware, and virtualize them to run on general
     purpose hardware.

   NFVI
     Network Function Virtualization Infrastructure
     The servers, routers, switches, etc on which the NFV system runs.

   NIC
     Network Interface Controller

   NSB
      Network Services Benchmarking. A subset of Yardstick features concerned
      with NFVI and VNF characterization.

   OpenStack
      OpenStack is a cloud operating system that controls pools of compute,
      storage, and networking resources. OpenStack is an open source project
      licensed under the Apache License 2.0.

   PBFS
     Packet Based per Flow State

   PROX
     Packet pROcessing eXecution engine

   QoS
     Quality of Service
     The ability to guarantee certain network or storage requirements to
     satisfy a Service Level Agreement (SLA) between an application provider
     and end users.
     Typically includes performance requirements like networking bandwidth,
     latency, jitter correction, and reliability as well as storage
     performance in Input/Output Operations Per Second (IOPS), throttling
     agreements, and performance expectations at peak load

   runner
     The part of a Yardstick testcase that determines how the test will be run
     (e.g. for x iterations, y seconds or until state z is reached). The runner
     also determines when the metrics are collected/reported.

   SampleVNF
     OPNFV project providing a repository of reference VNFs.
     More info on: https://opnfv-samplevnf.readthedocs.io/en/latest/

   scenario
     The part of a Yardstick testcase that describes each test step.

   SLA
     Service Level Agreement
     An SLA is an agreement between a service provider and a customer to
     provide a certain level of service/performance.

   SR-IOV
     Single Root IO Virtualization
     A specification that, when implemented by a physical PCIe
     device, enables it to appear as multiple separate PCIe devices. This
     enables multiple virtualized guests to share direct access to the
     physical device.

   SUT
     System Under Test

   testcase
      A task in Yardstick; the yaml file that is read by Yardstick to
      determine how to run a test.

   ToS
     Type of Service

   VLAN
     Virtual LAN (Local Area Network)

   VM
     Virtual Machine
     An operating system instance that runs on top of a hypervisor.
     Multiple VMs can run at the same time on the same physical
     host.

   VNF
     Virtual Network Function

   VNFC
     Virtual Network Function Component
