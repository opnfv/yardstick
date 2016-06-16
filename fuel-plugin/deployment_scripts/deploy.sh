#!/bin/bash
apt-get update
#apt-get install -y python-dev python-virtualenv libxml2-dev libffi-dev
#apt-get install -y python-pip git libz-dev
apt-get install -y python-dev python-virtualenv
apt-get install -y libssl-dev libffi-dev

pip install --user virtualenv
pip install --upgrade virtualenv
# create python virtual env
virtualenv ~/yardstick_venv
source ~/yardstick_env/bin/activate
easy_install -U setuptools
# get yardstick source, build dependencies, install
cp yardstick.tar.gz ~/
cd ~/
tar -xvf yardstick.tar.gz
rm -r yardstick.tar.gz
cd yardstick

pip install -r ci/requirements.txt > install-requirements.txt
pip install .

