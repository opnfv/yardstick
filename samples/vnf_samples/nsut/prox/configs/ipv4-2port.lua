--
-- Copyright (c) 2010-2017 Intel Corporation
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--

require("parameters")

local lpm4 = {}
lpm4.next_hops = {
   {id = 0,  port_id = 0, ip = ip("1.1.1.1"),  mac = mac(tester_mac0), mpls = 0x112},
   {id = 1,  port_id = 1, ip = ip("2.1.1.1"),  mac = mac(tester_mac1), mpls = 0x212},
   {id = 2,  port_id = 0, ip = ip("3.1.1.1"),  mac = mac(tester_mac0), mpls = 0x312},
   {id = 3,  port_id = 1, ip = ip("4.1.1.1"),  mac = mac(tester_mac1), mpls = 0x412},
   {id = 4,  port_id = 0, ip = ip("5.1.1.1"),  mac = mac(tester_mac0), mpls = 0x512},
   {id = 5,  port_id = 1, ip = ip("6.1.1.1"),  mac = mac(tester_mac1), mpls = 0x612},
   {id = 6,  port_id = 0, ip = ip("7.1.1.1"),  mac = mac(tester_mac0), mpls = 0x712},
   {id = 7,  port_id = 1, ip = ip("8.1.1.1"),  mac = mac(tester_mac1), mpls = 0x812},
   {id = 8,  port_id = 0, ip = ip("9.1.1.1"),  mac = mac(tester_mac0), mpls = 0x912},
   {id = 9,  port_id = 1, ip = ip("10.1.1.1"), mac = mac(tester_mac1), mpls = 0x1012},
   {id = 10, port_id = 0, ip = ip("11.1.1.1"), mac = mac(tester_mac0), mpls = 0x1112},
   {id = 11, port_id = 1, ip = ip("12.1.1.1"), mac = mac(tester_mac1), mpls = 0x1212},
   {id = 12, port_id = 0, ip = ip("13.1.1.1"), mac = mac(tester_mac0), mpls = 0x1312},
   {id = 13, port_id = 1, ip = ip("14.1.1.1"), mac = mac(tester_mac1), mpls = 0x1412},
   {id = 14, port_id = 0, ip = ip("15.1.1.1"), mac = mac(tester_mac0), mpls = 0x1512},
   {id = 15, port_id = 1, ip = ip("16.1.1.1"), mac = mac(tester_mac1), mpls = 0x1612},
   {id = 16, port_id = 0, ip = ip("17.1.1.1"), mac = mac(tester_mac0), mpls = 0x1712},
   {id = 17, port_id = 1, ip = ip("18.1.1.1"), mac = mac(tester_mac1), mpls = 0x1812},
   {id = 18, port_id = 0, ip = ip("19.1.1.1"), mac = mac(tester_mac0), mpls = 0x1912},
   {id = 19, port_id = 1, ip = ip("20.1.1.1"), mac = mac(tester_mac1), mpls = 0x2012},
   {id = 20, port_id = 0, ip = ip("21.1.1.1"), mac = mac(tester_mac0), mpls = 0x2112},
   {id = 21, port_id = 1, ip = ip("22.1.1.1"), mac = mac(tester_mac1), mpls = 0x2212},
   {id = 22, port_id = 0, ip = ip("23.1.1.1"), mac = mac(tester_mac0), mpls = 0x2312},
   {id = 23, port_id = 1, ip = ip("24.1.1.1"), mac = mac(tester_mac1), mpls = 0x2412},
   {id = 24, port_id = 0, ip = ip("25.1.1.1"), mac = mac(tester_mac0), mpls = 0x2512},
   {id = 25, port_id = 1, ip = ip("26.1.1.1"), mac = mac(tester_mac1), mpls = 0x2612},
   {id = 26, port_id = 0, ip = ip("27.1.1.1"), mac = mac(tester_mac0), mpls = 0x2712},
   {id = 27, port_id = 1, ip = ip("28.1.1.1"), mac = mac(tester_mac1), mpls = 0x2812},
   {id = 28, port_id = 0, ip = ip("29.1.1.1"), mac = mac(tester_mac0), mpls = 0x2912},
   {id = 29, port_id = 1, ip = ip("30.1.1.1"), mac = mac(tester_mac1), mpls = 0x3012},
   {id = 30, port_id = 0, ip = ip("31.1.1.1"), mac = mac(tester_mac0), mpls = 0x3112},
   {id = 31, port_id = 1, ip = ip("32.1.1.1"), mac = mac(tester_mac1), mpls = 0x3212},
   {id = 32, port_id = 0, ip = ip("33.1.1.1"), mac = mac(tester_mac0), mpls = 0x3312},
   {id = 33, port_id = 1, ip = ip("34.1.1.1"), mac = mac(tester_mac1), mpls = 0x3412},
   {id = 34, port_id = 0, ip = ip("35.1.1.1"), mac = mac(tester_mac0), mpls = 0x3512},
   {id = 35, port_id = 1, ip = ip("36.1.1.1"), mac = mac(tester_mac1), mpls = 0x3612},
   {id = 36, port_id = 0, ip = ip("37.1.1.1"), mac = mac(tester_mac0), mpls = 0x3712},
   {id = 37, port_id = 1, ip = ip("38.1.1.1"), mac = mac(tester_mac1), mpls = 0x3812},
   {id = 38, port_id = 0, ip = ip("39.1.1.1"), mac = mac(tester_mac0), mpls = 0x3912},
   {id = 39, port_id = 1, ip = ip("40.1.1.1"), mac = mac(tester_mac1), mpls = 0x4012},
   {id = 40, port_id = 0, ip = ip("41.1.1.1"), mac = mac(tester_mac0), mpls = 0x4112},
   {id = 41, port_id = 1, ip = ip("42.1.1.1"), mac = mac(tester_mac1), mpls = 0x4212},
   {id = 42, port_id = 0, ip = ip("43.1.1.1"), mac = mac(tester_mac0), mpls = 0x4312},
   {id = 43, port_id = 1, ip = ip("44.1.1.1"), mac = mac(tester_mac1), mpls = 0x4412},
   {id = 44, port_id = 0, ip = ip("45.1.1.1"), mac = mac(tester_mac0), mpls = 0x4512},
   {id = 45, port_id = 1, ip = ip("46.1.1.1"), mac = mac(tester_mac1), mpls = 0x4612},
   {id = 46, port_id = 0, ip = ip("47.1.1.1"), mac = mac(tester_mac0), mpls = 0x4712},
   {id = 47, port_id = 1, ip = ip("48.1.1.1"), mac = mac(tester_mac1), mpls = 0x4812},
   {id = 48, port_id = 0, ip = ip("49.1.1.1"), mac = mac(tester_mac0), mpls = 0x4912},
   {id = 49, port_id = 1, ip = ip("50.1.1.1"), mac = mac(tester_mac1), mpls = 0x5012},
   {id = 50, port_id = 0, ip = ip("51.1.1.1"), mac = mac(tester_mac0), mpls = 0x5112},
   {id = 51, port_id = 1, ip = ip("52.1.1.1"), mac = mac(tester_mac1), mpls = 0x5212},
   {id = 52, port_id = 0, ip = ip("53.1.1.1"), mac = mac(tester_mac0), mpls = 0x5312},
   {id = 53, port_id = 1, ip = ip("54.1.1.1"), mac = mac(tester_mac1), mpls = 0x5412},
   {id = 54, port_id = 0, ip = ip("55.1.1.1"), mac = mac(tester_mac0), mpls = 0x5512},
   {id = 55, port_id = 1, ip = ip("56.1.1.1"), mac = mac(tester_mac1), mpls = 0x5612},
   {id = 56, port_id = 0, ip = ip("57.1.1.1"), mac = mac(tester_mac0), mpls = 0x5712},
   {id = 57, port_id = 1, ip = ip("58.1.1.1"), mac = mac(tester_mac1), mpls = 0x5812},
   {id = 58, port_id = 0, ip = ip("59.1.1.1"), mac = mac(tester_mac0), mpls = 0x5912},
   {id = 59, port_id = 1, ip = ip("60.1.1.1"), mac = mac(tester_mac1), mpls = 0x6012},
   {id = 60, port_id = 0, ip = ip("61.1.1.1"), mac = mac(tester_mac0), mpls = 0x6112},
   {id = 61, port_id = 1, ip = ip("62.1.1.1"), mac = mac(tester_mac1), mpls = 0x6212},
   {id = 62, port_id = 0, ip = ip("63.1.1.1"), mac = mac(tester_mac0), mpls = 0x6312},
   {id = 63, port_id = 1, ip = ip("64.1.1.1"), mac = mac(tester_mac1), mpls = 0x6412},
}

lpm4.routes = {};

base_ip = 10 * 2^24;

for i = 1,2^13 do
   res = ip(base_ip + (1 * 2^12) * (i - 1));

   lpm4.routes[i] = {
      cidr        = {ip = res, depth = 24},
      next_hop_id = (i - 1) % 64,
   }
end

return lpm4
