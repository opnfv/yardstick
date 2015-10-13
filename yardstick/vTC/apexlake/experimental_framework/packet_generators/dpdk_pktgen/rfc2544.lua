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

-------------------------------
----- RFC-2544 throughput -----
-------------------------------

package.path = package.path ..";?.lua;test/?.lua;app/?.lua;../?.lua"
require "Pktgen";

----- Packet Gen Configuration
local sendport = "0";
local recvport = "1";
pktgen.set(recvport, "rate", 1);
pktgen.vlan(sendport, "on");
pktgen.ping4("all");
pktgen.icmp_echo("all", "on");
pktgen.process("all", "on");


----- RFC2544 Configuration
local traffic_delay = 60;		-- Time in seconds to delay.
local multicast_delay = 15;		-- Time in seconds to delay.

local starting_rate = 100;		-- Initial Rate in %
local step = 100;               -- Initial Step in %
local down_limit = 0;
local up_limit = 100;


-- Creation of a module
--local rfc2544 = {}
function start_traffic(rate)
    local endStats, diff, prev, iteration, flag, found;
    flag = false;
    found = false;

    print("PACKET GENERATION - " .. rate .. "%\n");

    -- Send packet to join the multicast group
    print("Join Multicast Group")
    pktgen.start(recvport);
    sleep(multicast_delay);
    pktgen.stop(recvport)
    pktgen.clr();


    -- Send traffic at the specified rate
    print("Start Generation");
    pktgen.set(sendport, "rate", rate);
    sleep(1);
    pktgen.start(sendport);
    sleep(traffic_delay);
    pktgen.stop(sendport);
    print("Stop Generation");
    sleep(5);

    -- Collect statistics about the experiment
    endStats = pktgen.portStats("all", "port");
    diff = endStats[0].opackets - endStats[1].ipackets;
    if ( endStats[0].opackets <= 0) then
        diff = 0;
    else
        diff = diff / endStats[0].opackets;
    end
    pktgen.clr();

    print("Missing packets: " .. (diff * 100));

    -- Adjust variable for the next race
    prev_rate = rate;
    step = step/2;

    if ( diff > 0.01) then
        if(endStats[0].opackets > 0) then
            up_limit = rate;
            rate = math.floor(rate - (step));
        end
    else
	down_limit = rate;
        rate = math.floor(rate + (step));
        print("\nRATE: " .. rate .. " RECEIVED PACKETS: " .. endStats[1].ipackets .. " ")
	found = true;
    end

    printf("DOWN LIMIT: %d\n", down_limit);
    printf("UP LIMIT: %d\n", up_limit);

    if ( rate >= 100 ) then
        rate = 100;
    end

    if ( prev ~= rate  and  rate < up_limit  and  rate >= down_limit and step >= 1  ) then
        if (step < 1 and not found ) or (step >= 1 )  then
            return start_traffic(rate);
        end
    end
    sleep(3);
    return down_limit;
end
local out_file = ""
local starting_rate = 100;

pktgen.clr();
print("RFC 2544 THROUGHPUT CALCULATION")

-- Write output on log file
file = io.open(out_file, "w")

-- Start experiment
--rate = rfc2544.start_traffic(starting_rate)
rate = start_traffic(starting_rate)
print("RATE: " .. rate);
file:write(rate);

-- Close the log file
file:close()

-- Quit the environment
os.exit(1);
