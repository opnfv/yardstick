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
from optparse import OptionParser
import os
parser = OptionParser()
#parser.add_option("--image", dest="image",
#                  help="normal nsb, what image type should be used?")
parser.add_option("--installation_mode", dest="installation_mode",
                  help="container baremetal, type of deployment?")
parser.add_option("--yardstick_dir", dest="yardstick_dir",
                  help="/home/user/yardstick, The full path to the yardstick directory")
parser.add_option("--virtual_environment", dest="virtual_environment",
                  help="True False, use a virtual environment for python?")
parser.add_option("--nsb_dir", dest="nsb_dir",
                  help="nsb_dir, The full path to the nsb directory")

(options,args) = parser.parse_args()
cmd= "ansible-playbook"
for opt, value in options.__dict__.items():
  if value!=None:
    cmd += " --extra-vars "+opt.upper()+"="+value

os.system("echo " +cmd)
