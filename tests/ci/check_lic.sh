#! /bin/bash
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

check_no_lic_extention() {
  file=$1
  ret=1
  filename=$(basename "$file")
  extension="${filename##*.}"
  filename="${filename%*.}"
  no_lic_ext="txt rst json"

  for ext in $no_lic_ext; do
    if [[ "$extension" == "$ext" || "$extension" == "$filename" ]]; then
      ret=0
      return
    fi
  done
}

verify_license() {
  file=$1
  head -n10 "${file}" | grep -Eq "(Copyright|generated|GENERATED|Licensed)"
  if [[ "$?" == "0" ]]; then
     echo "Verify License header for '$file' - successful"
     return
  fi
  echo "Verify License header for '$file' - failed"
  exit 255
}

check_for_license() {
  files=$(git diff HEAD~1 --name-only)

  for x in $files; do
    if [ -f "$x" ]; then
         check_no_lic_extention "$x"
         if [[ "$ret" == "1" ]]; then # if file not in no lic extention
            verify_license "$x"
         fi
    fi
  done;
}
