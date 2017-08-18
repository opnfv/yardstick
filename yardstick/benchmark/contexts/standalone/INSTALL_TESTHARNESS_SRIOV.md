---------------------------------------------------------------------------
           ISB Test Harness - SR-IOV Installation Guide.
---------------------------------------------------------------------------

I. Installation, Compile and Execution
-----------------------------------------------------------------
After downloading (or doing a git clone) in a directory (isb_repo)
isb_repo $ ./scripts/install.sh --> select [2] to install Test harness

It will automatically download all the packages needed for test harness setup.

II. System Topology (SR-IOV): PHY-VM-PHY
+---------------------------------------

                         +----------------------+
                         -                      -
                         -         VM           -
              +-(0) ---->-  ->(VNF running)<-   -<----(1)--+
              -          -                      -          -
              -          +----------------------+          -
              -           - VF NIC -  - VF NIC -           -
              -           +--------+  +--------+           -
              -               -            -               -
              -               -            -               -
              -           +--------+  +--------+           -
              -           - PF NIC -  - PF NIC -           -
+-------+     -        +------------------------+          -      +------------+
-       -(0) --        -                        -          - (0)->-            -
- TG1   -(1) --        -           HOST         -                 -  L4Replay/ -
-       -     -        -                        -                 -  Verifier  -
-       -(2) <-        -                        -                 -            -
+-------+              +------------------------+                 +------------+
trafficgen_1                        vnf                             trafficgen_2

III. Setup SR-IOV Environment on Host:
-------------------------------------
BIOS Configuration:
--------------------
Parameter                               Enable/Disable
----------                              ---------------
CPU Power and Performance Policy        Performance
P-State                                 Disable
C- State                                Disable

Intel® Hyper-Threading Technology       Enable
Intel® VT                               Enable

Intel® Virtualization Technology
for Directed I/O (VT-d)                 Enable
Coherency                               Enable

OS Requirements:
------------------
This release is tested and supported for the following components for running the VNFs.
        1. DPDK - 16.04
                http://fast.dpdk.org/rel/dpdk-16.04.tar.xz

        2. VNFs on Standalone Hypervisor
             -  HOST OS: Ubuntu 16.04 LTS
             -  Hypervisor - KVM
             -  VM OS - Ubuntu 16.04

SR-IOV (Single Root IO virtulaization) Manual setup:
---------------------------------------------------
        1. Make sure the host has boot line configuration for 1 GB hugepage memory,
           CPU isolation, and the Intel IOMMU is on and running in PT mode.
           - default_hugepagesz=1GB hugepagesz=1GB hugepages=12
             hugepagesz=2M hugepages=2048 isolcpus=1,2,3,4,5,6,7,28,29,30,31,32,33,34
             iommu=pt intel_iommu=on
             CPU isolation --> CPUs of Numa Node 0 or 1 based on NIC location.
        2. Black list the IXGBE/i40e VF device driver
           - cat /etc/modprobe.d/blacklist.conf . . .
             --> blacklist ixgbevf
             --> blacklist i40evf
        3. Uninstall and reinstall the NIC device driver to enable SR-IOV
           - $ modprobe -r ixgbe or modprobe -r i40e
           - $ modprobe ixgbe max_vfs=1 or modprobe i40e max_vfs=1
           - $ service network restart
        Note: 
           a. Intel® Ethernet Controller XL710 10/40 GbE     - kernel driver i40e
           b. 82599ES 10-Gigabit SFI/SFP+ Network Connection - kernel driver ixgbe
        4. echo "num_vfs" to setup VF on the NIC
                echo 1 > /sys/bus/pci/devices/0000:{pci}/sriov_numvfs
        5. Bring up and configure the PF interfaces to allow the SR-IOV interfaces to be used
           - ifconfig p786p1 up
        6. Find the target SR-IOV interfaces to use:
           - lspci -nn |grep -i virtual
        7. Setup MAC for VF
           - ip link show <PF interface>
           - ip link set <PF interface> vf 0 mac 02:68:b3:29:da:98
           - ip link set <PF interface>  promisc off
        8. Make sure the pci-stub device driver is loaded
           - modprobe pci-stub
        9. The VF interfaces are the target interfaces which have a type ID of ex 8086:10ed.
           Load the VF devices into pci-stub
           - echo "8086 10ed" > /sys/bus/pci/drivers/pci-stub/new_id
        10. Enable unsafe assigned interruptd
           - echo 1 > /sys/module/kvm/parameters/allow_unsafe_assigned_interrupts
        11. Disable transparent hugepage
            - echo never > /sys/kernel/mm/transparent_hugepage/enabled
        12. Set affinity based on socket
            - taskset -pc <numa node cpu id> <qemu thread pid>
 
VM Launch script:
-----------------
a. Setup management bridge for Test harness to connect:
--------------------------------------------------------
 $ brctl addbr br-int
 $ brctl addif br-int <physical interface>

