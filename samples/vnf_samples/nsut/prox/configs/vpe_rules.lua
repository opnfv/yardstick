-- Copyright (c) 2016-2017 Intel Corporation
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--      http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--

seven_tuple = function(svlan, cvlan, ip_proto, src, dst, sport, dport, action)
   return {
      svlan_id = svlan,
      cvlan_id = cvlan,
      ip_proto = ip_proto,
      src_cidr = src,
      dst_cidr = dst,
      sport    = sport,
      dport    = dport,
      action   = action,
   }
end

rules2={};
sports={0,2,4,6,8,10,12,14};
src_t={{s="192.168.0.0/18", svlan1=0, svlan2=1},
       {s="192.168.16.0/18", svlan1=16, svlan2=17},
       {s="192.168.32.0/18", svlan1=32, svlan2=33},
       {s="192.168.48.0/18", svlan1=48, svlan2=49},
      };

for srck,srcv in pairs(src_t) do
 for cvlan_mask = 0,255 do
  for spk,spv in pairs(sports) do
    table.insert(rules2,seven_tuple(val_mask(srcv.svlan1,0x0fff), val_mask(cvlan_mask,0x0fff), val_mask(17,0xff), cidr(srcv.s), cidr("10.0.0.0/7"), val_range(spv,spv), val_range(0,511), "allow"));
    table.insert(rules2,seven_tuple(val_mask(srcv.svlan1,0x0fff), val_mask(cvlan_mask,0x0fff), val_mask(17,0xff), cidr(srcv.s), cidr("74.0.0.0/7"), val_range(spv,spv), val_range(0,511), "allow"));
    table.insert(rules2,seven_tuple(val_mask(srcv.svlan2,0x0fff), val_mask(cvlan_mask,0x0fff), val_mask(17,0xff), cidr(srcv.s), cidr("10.0.0.0/7"), val_range(spv,spv), val_range(0,511), "allow"));
    table.insert(rules2,seven_tuple(val_mask(srcv.svlan2,0x0fff), val_mask(cvlan_mask,0x0fff), val_mask(17,0xff), cidr(srcv.s), cidr("74.0.0.0/7"), val_range(spv,spv), val_range(0,511), "allow"));
   table.insert(rules2,rules4);
  end
 end
end

return rules2

