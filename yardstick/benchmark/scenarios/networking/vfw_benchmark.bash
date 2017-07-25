#!/bin/bash

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

# Clone samplevnf and run the tescase
download_build_vnf()
{
  which /usr/bin/vFW >/dev/null
	if [ $? -eq 0 ]
	then
	    echo "vFW already installed. Done"
  else
      # git clone samplevnf (https://gerrit.opnfv.org/gerrit/samplevnf)
      git clone https://gerrit.opnfv.org/gerrit/samplevnf
      pushd .
      cd samplevnf
      bash ./tools/vnf_build.sh --silient '17.05'
      cp VNFs/vFW/build/vFW /usr/bin/
      popd
  fi
}

bind_pci()
{
			if [ -d "/sys/bus/pci/drivers/ixgbe" ]; then
							pci=$(find /sys/class/net -lname "*$1*" -printf '%f')
							if [[ "$pci" != "" ]]; then
							    $(echo "$1" > "/sys/bus/pci/drivers/ixgbe/unbind")
							fi
							pci=$(find /sys/class/net -lname "*$2*" -printf '%f')
							if [[ "$pci" != "" ]]; then
							    $(echo "$2" > "/sys/bus/pci/drivers/ixgbe/unbind")
							fi
			fi
   sleep 1

			if [ -d "/sys/bus/pci/drivers/i40e" ]; then
							pci=$(find /sys/class/net -lname "*$1*" -printf '%f')
							if [[ "$pci" != "" ]]; then
							    $(echo "$1" > "/sys/bus/pci/drivers/i40e/unbind")
							fi
							pci=$(find /sys/class/net -lname "*$2*" -printf '%f')
							if [[ "$pci" != "" ]]; then
							    $(echo "$2" > "/sys/bus/pci/drivers/i40e/unbind")
							fi
			fi
   sleep 1

			if [ -d "/sys/bus/pci/drivers/igb_uio" ]; then
							$(echo "$1" > "/sys/bus/pci/drivers/igb_uio/bind")
							$(echo "$2" > "/sys/bus/pci/drivers/igb_uio/bind")
			fi
   sleep 1
}

# main entry
main()
{
	  if [[ "$1" == "" || "$2" == "" ]]; then
				echo "Invalid PCIs."
				exit 1
		fi
    # Source env variables
    export http_proxy=proxy02.isng.intel.com:911
    export https_proxy=proxy02.isng.intel.com:911
	  echo "Build and install samplevnf (vfw)"
		download_build_vnf
		bind_pci $1 $2
    modprobe uio 
}

main $1 $2
