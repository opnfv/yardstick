#!/usr/bin/env python
# Copyright (c) 2018 Intel Corporation.
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

import argparse
import os


parser = argparse.ArgumentParser()
parser.add_argument("--installation-mode", dest="installation_mode",
                  help="container baremetal, type of deployment?")
parser.add_argument("--yardstick-dir", dest="yardstick_dir",
                  default="/home/user/yardstick/",
                  help="/home/user/yardstick/, The full path to the yardstick directory")
parser.add_argument("--virtual-environment", dest="virtual_environment",
                  help="True False, use a virtual environment for python?")
parser.add_argument("--nsb-dir", dest="nsb_dir",
                  help="The full path to the nsb directory")

options = parser.parse_args()

cmd= "ansible-playbook "+options.yardstick_dir+"ansible/install.yaml"
for opt, value in options.__dict__.items():
  if value!=None:
    cmd += " --extra-vars "+opt.upper()+"="+value

os.system(cmd)
