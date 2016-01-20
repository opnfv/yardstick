# Copyright (c) 2015 Intel Research and Development Ireland Ltd.
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

INPUT_FILE=$1
VLAN_TAG=$2

tcprewrite --enet-vlan=add --enet-vlan-tag=$VLAN_TAG --enet-vlan-cfi=0 --enet-vlan-pri=0 --infile=$INPUT_FILE --outfile=$INPUT_FILE
