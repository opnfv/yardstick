#!/bin/bash
sudo apt-get update -y
sudo apt-get install -y ruby-dev rubygems-integration python-pip rpm createrepo dpkg-dev
sudo gem install fpm
sudo pip install fuel-plugin-builder
cp -r /yardstick /home/vagrant
cd /home/vagrant/yardstick/fuel-plugin;
rm -rf vagrant/.vagrant
fpb --debug --build .
cp *.rpm /vagrant
