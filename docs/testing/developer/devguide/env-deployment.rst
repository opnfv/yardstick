=========================
Environment deployment
=========================
.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB, Huawei Technologies Co.,Ltd, Intel and others.

Install OpenStack with APEX
===========================
Apex is based on the OpenStack Triple-O project as distributed by the RDO Project.
It is important to understand the basics of a Triple-O deployment to help make
decisions that will assist in successfully deploying OPNFV.

This is an installation guide for APEX with CentOS 7.
If behind a proxy the following should be set on the host::

    http_proxy="http://<proxy_address>:<proxy_port>"
    https_proxy="http://<proxy_address>:<proxy_port>"

It is advised to put the proxy settings in ``/etc/enviroment``.

More Information about APEX can be found at `APEX installation instructions`_
Source code can be found at `APEX source code`_

Guide
=====
Update the system

.. code-block:: bash

    yum -y update
    
Install dependancies

.. code-block:: bash

    yum install -y yum-utils
    yum install -y wget
    yum install -y epel-release
    yum install -y python34
    yum install -y python-docutils

Make a directory to hold the rpm's.
Create a script within this directory to pull the rpm's.
Give the script executable permissions and execute it

.. code-block:: bash

    mkdir ~/apex-rpms
    cd ~/apex-rpms
    #create a script to pull rpm's
    cat > wget_rpms.sh << _EOF_
    wget http://artifacts.opnfv.org/apex/euphrates/yumrepo/python3-ipmi-0.3.0-1.noarch.rpm
    wget http://artifacts.opnfv.org/apex/euphrates/yumrepo/python34-PrettyTable-0.7.2-1.el7.centos.noarch.rpm
    wget http://artifacts.opnfv.org/apex/euphrates/yumrepo/python34-asn1crypto-0.22.0-1.el7.centos.noarch.rpm
    wget http://artifacts.opnfv.org/apex/euphrates/yumrepo/python34-cryptography-2.0.3-1.el7.centos.x86_64.rpm
    wget http://artifacts.opnfv.org/apex/euphrates/yumrepo/python34-iptables-0.12.0-1.el7.centos.x86_64.rpm
    wget http://artifacts.opnfv.org/apex/euphrates/yumrepo/python34-libvirt-3.6.0-1.el7.centos.x86_64.rpm
    wget http://artifacts.opnfv.org/apex/euphrates/yumrepo/python34-pbr-3.1.1-1.el7.centos.x86_64.rpm
    wget http://artifacts.opnfv.org/apex/euphrates/yumrepo/python34-pycrypto-2.6.1-1.el7.centos.x86_64.rpm
    wget http://artifacts.opnfv.org/apex/euphrates/yumrepo/python34-pyghmi-1.0.22-1.el7.centos.noarch.rpm
    wget http://artifacts.opnfv.org/apex/euphrates/yumrepo/python34-virtualbmc-1.2.0-1.el7.centos.noarch.rpm
    _EOF_
    chmod +x wget_rpms.sh
    ./wget_rpms.sh
    yum install -y ./*.rpm

Install the following

.. code-block:: bash

    yum install -y https://repos.fedorapeople.org/repos/openstack/openstack-ocata/rdo-release-ocata-2.noarch.rpm
    cd /etc/yum.repos.d && wget artifacts.opnfv.org/apex/euphrates/opnfv-apex.repo

Reboot the host

.. code-block:: bash

    reboot

After the host is rebooted, clone the APEX repo

.. code-block:: bash

    cd ~
    git clone https://gerrit.opnfv.org/gerrit/p/apex.git
    cd ~/apex
    git checkout stable/euphrates

If behind a proxy edit `configure_undercloud.yml`.

.. code-block:: bash

    vim ./lib/ansible/playbooks/configure_undercloud.yml



Change the start of `configure_undercloud.yml` to look like the following.
Remember to put your proxy setting in place of `http://proxy.com:123`

.. code-block:: bash

    - hosts: all
      tasks:
        - name: insert proxy settings
          shell: echo "export http_proxy=http://proxy.com:123" >> /etc/environment
        - name: insert proxy settings
          shell: echo "export https_proxy=https://proxy.com:123" >> /etc/environment
        - name: insert proxy settings
          shell: echo "export no_proxy=$no_proxy,192.0.2.1" >> /etc/environment
        - name: source proxy settings
          shell: . /etc/environment
        - name: Generate SSH key for stack if missing
          shell: test -e ~/.ssh/id_rsa || ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
        - name: Fix ssh key for stack

Clean previous build. Set the python environment variable

.. code-block:: bash

    cd build
    make clean
    mkdir -p ~/apex-cache
    export PYTHONPATH=~/apex:$PYTHONPATH

Install python dependencies

.. code-block:: bash

    yum install -y python34-pip
    pip3 install pyyaml
    yum install -y python-pip
    yum install -y ansible
    yum install -y openvswitch

Build APEX

.. code-block:: bash 

    cd ../apex
    python3 build.py -c ~/apex-cache -r dev1

Configure virsh

.. code-block:: bash

    virsh pool-define-as default dir --target /var/lib/libvirt/images/
    virsh pool-autostart default
    virsh pool-start default

Destroy any APEX VMs that may already be running.
This command should fail if APEX has not been deployed before.
 
.. code-block:: bash

    python3 clean.py

Deploy APEX

.. code-block:: bash

    python3 deploy.py -v -n ../config/network/network_settings.yaml -d ../config/deploy/os-nosdn-nofeature-noha.yaml --deploy-dir ../build --lib-dir ../lib --image-dir ../.build --virtual-compute-ram 40

References
==========

.. _`APEX installation instruction`: http://artifacts.opnfv.org/apex/docs/installation-instructions/architecture.html
.. _`APEX source code`: https://github.com/opnfv/apex

