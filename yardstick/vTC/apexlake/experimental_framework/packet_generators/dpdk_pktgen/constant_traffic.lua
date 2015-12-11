-----------------------------------------------------------------------------
-- Copyright (c) 2015 Intel Research and Development Ireland Ltd.
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
-----------------------------------------------------------------------------

-----------------------------------
----- Constant traffic sender -----
-----------------------------------

package.path = package.path ..";?.lua;test/?.lua;app/?.lua;../?.lua"
require "Pktgen";

----- Packet Gen Configuration
local sendport = "0";
pktgen.vlan(sendport, "on");
pktgen.ping4("all");
pktgen.icmp_echo("all", "on");
pktgen.process("all", "on");


----- Script Configuration
local traffic_delay = 0;
local traffic_rate = 0;
local out_file = "";


function start_traffic(rate)
    local endStats, diff, prev, iteration, flag, found;
    flag = false;
    found = false;

    -- Send traffic at the specified rate
    print("Start Generation");
    pktgen.set(sendport, "rate", rate);
    sleep(1);
    pktgen.start(sendport);
    sleep(traffic_delay);
    pktgen.stop(sendport);
    print("Stop Generation");

    -- Collect statistics about the experiment
    endStats = pktgen.portStats("all", "port");
    sent_packets = endStats[0].opackets
    return sent_packets;
end


pktgen.clr();
print("INSTANTIATION VALIDATION TEST")

-- Write output on log file
file = io.open(out_file, "w");

-- Start experiment
packets = start_traffic(traffic_rate);
print("SENT PACKETS: " .. packets);
file:write(packets);

-- Close the log file
file:close();

-- Quit the environment
os.exit(1);