b. Setup scripts for tap creation:
----------------------------------
$ cat /etc/br-ifup
  #!/bin/sh
  bridge='br-int'
  /sbin/ifconfig $1 0.0.0.0 up
  brctl addif ${bridge} $1
$ cat /etc/ovs-ifdown
  #!/bin/sh
  bridge='br-int'
  /sbin/ifconfig $1 0.0.0.0 down
  brctl delif ${bridge} $1

Note: using OVS commands can help in keeping configuration between server reboots.
 
$ brctl addbr br-int
$ brctl addif br-int <physical interface>
setup scripts for tap creation
$ cat ovs-ifup
  #!/bin/sh
  switch='br-int'
  /sbin/ifconfig $1 0.0.0.0 up
  ovs-vsctl add-port ${switch} $1
$ cat ovs-ifdown
  #!/bin/sh
  switch='br-int'
  /sbin/ifconfig $1 0.0.0.0 down
  ovs-vsctl del-port ${switch} $1

Launch VM using qemu:
------------------------
vm=<VM Image>
vm_name=<VM Name>
vnc=1
qemu-system-x86_64 --enable-kvm -m 10240  -smp cores=10,sockets=1,threads=2 -cpu host -hda $vm -boot c \
-pidfile /tmp/vm1.pid -monitor unix:/tmp/vm1monitor,server,nowait \
-enable-kvm -mem-path /dev/hugepages -mem-prealloc \
-net nic,macaddr=00:00:00:11:cc:10 -net tap,script=/etc/ovs-ifup,downscript=/etc/ovs-ifdown \
-device pci-assign,host=83:10.0(VF PCI) -device pci-assign,host=83:10.1(VF PCI) -vnc :$vnc -name $vm_name

Note: For better performance, make sure to set the CPU affinity properly.

In System 1 (Traffic Generator 1)
--------------------------------
1. Download/clone isb repository in install directory (e.g. isb_repo)
2. ./scripts/install.sh --> select [2] to install and setup test harness.

In System 2 (where VNF has to be run) - Run on both Host & VM
--------------------------------------------------------------
1. Download/clone isb repository in install directory (e.g. isb_repo)
2. ./scripts/install.sh --> select [1] to build and install VNF.

In System 3 (Traffic Generator 2)
---------------------------------
1. Download/clone isb repository in install directory (e.g. isb_repo)
2. ./scripts/install.sh --> select [1] to build and install VNF.

IV. Test Topology and execution:
---------------------------------

a. Setup pod.yaml describing Test Harness topology:
-------------------------------------------------
In yardstick configuration it's defined that, trafficgen_1, trafficgen_2 and vnf are the names of the machines.
Configuration required on yardstick server:
        copy /etc/yardstick/nodes/pod.yaml.example to /etc/yardstick/nodes/pod.yaml
        Edit /etc/yardstick/nodes/pod.yaml.
        1. Insert management IPs and login/password of your three machines
        2. Set the "vpci" field to the real PCI addresses of your test adapters.
           Command to get vpci in Ubuntu system: lspci | grep Ether | awk '{print $1}'
           e.g. vpci:      "0000:02:00.1"
        3. Set interface driver name in the pod.yaml file.
           Linux command to get all network interface information: lspci
           e.g. driver:    "ixgbe"
        4. "host" parameter in vnf node (pod.yaml)
            - "host" address will be system which hosts VM in SR-IOV environment.
            - Note - "host" & VM username & password should be same.

        Enable the virtual environment in yardstick machine:
                1. Go to path: <isb_repo>/test_harness/yardstick_venv
                2. Execute command: source bin/activate

b. Throughput Tests:
----------------------------------
        Purpose: To find the maximum throughput supported by VNF with drop percentage between 0.8 - 1.0
        Topology: trafficgen_1(Port 0)-->(Port 0)vnf(Port 1)-->(Port 0)trafficgen_2
        Tools/application to be deployed:
                TG1 - TRex 2.05
                VNF - vCGNAT/vACL/vFW/vPE/vEPC
                TG2 - L4Replay

c. Latency/Jitter Tests:
-----------------------
        Purpose: To find the latency/jitter introduced by VNF when traffic is sent
                 at maximum throughput supported by that VNF
        Topology: trafficgen_1(Port 0)-->(Port 0)vnf(Port 1)-->(Port 0)trafficgen_2
        Tools/application to be deployed:
                TG1 - TRex 2.05
                VNF - vCGNAT/vACL/vFW/vPE
                TG2 - L4Replay

d. Verification Tests:
----------------------
        Purpose: To check the values of the IP header of a packet processed&forwarded
                 by VNF to Public interface
        Topology: trafficgen_1(Port 0)-->(Port 0)vnf(Port 1)-->(Port 0)trafficgen_2
        Tools/application to be deployed:
                TG1 - TRex 2.05
                VNF - vCGNAT/vACL/vFW/vPE
                TG2 - tcpdump

