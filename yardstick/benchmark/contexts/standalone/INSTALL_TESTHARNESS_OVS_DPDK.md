---------------------------------------------------------------------------
                ISB Test Harness - OVS-DPDK Installation Guide.
---------------------------------------------------------------------------

I. Installation, Compile and Execution
-----------------------------------------------------------------
After downloading (or doing a git clone) in a directory (isb_repo)
isb_repo $ ./scripts/install.sh --> select [2] to install Test harness

It will automatically download all the packages needed for test harness setup.

II. System Topology (OVS-DPDK): PHY-VM-PHY
------------------------------------------

                         +----------------------+
                         -                      -
                         -         VM           -
              +-(0) ---->-  ->(VNF running)<-   -<----(1)--+
              -          -                      -          -
              -          +----------------------+          -
              -           - virtio -  - virtio -           -
              -           +--------+  +--------+           -
              -               -            -               -
              -               -            -               -
              -           +--------+  +--------+           -
              -           - vHOST0 -  - vHOST1 -           -
+-------+     -        +------------------------+          -      +------------+
-       -(0) --        -                        -          - (0)->-            -
- TG1   -(1) --        -         HOST           -                 -  L4Replay/ -
-       -     -        -      (OVS-DPDK)        -                 -  Verifier  -
-       -(2) <-        -                        -                 -            -
+-------+              +------------------------+                 +------------+
trafficgen_1                        vnf                             trafficgen_2


III. Setup OVS-DPDK Environment on Host:
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
             -  OVS (DPDK) - 2.5
             -  Hypervisor - KVM
             -  VM OS - Ubuntu 16.04

OVS-DPDK Manual setup:
----------------------
        1. Make sure the host has boot line configuration for 1 GB hugepage memory,
           CPU isolation, and the Intel IOMMU is on and running in PT mode.
           - default_hugepagesz=1GB hugepagesz=1GB hugepages=16
             hugepagesz=2M hugepages=2048 isolcpus=1,2,3,4,5,6,7,28,29,30,31,32,33,34
             iommu=pt intel_iommu=on
             Note: CPU isolation --> Isolate CPUs on Numa Node 0 or 1 based on NIC location.

        2. Installing OVS-DPDK using Ubuntu packages
           - $ sudo apt-get install openvswitch-switch-dpdk
           - $ sudo update-alternatives --set ovs-vswitchd /usr/lib/openvswitch-switch-dpdk/ovs-vswitchd-dpdk

        3. Configuring OVS-DPDK on Ubuntu:
           - /etc/default/openvswitch-switch – Passes in DPDK command-line options to ovs-vswitchd:
           * Specifies the CPU cores on which dpdk lcore threads should be spawned.
             + This needs to be done on the CPU socket where the NIC is installed.
             + Run the command: <isb_repo>/dpdk-16.04/tools/./cpu_layout.py to check the logical core to
               CPU socket mapping 
           * Specifies dpdk-socket-mem to pre-allocate memory from hugepages on specific sockets
               :~# cat /etc/default/openvswitch-switch
                # This is a POSIX shell fragment
                # FORCE_COREFILES: If 'yes' then core files will be enabled.
                # FORCE_COREFILES=yes
                # OVS_CTL_OPTS: Extra options to pass to ovs-ctl.  This is, for example,
                # a suitable place to specify --ovs-vswitchd-wrapper=valgrind.
                # OVS_CTL_OPTS=

                # DPDK options - see /usr/share/doc/openvswitch-common/INSTALL.DPDK.md.gz
                 DPDK_OPTS='--dpdk -c 0x3 -n 4 --socket-mem 2048,0'       (core 0-1 for Socket 0)
                 or
                 DPDK_OPTS='--dpdk -c 0xC00000 -n 4 --socket-mem 0,2048'  (core 22-23 for Socket 1)
                 
           - /etc/dpdk/dpdk.conf – Configures hugepages.
                :~# cat /etc/dpdk/dpdk.conf
                  # The number of 1G hugepages to reserve on system boot
                  # To e.g. let it reserve 2x 1G Hugepages set:
                    NR_1G_PAGES=2

           - /etc/dpdk/interfaces – Configures/assigns NICs for DPDK use
                :~# cat /etc/dpdk/interfaces
                  #
                  # <bus>         Currently only "pci" is supported
                  # <id>          Device ID on the specified bus
                  # <driver>      Driver to bind against (vfio-pci or uio_pci_generic)
                  #
                  # <bus> <id>              <driver>
                    pci   bus:device.func   uio_pci_generic

        4. Setup OVS bridge.
            - ovs-vsctl add-br br0 -- set bridge br0 datapath_type=netdev
            - ovs-vsctl add-port br0 dpdk0 -- set Interface dpdk0 type=dpdk
            - ovs-vsctl add-port br0 dpdk1 -- set Interface dpdk1 type=dpdk
            - ovs-vsctl add-port br0 dpdkvhostuser0 -- set Interface dpdkvhostuser0 type=dpdkvhostuser
            - ovs-vsctl add-port br0 dpdkvhostuser1 -- set Interface dpdkvhostuser1 type=dpdkvhostuser
                
        5. Setup the ovs rules
            # Clear current flows at br0
              - ovs-ofctl del-flows br0

            # Add flows to br0
              - ovs-ofctl add-flow br0 in_port=1,action=output:3
              - ovs-ofctl add-flow br0 in_port=3,action=output:1
              - ovs-ofctl add-flow br0 in_port=4,action=output:2
              - ovs-ofctl add-flow br0 in_port=2,action=output:4

        # Dump flows at br0
              - ovs-ofctl dump-flows br0
                          
        6. Disable transparent hugepage
            - echo never > /sys/kernel/mm/transparent_hugepage/enabled
                
        7. To better scale the work loads across cores, Multiple pmd threads
           can be created and pinned to CPU cores by explicitly specifying pmd-cpu-mask.
           This needs to be done on the CPU socket where the NIC is installed.
           Run the command: <isb_repo>/dpdk-16.04/tools/./cpu_layout.py to check the logical core to socket mapping.
              eg: To spawn 4 pmd threads and pin them to cores on Socket 0: 1, 2, 3, 4
                  - ovs-vsctl set Open_vSwitch . other_config:pmd-cpu-mask=0x1E
              eg: To spawn 4 pmd threads and pin them to cores on socket 1: 25, 26, 27, 28
                  - ovs-vsctl set Open_vSwitch . other_config:pmd-cpu-mask=0xF000000
                
        8. Setup ovs with multiple queue:
            - ovs-vsctl set Open_vSwitch . other_config:n-dpdk-rxqs=4

