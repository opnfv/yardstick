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
sudo apt-get update -y
sudo apt-get install -y ruby-dev rubygems-integration python-pip rpm createrepo dpkg-dev
sudo gem install fpm
sudo pip install fuel-plugin-builder
cp -r /yardstick /home/vagrant
cd /home/vagrant/yardstick/fuel-plugin;
rm -rf vagrant/.vagrant
fpb --debug --build .
cp *.rpm /vagrant
