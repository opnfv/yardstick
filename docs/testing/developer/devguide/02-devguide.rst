Introduction
=============
The following is an insallation guide for apex with centos7 when the host is behing a proxy.
The following should be set on the host.
http_proxy=http://proxy.com:123
https_proxy=https://proxy.com:123
where :123 is the port used by your proxy.
It is advised to put the proxy settings in /etc/enviroment.
Information about apex can be found at http://artifacts.opnfv.org/apex/docs/installation-instructions/architecture.html
Apex source code can be found at https://github.com/opnfv/apex

Guide
======
yum -y update
yum install -y yum-utils
yum install -y wget
yum install -y epel-release
yum install -y python34
yum install -y python-docutils
mkdir apex-rpms
cd apex-rpms
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
yum install -y https://repos.fedorapeople.org/repos/openstack/openstack-ocata/rdo-release-ocata-2.noarch.rpm
cd /etc/yum.repos.d && wget artifacts.opnfv.org/apex/euphrates/opnfv-apex.repo
reboot
cd ~
git clone https://gerrit.opnfv.org/gerrit/p/apex.git
cd apex
git checkout stable/euphrates
./lib/ansible/playbooks/configure_undercloud.yml

#Change the start of the file to look like the following
#Remember to put your proxy setting in place of http://proxy.com:123

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


cd build
make clean
mkdir -p ~/apex-cache
cd ../apex
export PYTHONPATH=~/apex:$PYTHONPATH
yum install -y python34-pip
pip3 install pyyaml
yum install -y python-pip
yum install -y ansible
yum install -y openvswitch
python3 build.py -c ~/apex-cache -r dev1
virsh pool-define-as default dir --target /var/lib/libvirt/images/
virsh pool-autostart default
virsh pool-start default

python3 clean.py #(its ok if this command fails)

python3 deploy.py -v -n ../config/network/network_settings.yaml -d ../config/deploy/os-nosdn-nofeature-noha.yaml --deploy-dir ../build --lib-dir ../lib --image-dir ../.build --virtual-compute-ram 40