VM Launch script:
-----------------
a. Setup management bridge for Test harness to connect:
--------------------------------------------------------
# Create a management bridge and the interface to it.
$ ovs-vsctl add-br br-int
$ ovs-vsctl add-port br-int <physical interface>
note: After assigning active interface to bridge we loose internet connectivity.

# Following steps are needed to get the internet back on eno1:
$ dhclient br-int
$ ifconfig eno1 0.0.0.0
$ ifconfig br-int
$ route add default gw <gateway IP> br-int

                +-----+------+
                |  IP stack  |
                +-----+------+  
                      | 
eth0/eno1--------+    |
(active)         |    | 
                 |    | 
          +-----+-----+---------+
          |  management-bridge  |
          |      (br-int)       | 
          +---------------------+         
Fig: Internal ovs-bridge set-up for management interface
          
# Setup scripts for tap creation:
# These scripts needs to be created at "/etc" location for the management IP of VM which will be used by test-harness:
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

# make the scripts executable:
$ chmod +x /etc/ovs-ifup
$ chmod +x /etc/ovs-down
  
Launch VM using qemu:
------------------------
export VM_NAME=vhost-vm
export GUEST_MEM=10240M
export QCOW2_IMAGE=<VM Image>
export VHOST_SOCK_DIR=/var/run/openvswitch

Note: Set qemu thread affinity based on CPU socket where NIC is installed 
    - taskset -pc <numa node cpu id> <qemu thread pid>
        
taskset 0xe qemu-system-x86_64 -name $VM_NAME -cpu host -enable-kvm -m $GUEST_MEM -object memory-backend-file,id=mem,size=$GUEST_MEM,mem-path=/dev/hugepages,share=on -numa node,memdev=mem -mem-prealloc -smp sockets=1,cores=10,threads=2 -drive file=$QCOW2_IMAGE -net nic,macaddr=00:00:00:00:cc:10 -net tap,script=/etc/ovs-ifup,downscript=/etc/ovs-ifdown -chardev socket,id=char0,path=$VHOST_SOCK_DIR/dpdkvhostuser0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=4 -device virtio-net-pci,mac=00:00:00:00:00:03,netdev=mynet1,mq=on,vectors=10,csum=on,mrg_rxbuf=off -chardev socket,id=char1,path=$VHOST_SOCK_DIR/dpdkvhostuser1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce,queues=4 -device virtio-net-pci,mac=00:00:00:00:00:04,netdev=mynet2,mq=on,vectors=10,csum=on,mrg_rxbuf=off --nographic  -vnc :1 -redir tcp:2222::22

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
           e.g. vpci:      "0000:00:04.0"
           Note: For the "vnf" system, it should be PCI address of the virtual NIC's created by qemu.
        3. Set interface driver name in the pod.yaml file.
           Linux command to get all network interface information: lspci
           e.g. driver:    "ixgbe"               #In case of "trafficgen_1" and "trafficgen_2" as per physical NIC driver
           e.g. driver:    "virtio-pci"  #In the "vnf" system where OVS-DPDK is running, virtio-pci is the driver
        4. "host" parameter in vnf node (pod.yaml)
            - In the "vnf" system: 
                        - "host" & VM username & password should be same.
                        - ip: <IP of the VM running vnf>
                        - host: <system which hosts VM in ovs-dpdk environment.>

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
        6.  From the list of supported "VNF DEPLOYMENT TYPES", choose OVS
        7.  From the list of supported "TEST TYPES", choose one of the test type and enter choice accordingly
        8.  From list of supported "IP Protocol", choose one of the IP Protocol type and
            enter choice accordingly ( "IP Protocol" list will not be there if test type is either "http_test" or "attacker_tests"
            in previous step. It will list the test cases as mentioned in step 8)
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
        6. Click on the "OVS" Deployment Type from the list of supported "Deployment Types"
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