e. HTTP Tests:
-------------
        Purpose: To check time taken by VNF for HTTP request while serving requests
                 from client for accessing files with different sizes
        Topology: trafficgen_1(Port 0)-->(Port 0)vnf(Port 1)-->(Port 0)trafficgen_2
        Tools/application to be deployed:
                TG1 - ab2 (Apache 2.4.7)
                VNF - vCGNAT/vACL/vFW
                TG2 - NGINX (nginx 1.4.6)

f. Attacker Tests:
------------------
        Purpose: To test the TCP synflood attack & ICMP attacks fragmentation attacks
                 for FWL, when FWL is handling normal HTTP requests
        Topology: trafficgen_1(Port 0)-->(Port 0)vnf(Port 1)-->(Port 0)trafficgen_2
        Tools/application to be deployed:
                TG1 - ab2 & Hping (Apache 2.4.7)
                VNF - vFW
                TG2 - NGINX (Apache 2.4.7)

g. Execution of Tests using the CLI
-----------------------------------
        1.  Go to directory <isb_repo>/test_harness (make sure your virtual environment is enabled)
                Enable the virtual environment in yardstick machine:
                        cd <isb_repo>/test_harness
                        source yardstick_venv/bin/activate
        2.  Setup PYTHONPATH, execute cmd: ". ~/.bash_profile"
        3.  Go to directory <isb_repo>/test_harness/cli
                To start the CLI, Execute command: python execute_cli.py
        4.  From the list of supported "Select Traffic Generator", please choose one traffic generator
        5.  From the list of supported "VNF TYPES", please choose one VNF and enter choice accordingly
        6.  From the list of supported "VNF DEPLOYMENT TYPES", choose SRIOV
        7.  From the list of supported "TEST TYPES", choose one of the test type and enter choice accordingly
        8.  From list of supported "IP Protocol", choose one of the IP Protocol type and
            enter choice accordingly ( "IP Protocol" list will not be there if test type is either "http_test" or "attacker_tests"
            in previous step. It will list the test cases as mentioned in step 9)
        9.  From the list of supported "Packet Size", choose one of the packet size and enter choice accordingly
            (for "verification" tests, "packet Size" option will not be there. It will list the test
            cases as mentioned in step 8)
        10. From the list of test cases, please choose one of the test cases and enter the choice accordingly
        11. Test execution will begin and the debug log will be printed on the console.
        12. Once the execution is completed, please check the /tmp/yardstick.out for the result of that test case.
 
h. Execution of Tests using the GUI
----------------------------------
        1. Go to directory <isb_repo>/test_harness/gui (make sure your virtual environment is enabled)
                Enable the virtual environment in yardstick machine:
                        cd <isb_repo>/test_harness
                        source yardstick_venv/bin/activate
        2. Setup PYTHONPATH, execute cmd: ". ~/.bash_profile"
        3. Go to directory <isb_repo>/test_harness/gui
                To start the GUI, Execute command: python yardstick_gui.py
           - To Launch new GUI: python manage.py runserver 0.0.0.0:8000
        4. Access the GUI from browser using URL: http://<YardstickMachine_MgmtIP>:5000/ or new GUI http://<YardstickMachine_MgmtIP>:8000/execute_test/traffic-generator’
        5. Choose one of the network service from the list of supported "Network Service" option. Click on the corresponding button.
        6. Choose one of the Deployment Types from the list of supported "Deployment Types".
           corresponding button. (Currently we support only baremetal deployment type)
        7. From the list of supported "Traffic Profile", choose one of the Traffic Profile and click on the corresponding button.
        8. From the list of supported "IP Version", choose one of the IP Version and click on the corresponding button
           ("IP Protocol" list will not be there if test type is either "http_test" or "attacker_tests"
            in previous step. It will list the test cases as mentioned in step 9)
        9. From the list of supported "Packet Size", choose one of the Packet Size and click on the corresponding button.
           (for "verification" tests, "packet Size" option will not be there. It will list the
           test cases as mentioned in step 8)
        10.  From the list of "Test Cases", choose one of the test cases and click on that test case link.
        11. When test case execution started, a pop-up will be opened to display the console output.
        12. Once test case execution is completed, please check the /tmp/yardstick.out,
            in machine where yardstick is running, for the result of that test case.
        13. From the GUI, output stats for traffic generator and VNF can be viewed.


I. Run manually
------------
        1. Enable the virtual environment in yardstick machine:
           - cd <isb_repo>/test_harness
           - source yardstick_venv/bin/activate
        2. Go to particular folder for the test case type we want to execute.
                e.g. <isb_repo>/test_harness/isb_samples/nsut/<vnf>/<performance measurement type>
                run: yardstick --debug task start <test_case.yaml>
