#!/bin/bash
sudo apt-get update -y
sudo apt-get install createrepo rpm dpkg-dev -y
sudo apt-get install python-setuptools -y
sudo apt-get install python-pip -y
sudo easy_install pip
sudo pip install fuel-plugin-builder
sudo apt-get install ruby -y
sudo gem install rubygems-update
sudo gem install fpm
sudo apt-get install docker.io -y
cp -r /yardstick /home/vagrant
cd /home/vagrant/yardstick/fuel-plugin;
rm -rf vagrant/.vagrant
fpb --debug --build .
cp *.rpm /vagrant
