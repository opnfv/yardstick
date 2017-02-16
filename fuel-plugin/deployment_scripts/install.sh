# Copyright (c) 2016-2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/bin/bash

set -eux

HOST=$1
BIN_HOME=/opt/yardstick
VAR_HOME=/var/lib/yardstick
rm -rf $BIN_HOME; mkdir -p $BIN_HOME
rm -rf $VAR_HOME; mkdir -p $VAR_HOME

apt-get install -y python-dev python-pip libffi-dev libssl-dev libxml2-dev libxslt1-dev

#apt-get install python-virtualenv cannot work
#use pip to work around the issue

pip install virtualenv

# create python virtual env
virtualenv $VAR_HOME

export PS1="yardstick"
source $VAR_HOME/bin/activate

easy_install -U setuptools

cd $BIN_HOME

curl http://$HOST:8080/plugins/fuel-plugin-yardstick-1.0/repositories/ubuntu/yardstick.tar.gz | tar xzvf -

# install dependency
pip install -r requirements.txt

python setup.py install
