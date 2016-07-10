#!/bin/bash

set -eux

HOST=$1
BIN_HOME=/opt/yardstick
VAR_HOME=/var/lib/yardstick
rm -rf $BIN_HOME; mkdir -p $BIN_HOME
rm -rf $VAR_HOME; mkdir -p $VAR_HOME

sudo apt-get install -y python-dev python-pip libffi-dev libssl-dev libxml2-dev libxslt1-dev
pip install virtualenv

# create python virtual env
virtualenv $VAR_HOME

export PS1="yardstick"
source $VAR_HOME/bin/activate

easy_install -U setuptools

cd $BIN_HOME

curl http://$HOST:8080/plugins/fuel-plugin-yardstick-0.9/repositories/ubuntu/yardstick.tar.gz | tar xzvf -

python setup.py develop
