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
--

tuples = {};

for i = 0,2^23-1 do
    tuples[i] = {if_out = i%4,
                ip_src = i%2^5,
                ip_dst = ((i-i%2^5)/2^5)%2^5,
                port_src = ((i-i%2^10)/2^10)%2^5,
                port_dst = ((i-i%2^15)/2^15)%2^5,
                proto = ((i-i%2^20)/2^20)%2^3 * 2^5,
            }
end

