#!/bin/bash

set -eux

HOST=$1
INSTALL_HOME=/opt/yardstick
rm -rf $INSTALL_HOME; mkdir -p $INSTALL_HOME

cd $INSTALL_HOME

sudo apt-get install -y python-virtualenv python-dev python-pip libffi-dev libssl-dev libxml2-dev libxslt1-dev
pip install --user virtualenv
pip install --upgrade virtualenv

# create python virtual env
virtualenv $INSTALL_HOME/yardstick_venv
# source $INSTALL_HOME/yardstick_venv/bin/activate

easy_install -U setuptools

mkdir bin
cd $INSTALL_HOME/bin

curl http://$HOST:8080/plugins/fuel-plugin-yardstick-0.9/repositories/ubuntu/yardstick.tar.gz | tar xzvf -

pip install -r tests/ci/requirements.txt
