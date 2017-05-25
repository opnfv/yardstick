-- This program provides a RFC2544-like testing of network devices, using
-- libaries from the MoonGen packet generator and DPDK.  This program
-- is typically from within a MoonGen source tree, for example:
--
-- cd MoonGen
-- build/MoonGen examples/opnfv-vsperf.lua
--
-- The test will run a binary search to find the maximum packet rate while
-- not exceeding a defined percentage packet loss.
--
-- The test parameters can be adjusted by created a file, opnfv-vsperf-cfg.lua
-- in the current working directory.  The file is lua syntax and describes the
-- test paramters.  For example:
--
-- VSPERF {
--	rate = 5,
--	runBidirec = true,
--	ports = {0,1,2,3}
-- }
--
-- paramters that may be used:
-- testType		Either "throughput" or "latency"
-- ports        	A list of DPDK ports to use, for example {0,1}.  Minimum is 1 pair, and more than 1 pair can be used.
-- 			It is assumed that for each pair, packets transmitted out the first port will arrive on the second port (and the reverse)
-- startRate         	Float: The packet rate in millions/sec to start testing (default is 14.88).
-- runBidirec   	true or false: If true all ports transmit packets (and receive).  If false, only every other port transmits packets.
-- txMethod     	"hardware" or "software": The method to transmit packets (hardware recommended when adapter support is available).
-- nrFlows      	Integer: The number of unique network flows to generate.
-- latencyRunTime 	Integer: The number of seconds to run when doing a latency test.
-- searchRunTime 	Integer: The number of seconds to run when doing binary search for a throughput test.
-- validationRunTime 	Integer: The number of seconds to run when doing final validation for a throughput test.
-- acceptableLossPct	Float: The maximum percentage of packet loss allowed to consider a test as passing.
-- rate_granularity	testParams.rate_granularity or RATE_GRANULARITY
-- txQueuesPerDev	Integer: The number of queues to use when transmitting packets.  The default is 3 and should not need to be changed
-- frameSize		Integer: the size of the Ethernet frame (including CRC)
-- oneShot		true or false: set to true only if you don't want a binary search for maximum packet rate
-- negativeLossRetry	true or false: set to false only if you want to allow negative packet loss attempts to pass
-- loggingLevel		Integer: The minimum level to log, any logging function called with a lower level than the loggingLevel is
--		ignored and no text is outputted or written. Possible values are
--		0=[debug], 1=[info], 2=[warn], 3=[error], 4=[fatal]. Default logging level is 1 (info).


local moongen	= require "moongen"
local dpdk	= require "dpdk"
local memory	= require "memory"
local ts	= require "timestamping"
local device	= require "device"
local filter	= require "filter"
local timer	= require "timer"
local stats	= require "stats"
local hist	= require "histogram"
local log	= require "log"
local ffi	= require "ffi"
-- required here because this script creates *a lot* of mempools
-- memory.enableCache()

local LOGGING_LEVEL = log.INFO
local REPS = 1
local VALIDATION_RUN_TIME = 30
local LATENCY_RUN_TIME = 1800
local SEARCH_RUN_TIME = 60
local LATENCY_TRIM = 3000 -- time in ms to delayied start and early end to latency mseasurement, so we are certain main packet load is present
local FRAME_SIZE = 64
local TEST_TYPE = "throughput" -- "throughput" is for finding max packets/sec while not exceeding MAX_FRAME_LOSS_PCT
			       -- "latency" is for measuring round-trip packet latency while handling testParams.startRate packets/sec
			       -- "throughput-latency" will run a throughput test but also measure latency in the final validation
local TEST_BIDIREC = false -- do not do bidirectional test
local MAX_FRAME_LOSS_PCT = 0
local LINK_SPEED = 10000000000 -- 10Gbps
local RATE_GRANULARITY = 0.1
local TX_HW_RATE_TOLERANCE_MPPS = 0.250  -- The acceptable difference between actual and measured TX rates (in Mpps)
local TX_SW_RATE_TOLERANCE_MPPS = 0.250  -- The acceptable difference between actual and measured TX rates (in Mpps)
local SRC_IP    = "10.0.0.1"
local DST_IP    = "192.168.0.10"
local SRC_PORT  = 1234
local DST_PORT  = 1234
local NR_FLOWS = 256
local TX_QUEUES_PER_DEV = 3
local RX_QUEUES_PER_DEV = 1
local MAX_CALIBRATION_ATTEMPTS = 20
local VLAN_ID = 0
local MPPS_PER_QUEUE = 5
local QUEUES_PER_TASK = 3
local PCI_ID_X710 = 0x80861572
local PCI_ID_XL710 = 0x80861583
local ATTEMPT_FAIL = 0
local ATTEMPT_PASS = 1
local ATTEMPT_RETRY = 2
local MIN_RATE = 0


function macToU48(mac)
	-- this is similar to parseMac, but maintains ordering as represented in the input string
	local bytes = {string.match(mac, '(%x+)[-:](%x+)[-:](%x+)[-:](%x+)[-:](%x+)[-:](%x+)')}
	if bytes == nil then
	return
	end
	for i = 1, 6 do
	if bytes[i] == nil then
			return
		end
		bytes[i] = tonumber(bytes[i], 16)
		if  bytes[i] < 0 or bytes[i] > 0xFF then
			return
		end
	end

	local acc = 0
	for i = 1, 6 do
		acc = acc + bytes[i] * 256 ^ (6 - i)
	end
	return acc
end

function master(...)
	local testParams = getTestParams()
	dumpTestParams(testParams)

	-- set logging level
	log:setLevel(testParams.loggingLevel)

	local finalValidation = false
	local prevRate = 0
	local prevPassRate = 0
	local rateAttempts = {0}
	local maxRateAttempts = 2 -- the number of times we will allow MoonGen to get the Tx rate correct
	local negativeLossAttempts = {0}
	local maxNegativeLossAttempts = 3
	if ( method == "hardware" ) then
		tx_rate_tolerance = TX_HW_RATE_TOLERANCE_MPPS
	else
		tx_rate_tolerance = TX_SW_RATE_TOLERANCE_MPPS
	end
	local txStats = {}
	local rxStats = {}
        local devs = {}
	testParams.rate = getMaxRateMpps(devs, testParams, getLineRateMpps(testParams), testParams.startRate)
	if testParams.startRate and testParams.rate < testParams.startRate then
		log:warn("Start rate has been reduced from %.2f to %.2f because the original start rate could not be achieved.", testParams.startRate, testParams.rate)
	end
	testParams.startRate = testParams.startRate or testParams.rate
	local prevFailRate = testParams.rate

	if testParams.testType == "latency" then 
		printf("Starting latency test", testParams.acceptableLossPct);
		if launchTest(finalValidation, devs, testParams, txStats, rxStats) then
			showReport(rxStats, txStats, testParams, "REPORT")
		else
			log:error("Test failed");
			return
		end
	else
		if testParams.testType == "throughput" or testParams.testType == "throughput-latency" then
			if testParams.oneShot then
				printf("Running single throughput test");
				finalValidation = true
			else
				printf("Starting binary search for maximum throughput with no more than %.8f%% packet loss", testParams.acceptableLossPct);
			end
			while ( math.abs(testParams.rate - prevRate) >= testParams.rate_granularity or finalValidation ) do
				if launchTest(finalValidation, devs, testParams, txStats, rxStats) then
					local acceptableLossResult = acceptableLoss(testParams, rxStats, txStats, maxNegativeLossAttempts, negativeLossAttempts)
					local acceptableRateResult = false
					if acceptableLossResult == ATTEMPT_PASS then
						acceptableRateResult = acceptableRate(tx_rate_tolerance, testParams.rate, txStats, maxRateAttempts, rateAttempts)
					end
					if (acceptableLossResult == ATTEMPT_FAIL) or acceptableRateResult then
						prevRate = testParams.rate
						if testParams.oneShot or (acceptableLossResult == ATTEMPT_PASS) then
							if finalValidation then
								showReport(rxStats, txStats, testParams, "REPORT")
								return
							else
								showReport(rxStats, txStats, testParams, "RESULT")
								nextRate = (prevFailRate + testParams.rate ) / 2
								if math.abs(nextRate - testParams.rate) <= testParams.rate_granularity then
									-- since the rate difference from rate that just passed and the next rate is not greater than rate_granularity, the next run is a "final validation"
									finalValidation = true
								else
									prevPassRate = testParams.rate
									testParams.rate = nextRate
								end
							end
						else
							showReport(rxStats, txStats, testParams, "RESULT")
							if testParams.rate == testParams.minRate then
								log:error("Could not pass minimum specified rate (%f)", testParams.minRate)
								return
							end
							if testParams.rate <= testParams.rate_granularity then
								log:error("Could not even pass with rate <= the rate granularity, %f", testParams.rate_granularity)
								return
							end
							if finalValidation then
								finalValidation = false
								nextRate = testParams.rate - testParams.rate_granularity
							else
								nextRate = (prevPassRate + testParams.rate ) / 2
							end
							if nextRate < testParams.minRate then
								log:info("Setting nextRate to testParams.minRate (%f)", testParams.minRate)
								nextRate = testParams.minRate
							end
							if math.abs(nextRate - testParams.rate) < testParams.rate_granularity then
								-- since the rate difference from the previous *passing* test rate and next rate is not greater than rate_granularity, the next run is a "final validation"
								finalValidation = true
							end
							prevFailRate = testParams.rate
							testParams.rate = nextRate
						end
						if not moongen.running() then
							break
						end
					else
						if rateAttempts[1] > maxRateAttempts then
							return
						end
					end
				else
					log:error("Test failed");
					return
				end
			end
		end
	end
end

function showReport(rxStats, txStats, testParams, mode)
	local totalRxMpps = 0
	local totalTxMpps = 0
	local totalRxFrames = 0
	local totalTxFrames = 0
	local totalLostFrames = 0
	local totalLostFramePct = 0
	local portList = ""
	local count = 0
	for i, v in ipairs(testParams.ports) do
		if count == 0 then
			portList = portList..i
		else
			portList = portList..","..i
		end
		count = count + 1
	end
	if testParams.testType == "throughput" then
		printf("[PARAMETERS] startRate: %f nrFlows: %d frameSize: %d runBidirec: %s searchRunTime: %d validationRunTime: %d acceptableLossPct: %f ports: %s",
			testParams.startRate, testParams.nrFlows, testParams.frameSize, testParams.runBidirec, testParams.searchRunTime, testParams.validationRunTime, testParams.acceptableLossPct, portList) 
	end
	if testParams.testType == "latency" then
		printf("[PARAMETERS] startRate: %f nrFlows: %d frameSize: %d runBidirec: %s latencyRunTime: %d ports: %s",
			testParams.startRate, testParams.nrFlows, testParams.frameSize, testParams.runBidirec, testParams.latencyRunTime, portList) 
	end
	if testParams.testType == "throughput-latency" then
		printf("[PARAMETERS] startRate: %f nrFlows: %d frameSize: %d runBidirec: %s latencyRunTime: %d searchRunTime: %d validationRunTime: %d acceptableLossPct: %f ports: %s",
			testParams.startRate, testParams.nrFlows, testParams.frameSize, testParams.runBidirec, testParams.latencyRunTime, testParams.searchRunTime, testParams.validationRunTime, testParams.acceptableLossPct, portList) 
	end
	for i, v in pairs(txStats) do
		if testParams.connections[i] then
			local lostFrames = txStats[i].totalFrames - rxStats[testParams.connections[i]].totalFrames
			local lostFramePct = 100 * lostFrames / txStats[i].totalFrames
			local rxMpps = txStats[i].avgMpps * (100 - lostFramePct) / 100
			totalRxMpps = totalRxMpps + rxMpps
			totalTxMpps = totalTxMpps + txStats[i].avgMpps
			totalRxFrames = totalRxFrames + rxStats[testParams.connections[i]].totalFrames
			totalTxFrames = totalTxFrames + txStats[i].totalFrames
			totalLostFrames = totalLostFrames + lostFrames
			totalLostFramePct = 100 * totalLostFrames / totalTxFrames
			printf("[%s]Device %d->%d: Tx frames: %d Rx Frames: %d frame loss: %d, %f%% Rx Mpps: %f", mode,
			 testParams.ports[i], testParams.ports[testParams.connections[i]], txStats[i].totalFrames,
			 rxStats[testParams.connections[i]].totalFrames, lostFrames, lostFramePct, rxMpps)
		end
	end
	printf("[%s]      total: Tx frames: %d Rx Frames: %d frame loss: %d, %f%% Tx Mpps: %f Rx Mpps: %f",
	 mode, totalTxFrames, totalRxFrames, totalLostFrames, totalLostFramePct, totalTxMpps, totalRxMpps)
end

function prepareDevs(testParams)
	local devs = {}
	local rxQueues = testParams.rxQueuesPerDev
	local txQueues = testParams.txQueuesPerDev
	if testParams.testType == "latency" or testParams.testType == "throughput-latency" then
		log:info("increasing queue count to accomodate latency testing"); 
		rxQueues = rxQueues + 1
		txQueues = txQueues + 1
	end
	log:info("number of rx queues: %d", rxQueues);
	log:info("number of tx queues: %d", txQueues);

	-- The connections[] table defines a relationship between te device which transmits and a device which receives the same packets.
	-- This relationship is derived via the ports[] table, where if ports contained {a, b, c, d}, device a transmits to device b,
	-- and device c transmits to device d.  
	-- If bidirectional traffic is enabled, the reverse is also true, and device b transmits to device a and d to c.
	testParams.connections = {}
	for i, v in ipairs(testParams.ports) do -- ports = {a, b, c, d}
		if ( i % 2 == 1) then -- for ports a, c
			testParams.connections[i] = i + 1  -- device a transmits to device b, device c transmits to device d 
			log:info("device %d transmits to device %d", testParams.ports[i], testParams.ports[testParams.connections[i]]);
			if testParams.runBidirec then
				testParams.connections[i + 1] = i  -- device b transmits to device a, device d transmits to device c
				log:info("device %d transmits to device %d", testParams.ports[testParams.connections[i]], testParams.ports[i]);
			end
		end
	end

	-- store the src MACs for each device
	if not testParams.srcMacs then
		testParams.srcMacs = {}
	end
	testParams.srcMacsUnsigned = {}
	for i, v in ipairs(testParams.ports) do
		devs[i] = device.config{ port = testParams.ports[i],
				 	rxQueues = rxQueues,
				 	txQueues = txQueues}
		-- by default a source MAC is retrived from the actual device
		-- if a source MAC was already provided for the device (via opnfv-vsperf-cfg.lua), then leave it alone
		if testParams.connections[i] then
			if not testParams.srcMacs[i] then
				testParams.srcMacs[i] = devs[i]:getMacString()
			end
			log:info("device %d src MAC: [%s]", v, testParams.srcMacs[i])
			testParams.srcMacsUnsigned[i] = macToU48(testParams.srcMacs[i])
		end
	end

	-- store the dst MACs for each device
	if not testParams.dstMacs then
		testParams.dstMacs = {}
	end
	testParams.dstMacsUnsigned = {}
	for i, v in ipairs(testParams.ports) do
		-- by default a destination MAC is used by looking at the source MAC in the connections[] table
		-- if a destination MAC was already provided for the device (via opnfv-vsperf-cfg.lua), then leave it alone
		if testParams.connections[i] then
			if not testParams.dstMacs[i] then
				local dstMac = testParams.srcMacs[testParams.connections[i]]
				if dstMac == nil then
					dstMac = devs[testParams.connections[i]]:getMacString()
					log:info("device %d dst MAC, getting from device %d src MAC: [%s]", v, testParams.connections[i], dstMac)
				end
				testParams.dstMacs[i] = dstMac
			end
			log:info("device %d dst MAC: [%s]", v, testParams.dstMacs[i])
			testParams.dstMacsUnsigned[i] = macToU48(testParams.dstMacs[i])
		end
	end

	for i, v in ipairs(testParams.ports) do
			if testParams.vlanIds and testParams.vlanIds[i] then
				log:info("device %d when transmitting will use vlan ID: [%d]", v, testParams.vlanIds[i])
			end
	end

	device.waitForLinks()
	return devs
end

function getTestParams(testParams)
	filename = "opnfv-vsperf-cfg.lua"
	local cfg
	if fileExists(filename) then
		log:info("reading [%s]", filename)
		cfgScript = loadfile(filename)
		setfenv(cfgScript, setmetatable({ VSPERF = function(arg) cfg = arg end }, { __index = _G }))
		local ok, err = pcall(cfgScript)
		if not ok then
			log:error("Could not load DPDK config: " .. err)
			return false
		end
		if not cfg then
			log:error("Config file does not contain VSPERF statement")
			return false
		end
	else
		log:warn("No %s file found, using defaults", filename)
	end

	local testParams = cfg or {}
	testParams.loggingLevel = testParams.loggingLevel or LOGGING_LEVEL
	testParams.frameSize = testParams.frameSize or FRAME_SIZE
	testParams.testType = testParams.testType or TEST_TYPE
	testParams.startRate = testParams.startRate
	testParams.minRate = testParams.minRate or MIN_RATE
	testParams.txMethod = "hardware"
	testParams.runBidirec = testParams.runBidirec or false
	testParams.nrFlows = testParams.nrFlows or NR_FLOWS
	testParams.latencyRunTime = testParams.latencyRunTime or LATENCY_RUN_TIME
	testParams.searchRunTime = testParams.searchRunTime or SEARCH_RUN_TIME
	testParams.validationRunTime = testParams.validationRunTime or VALIDATION_RUN_TIME
	testParams.acceptableLossPct = testParams.acceptableLossPct or MAX_FRAME_LOSS_PCT
	testParams.rate_granularity = testParams.rate_granularity or RATE_GRANULARITY
	testParams.ports = testParams.ports or {0,1}
	testParams.flowMods = testParams.flowMods or {"srcIp"}
	testParams.srcIp = testParams.srcIp or SRC_IP
	testParams.dstIp = testParams.dstIp or DST_IP
	testParams.srcPort = testParams.srcPort or SRC_PORT
	testParams.dstPort = testParams.dstPort or DST_PORT
	testParams.srcMacs = testParams.srcMacs
	testParams.dstMacs = testParams.dstMacs
	testParams.vlanIds = testParams.vlanIds
	testParams.srcIp = parseIPAddress(testParams.srcIp)
	testParams.dstIp = parseIPAddress(testParams.dstIp)
	testParams.oneShot = testParams.oneShot or false
	if testParams.negativeLossRetry == nil then
		testParams.negativeLossRetry = true
	end
	testParams.mppsPerQueue = testParams.mppsPerQueue or MPPS_PER_QUEUE
	testParams.queuesPerTask = testParams.queuesPerTask or QUEUES_PER_TASK
	testParams.rxQueuesPerDev = 1
	testParams.linkSpeed = testParams.linkSpeed or LINK_SPEED

	-- print stats only when debug logging mode is enabled
	testParams.statsFormatter = "nil"
	if testParams.loggingLevel < log.INFO then
		testParams.statsFormatter = "plain"
	end

	return testParams
end

function fileExists(f)
	local file = io.open(f, "r")
	if file then
	file:close()
	end
	return not not file
end

function acceptableLoss(testParams, rxStats, txStats, maxNegativeLossAttempts, t)
	local pass = ATTEMPT_PASS
	local i
	for i, v in pairs(txStats) do
		if testParams.connections[i] then
			for q = 0, testParams.txQueuesPerDev - 1 do
				if q == 0 then
					local lostFrames = txStats[i].totalFrames - rxStats[testParams.connections[i]].totalFrames
					local lostFramePct = 100 * lostFrames / txStats[i].totalFrames
					if (lostFramePct > testParams.acceptableLossPct) then
						log:warn("Device %d->%d: FAILED - frame loss (%d, %.8f%%) is greater than the maximum (%.8f%%)",
				 		testParams.ports[i], testParams.ports[testParams.connections[i]], lostFrames, lostFramePct, testParams.acceptableLossPct);
						pass = ATTEMPT_FAIL
					else
						if testParams.negativeLossRetry and lostFramePct < 0 then
							-- if pass == ATTEMPT_PASS then
							--	pass = ATTEMPT_RETRY
							-- end

							log:warn("Device %d->%d: PASSED with negative frame loss (%d)",
							testParams.ports[i], testParams.ports[testParams.connections[i]], lostFrames);
                                                        rxStats[testParams.connections[i]].totalFrames = txStats[i].totalFrames
						else
							log:info("Device %d->%d: PASSED - frame loss (%d, %.8f%%) is less than or equal to the maximum (%.8f%%)",
							testParams.ports[i], testParams.ports[testParams.connections[i]], lostFrames, lostFramePct, testParams.acceptableLossPct);
						end
					end
				end
			end
		end
	end
	if pass == ATTEMPT_RETRY then
		t[1] = t[1] + 1

		if t[1] > maxNegativeLossAttempts then
			log:warn("Exceeded maximum number of negative packet loss attempts (%d)", maxNegativeLossAttempts)
			pass = ATTEMPT_FAIL
		else
			log:warn("Test Result: RETRY - Attempt #%d", t[1])
		end
	end
	if pass == ATTEMPT_PASS then
		log:info("Test Result: PASSED")
		t[1] = 0
	else
		if pass == ATTEMPT_FAIL then
			log:warn("Test Result: FAILED")
			t[1] = 0
		end
	end
	return pass
end
			
function acceptableRate(tx_rate_tolerance, rate, txStats, maxRateAttempts, t)
	t[1] = t[1] + 1
	for i, v in ipairs(txStats) do
		local rateDiff = math.abs(rate - txStats[i].avgMpps)
		if rateDiff > tx_rate_tolerance then
			if t[1] > maxRateAttempts then
				log:error("ABORT TEST:  difference between actual and requested Tx rate (%.2f) is greater than allowed (%.2f)", rateDiff, tx_rate_tolerance)
				do return end
			else
				log:warn("RETRY TEST: difference between actual and requested Tx rate (%.2f) is greater than allowed (%.2f)", rateDiff, tx_rate_tolerance)
				return false
			end
		end
	end
	-- if every txRate was good, reset attempts counter
	t[1] = 0
	return true
end

function getLineRateMpps(testParams)
	-- TODO: check actual link rate instead of using linkSpeed
	return  (testParams.linkSpeed /(testParams.frameSize*8 +64 +96) /1000000)
end

function calcTxTasks(queues, testParams)
	return math.ceil(queues / testParams.queuesPerTask)
end

function calcTxQueues(rate, testParams)
	return 1 + math.floor(rate / testParams.mppsPerQueue)
end

function getTxQueues(txQueuesPerTask, txQueuesPerDev, taskId, devs, devId)
	local queueIds = {}
	local firstQueueId = taskId * txQueuesPerTask
	local lastQueueId = firstQueueId + txQueuesPerTask - 1
	if lastQueueId > (txQueuesPerDev - 1) then
		lastQueueId = txQueuesPerDev - 1
	end
	for queueId = firstQueueId, lastQueueId do
		table.insert(queueIds, devs[devId]:getTxQueue(queueId))
	end
	return queueIds
end

function getTimerQueues(devs, devId, testParams)
	-- build a table of one or more pairs of queues
	local queueIds = { devs[devId]:getTxQueue(testParams.txQueuesPerDev), devs[testParams.connections[devId]]:getRxQueue(testParams.rxQueuesPerDev) }
	-- If this is a bidirectional test, add another queue-pair for the other direction:
	if testParams.connections[testParams.connections[devId]] then
		table.insert(queueIds, devs[testParams.connections[devId]]:getTxQueue(testParams.txQueuesPerDev))
		table.insert(queueIds, devs[devId]:getRxQueue(testParams.rxQueuesPerDev))
	end
	return queueIds
end

function getMaxRateMpps(devs, testParams, lineRate, rate)
	local qid
	local idx
	local calTasks = {}
	local calStats = {}
	local rxTasks = {}
	local txTasks = {}
	local timerTasks = {}
	local macs = {}
	local runTime = 10

	-- set the number of transmit queues & tasks based on the transmit rate
	testParams.txQueuesPerDev = calcTxQueues(lineRate, testParams)
	log:info("testparams.txQueuesPerDev: %d", testParams.txQueuesPerDev)
	testParams.txTasks = calcTxTasks(testParams.txQueuesPerDev, testParams)
	log:info("testparams.txTasks: %d", testParams.txTasks)
        devs = prepareDevs(testParams)
	-- find the maximum transmit rate
	local perDevCalibratedRate = {}
	local rate_accuracy = TX_HW_RATE_TOLERANCE_MPPS
	for devId, v in ipairs(devs) do
		if testParams.connections[devId] then
			local packetCount = 0
			local measuredRate = 0
			local prevMeasuredRate = 0
			local calibrated = false
			local calibrationCount = 0
			local overcorrection = 1

			if rate then
				calibratedRate = rate
			else
				-- find the maximum rate without setting the rate value (which should be absolute fastest rate possible)
				calibratedRate = 0 -- using 0 will force calibrateSlave to not set a rate
				rate = lineRate
			end
			log:info("Finding maximum Tx Rate",  testParams.txMethod, rate)
			local taskId
			for taskId = 0, testParams.txTasks - 1 do
				local queueIds = getTxQueues(testParams.queuesPerTask, testParams.txQueuesPerDev, taskId, devs, devId)
				calTasks[taskId] = moongen.startTask("calibrateSlave", devs, devId, calibratedRate, testParams, taskId, queueIds)
			end
			-- wait for all jobs to complete
			for taskId = 0, testParams.txTasks - 1 do
				calStats[taskId] = calTasks[taskId]:wait()
			end
			local measuredRate = calStats[0].avgMpps -- only the first queue provides the measured rate [for all queues]
			log:info("Max Tx rate: %.2f",  measuredRate)
			if measuredRate < rate then
				rate = measuredRate
			end

			-- next try to achieve the maximum rate by using a calibrated rate value
			testParams.rate = rate
			calibratedRate = rate
			testParams.txQueuesPerDev = calcTxQueues(testParams.rate, testParams)
			log:info("testparams.txQueuesPerDev: %d", testParams.txQueuesPerDev)
			testParams.txTasks = calcTxTasks(testParams.txQueuesPerDev, testParams)
			log:info("testparams.txTasks: %d", testParams.txTasks)
			repeat
				for taskId = 0, testParams.txTasks - 1 do
					local queueIds = getTxQueues(testParams.queuesPerTask, testParams.txQueuesPerDev, taskId, devs, devId)
					calTasks[taskId] = moongen.startTask("calibrateSlave", devs, devId, calibratedRate, testParams, taskId, queueIds)
				end
				-- wait for all jobs to complete
				for taskId = 0, testParams.txTasks - 1 do
					calStats[taskId] = calTasks[taskId]:wait()
				end
				local measuredRate = calStats[0].avgMpps -- only the first queue provides the measured rate [for all queues]
				-- the measured rate must be within the tolerance window but also not exceed the desired rate
				if ( measuredRate > testParams.rate or (testParams.rate - measuredRate) > rate_accuracy ) then
					local correction_ratio = testParams.rate/measuredRate
					-- ensure a minimum amount of change in rate
					if (correction_ratio < 1 and correction_ratio > 0.99 ) then
						correction_ratio = 0.99
					end
					if (correction_ratio > 1 and correction_ratio < 1.01 ) then
						correction_ratio = 1.01
					end
					calibratedRate = calibratedRate * correction_ratio
						prevMeasuredRate = measuredRate
                        		log:info("measuredRate: %.4f  desiredRate:%.4f  new correction_ratio: %.4f  new calibratedRate: %.4f ",
			 		measuredRate, testParams.rate, correction_ratio, calibratedRate)
				else
					calibrated = true
					end
				calibrationCount = calibrationCount + 1
			until ( calibrated or calibrationCount > MAX_CALIBRATION_ATTEMPTS )
			if calibrated then
				return rate
			else
				log:error("Maximum tx rate reduced to %.2f", measuredRate) 
				return measuredRate
			end
		end
	end
end
			
function launchTest(final, devs, testParams, txStats, rxStats)
	local qid
	local idx
	local calTasks = {}
	local calStats = {}
	local rxTasks = {}
	local txTasks = {}
	local timerTasks = {}
	local macs = {}
	local runTime

	if testParams.testType == "throughput" or testParams.testType == "throughput-latency" then
		if final then
			runTime = testParams.validationRunTime
		else
			runTime = testParams.searchRunTime
		end
	else
		if testParams.testType == "latency" then
			runTime = testParams.latencyRunTime
		end
	end
	-- set the number of transmit queues & tasks based on the transmit rate
	testParams.txQueuesPerDev = calcTxQueues(testParams.rate, testParams)
	log:info("testparams.txQueuesPerDev: %d", testParams.txQueuesPerDev)
	testParams.txTasks = calcTxTasks(testParams.txQueuesPerDev, testParams)
	log:info("testparams.txTasks: %d", testParams.txTasks)
        devs = prepareDevs(testParams)
	-- calibrate transmit rate
	local calibratedRate = testParams.rate
	local perDevCalibratedRate = {}
	local rate_accuracy = TX_HW_RATE_TOLERANCE_MPPS
	for devId, v in ipairs(devs) do
		if testParams.connections[devId] then
			local packetCount = 0
			local measuredRate = 0
			local prevMeasuredRate = 0
			local calibrated = false
			local calibrationCount = 0
			local overcorrection = 1
			log:info("Starting transmit rate calibration for device %d", testParams.ports[devId])
			repeat
				local taskId
				-- launch a process to transmit packets per queue
				for taskId = 0, testParams.txTasks - 1 do
					local queueIds = getTxQueues(testParams.queuesPerTask, testParams.txQueuesPerDev, taskId, devs, devId)
					calTasks[taskId] = moongen.startTask("calibrateSlave", devs, devId, calibratedRate, testParams, taskId, queueIds)
				end
				-- wait for all jobs to complete
				for taskId = 0, testParams.txTasks - 1 do
					calStats[taskId] = calTasks[taskId]:wait()
				end
				local measuredRate = calStats[0].avgMpps -- only the first queue provides the measured rate [for all queues]
				-- the measured rate must be within the tolerance window but also not exceed the desired rate
				if ( measuredRate > testParams.rate or (testParams.rate - measuredRate) > rate_accuracy ) then
					local correction_ratio = testParams.rate/measuredRate
					-- ensure a minimum amount of change in rate
					if (correction_ratio < 1 and correction_ratio > 0.99 ) then
						correction_ratio = 0.99
					end
					if (correction_ratio > 1 and correction_ratio < 1.01 ) then
						correction_ratio = 1.01
					end
					calibratedRate = calibratedRate * correction_ratio
						prevMeasuredRate = measuredRate
                        		log:info("Device %d measuredRate: %.4f  desiredRate:%.4f  new correction_ratio: %.4f  new calibratedRate: %.4f ",
			 		testParams.connections[devId], measuredRate, testParams.rate, correction_ratio, calibratedRate)
				else
					calibrated = true
					end
				calibrationCount = calibrationCount + 1
			until ( calibrated or calibrationCount > MAX_CALIBRATION_ATTEMPTS )
			if calibrated then
				perDevCalibratedRate[devId] = calibratedRate
				log:info("Device %d rate calibration complete", testParams.ports[devId]) 
			else
				log:error("Device %d could not achive Tx packet rate", testParams.ports[devId]) 
				return
			end
		end
	end
	-- start devices which receive
	for devId, v in ipairs(devs) do
		if testParams.connections[devId] then
			log:info("Starting receiving for device %d", testParams.ports[devId])
			rxTasks[devId] = moongen.startTask("counterSlave", devs[testParams.connections[devId]]:getRxQueue(0), runTime, testParams)
		end
	end
	moongen.sleepMillis(3000)
	if final then
		log:info("Starting final validation");
	end
	-- start devices which transmit
	idx = 1
	local txTaskId = 1
	for devId, v in ipairs(devs) do
		if testParams.connections[devId] then
			printf("Testing %.2f Mfps", testParams.rate)
			--for q = 0, testParams.txQueuesPerDev - 1 do
			for perDevTaskId = 0, testParams.txTasks - 1 do
				--log:info("calibrateSlave: devId: %d  taskId: %d  perDevTaskId: %d", devId, txTaskId, perDevTaskId)
				local queueIds = getTxQueues(testParams.queuesPerTask, testParams.txQueuesPerDev, perDevTaskId, devs, devId)
				txTasks[txTaskId] = moongen.startTask("loadSlave", devs, devId, perDevCalibratedRate[devId], runTime, testParams, perDevTaskId, queueIds)
				txTaskId = txTaskId + 1
			end
			if testParams.testType == "latency" or
				( testParams.testType == "throughput-latency" and final ) then
				-- latency measurements do not involve a dedicated task for each direction of traffic
				if not timerTasks[testParams.connections[devId]] then
					local queueIds = getTimerQueues(devs, devId, testParams)
					log:info("timer queues: %s", dumpQueues(queueIds))
					timerTasks[devId] = moongen.startTask("timerSlave", runTime, testParams, queueIds)
				end
			end
		end
	end
	-- wait for transmit devices to finish
	local txTaskId = 1
	for devId, v in ipairs(devs) do
		if testParams.connections[devId] then
			for perDevTaskId = 0, testParams.txTasks - 1 do
				if perDevTaskId == 0 then
					txStats[devId] = txTasks[txTaskId]:wait()
				else
					txTasks[txTaskId]:wait()
				end
				txTaskId = txTaskId + 1
			end
		end
	end

	if final then
		log:info("Stopping final validation");
	end
	-- moongen.sleepMillis(3000)
	-- wait for receive devices to finish
	for devId, v in ipairs(devs) do
		if testParams.connections[devId] then
			rxStats[testParams.connections[devId]] = rxTasks[devId]:wait()
		end
		if testParams.testType == "latency" or
			( testParams.testType == "throughput-latency" and final ) then
			if timerTasks[devId] then
				timerTasks[devId]:wait()
			end
		end
	end
	return true
end

function adjustHeaders(devId, bufs, packetCount, testParams)
	for _, buf in ipairs(bufs) do
		local pkt = buf:getUdpPacket()
		local ethernetPacket = buf:getEthernetPacket()
		local flowId = packetCount % testParams.nrFlows

		for _,v in ipairs(testParams.flowMods) do

			if ( v == "srcPort" ) then
				pkt.udp:setSrcPort((testParams.srcPort + flowId) % 65536)
			end
	
			if ( v == "dstPort" ) then
				pkt.udp:setDstPort((testParams.srcPort + flowId) % 65536)
			end
	
			if ( v == "srcIp" ) then
				pkt.ip4.src:set(testParams.srcIp + flowId)
			end
	
			if ( v == "dstIp" ) then
				pkt.ip4.dst:set(testParams.dstIp + flowId)
			end
	
			if ( v == "srcMac" ) then
				local addr = testParams.srcMacsUnsigned[devId] + flowId
				ethernetPacket.eth.src.uint8[5] = bit.band(addr, 0xFF)
				ethernetPacket.eth.src.uint8[4] = bit.band(bit.rshift(addr, 8), 0xFF)
				ethernetPacket.eth.src.uint8[3] = bit.band(bit.rshift(addr, 16), 0xFF)
				ethernetPacket.eth.src.uint8[2] = bit.band(bit.rshift(addr, 24), 0xFF)
				ethernetPacket.eth.src.uint8[1] = bit.band(bit.rshift(addr + 0ULL, 32ULL), 0xFF)
				ethernetPacket.eth.src.uint8[0] = bit.band(bit.rshift(addr + 0ULL, 40ULL), 0xFF)
			end
	
			if ( v == "dstMac" ) then
				local addr = testParams.dstMacsUnsigned[devId] + flowId
				ethernetPacket.eth.dst.uint8[5] = bit.band(addr, 0xFF)
				ethernetPacket.eth.dst.uint8[4] = bit.band(bit.rshift(addr, 8), 0xFF)
				ethernetPacket.eth.dst.uint8[3] = bit.band(bit.rshift(addr, 16), 0xFF)
				ethernetPacket.eth.dst.uint8[2] = bit.band(bit.rshift(addr, 24), 0xFF)
				ethernetPacket.eth.dst.uint8[1] = bit.band(bit.rshift(addr + 0ULL, 32ULL), 0xFF)
				ethernetPacket.eth.dst.uint8[0] = bit.band(bit.rshift(addr + 0ULL, 40ULL), 0xFF)
			end
		end

		packetCount = packetCount + 1
	end
	return packetCount
end

function getBuffers(devId, testParams)
	local mem = memory.createMemPool(function(buf)
		local eth_dst
		buf:getUdpPacket():fill{
			pktLength = frame_size_without_crc, -- this sets all length headers fields in all used protocols
			ethSrc = testParams.srcMacs[devId],
			ethDst = testParams.dstMacs[devId],
			ip4Dst = testParams.dstIp,
			udpSrc = testParams.srcPort,
			udpDst = testParams.dstPort
		}
	end)
	local bufs = mem:bufArray()
	return bufs
end

function dumpQueues(queueIds)
	local queues = ""
	for _ , queueId in pairs(queueIds)  do
		queues = queues..queueId:__tostring()
	end
	return queues
end

function dumpTable(table, indent)
	local indentString = ""

	for i=1,indent,1 do
		indentString = indentString.."\t"
	end

	for key,value in pairs(table) do
		if type(value) == "table" then
			log:info("%s%s => {", indentString, key)
			dumpTable(value, indent+1)
			log:info("%s}", indentString)
		else
			log:info("%s%s: %s", indentString, key, value)
		end
	end
end

function dumpTestParams(testParams)
	log:info("testParams => {")
	dumpTable(testParams, 1)
	log:info("}")
end

function calibrateSlave(devs, devId, calibratedRate, testParams, taskId, queueIds)
	local dev = devs[devId]
	local frame_size_without_crc = testParams.frameSize - 4
	local bufs = getBuffers(devId, testParams)
	local packetCount = 0
	local overcorrection = 1
	local id = dev:getPciId()
	log:info("calibrateSlave: devId: %d  taskId: %d  calibratedRate: %.4f queues: %s", devId, taskId, calibratedRate, dumpQueues(queueIds))
	-- only the first process tracks stats for the device
	if taskId == 0 then
		txStats = stats:newDevTxCounter(dev, testParams.statsFormatter)
	end
	if ( testParams.txMethod == "hardware"  and calibratedRate > 0 ) then
        	if id == PCI_ID_X710 or id == PCI_ID_XL710 then
                	dev:setRate(calibratedRate * (testParams.frameSize + 4) * 8)
		else
			local queueId
			for _ , queueId in pairs(queueIds)  do
				queueId:setRateMpps(calibratedRate / testParams.txQueuesPerDev, testParams.frameSize)
			end
		end
		runtime = timer:new(5)
	else
		-- s/w rate seems to be less consistent, so test over longer time period
		runtime = timer:new(10)
	end
	while runtime:running() and moongen.running() do
		bufs:alloc(frame_size_without_crc)
		packetCount = adjustHeaders(devId, bufs, packetCount, testParams, srcMacs, dstMacs)
		if (testParams.vlanIds and testParams.vlanIds[devId]) then
			bufs:setVlans(testParams.vlanIds[devId])
		end
               	bufs:offloadUdpChecksums()
		if ( testParams.txMethod == "hardware" ) then
			local queueId
			for _ , queueId in pairs(queueIds)  do
				queueId:send(bufs)
			end
		else
			if calibratedRate > 0 then
				for _, buf in ipairs(bufs) do
					buf:setRate(calibratedRate)
				end
			end
			local queueId
			for _ , queueId in pairs(queueIds)  do
				queueId:sendWithDelay(bufs)
			end
		end
		if taskId == 0 then
			txStats:update(0.5, false)
		end
	end
	local results = {}
	if taskId == 0 then
		txStats:finalize()
		results.avgMpps = txStats.mpps.avg
	end
        return results
end

function counterSlave(rxQueue, runTime, testParams)
	local rxStats = stats:newDevRxCounter(rxQueue, testParams.statsFormatter)
	if runTime > 0 then
		-- Rx runs a bit longer than Tx to ensure all packets are received
		runTimer = timer:new(runTime + 6)
	end
	while (runTime == 0 or runTimer:running()) and moongen.running() do
		rxStats:update(0.5)
	end
        rxStats:finalize()
	local results = {}
        results.totalFrames = rxStats.total
        return results
end

function loadSlave(devs, devId, calibratedRate, runTime, testParams, taskId, queueIds)
	local dev = devs[devId]
	local frame_size_without_crc = testParams.frameSize - 4
	local bufs = getBuffers(devId, testParams)
	log:info("loadSlave: devId: %d  taskId: %d  calibratedRate: %.4f queues: %s", devId, taskId, calibratedRate, dumpQueues(queueIds))
	if runTime > 0 then
		runtime = timer:new(runTime)
		log:info("loadSlave test to run for %d seconds", runTime)
	else
		log:warn("loadSlave runTime is 0")
	end
	
	if taskId == 0 then
		txStats = stats:newDevTxCounter(dev, testParams.statsFormatter)
	end
	local count = 0
	local pci_id = dev:getPciId()
	if ( testParams.txMethod == "hardware" ) then
        	if pci_id == PCI_ID_X710 or pci_id == PCI_ID_XL710 then
                	dev:setRate(calibratedRate * (testParams.frameSize + 4) * 8)
		else
			local queueId
			for _ , queueId in pairs(queueIds)  do
				queueId:setRateMpps(calibratedRate / testParams.txQueuesPerDev, testParams.frameSize)
			end
		end
	end
	local packetCount = 0
	while (runTime == 0 or runtime:running()) and moongen.running() do
		bufs:alloc(frame_size_without_crc)
		packetCount = adjustHeaders(devId, bufs, packetCount, testParams, srcMacs, dstMacs)
		if (testParams.vlanIds and testParams.vlanIds[devId]) then
			bufs:setVlans(testParams.vlanIds[devId])
		end
                bufs:offloadUdpChecksums()
		if ( testParams.txMethod == "hardware" ) then
			local queueId
			for _ , queueId in pairs(queueIds)  do
				queueId:send(bufs)
			end
		else
			for _, buf in ipairs(bufs) do
				buf:setRate(calibratedRate)
			end
			local queueId
			for _ , queueId in pairs(queueIds)  do
				queueId:sendWithDelay(bufs)
			end
		end
		if taskId == 0 then
			txStats:update(0.5, false)
		end
	end
        local results = {}
	if taskId == 0 then
		txStats:finalize()
		results.totalFrames = txStats.total
		results.avgMpps = txStats.mpps.avg
	end
        return results
end

function saveSampleLog(file, samples, counter, label)
	log:info("Saving sample log to '%s'", file)
	file = io.open(file, "w+")
	file:write("samples,", label, "\n")
	for i=1,counter do
		file:write(i, ",", samples[i], "\n")
	end
	file:close()
end

function saveHistogram(file, hist, label)
	output = io.open(file, "w")
	output:write("bucket,", label, "\n")
	hist:save(output)
	output:close()
end

function timerSlave(runTime, testParams, queueIds)
	local hist1, hist2, haveHisto1, haveHisto2, timestamper1, timestamper2
	local transactionsPerDirection = 1 -- the number of transactions before switching direction
	local frameSizeWithoutCrc = testParams.frameSize - 4
	local samplesPerSecond = 1000
	local rateLimit = timer:new(1/samplesPerSecond) -- overhead will result in a lower than requested rate
	local sampleLogElements = samplesPerSecond * runTime
	if testParams.runBidirec then
		sampleLogElements = sampleLogElements / 2
	end
	log:info("Latency test sample log size is %d", sampleLogElements)
	local sampleLog1 = ffi.new("float[?]", sampleLogElements)
	local sampleLog2

	-- TODO: adjust headers for flows

	if testParams.runBidirec then
		log:info("timerSlave: bidirectional testing from %d->%d and %d->%d", queueIds[1].id, queueIds[2].id, queueIds[3].id, queueIds[4].id)
	else
		log:info("timerSlave: unidirectional testing from %d->%d", queueIds[1].id, queueIds[2].id)
	end
	
	hist1 = hist()
	if testParams.frameSize < 76 then
		log:warn("Latency packets are not UDP due to requested size (%d) less than minimum UDP size (76)", testParams.frameSize)
		timestamper1 = ts:newTimestamper(queueIds[1], queueIds[2])
	else
		timestamper1 = ts:newUdpTimestamper(queueIds[1], queueIds[2])
	end
	if testParams.runBidirec then
		if testParams.frameSize < 76 then
			timestamper2 = ts:newTimestamper(queueIds[3], queueIds[4])
		else
			timestamper2 = ts:newUdpTimestamper(queueIds[3], queueIds[4])
		end
		hist2 = hist()
		sampleLog2 = ffi.new("float[?]", sampleLogElements)
	end
	-- timestamping starts after and finishes before the main packet load starts/finishes
	moongen.sleepMillis(LATENCY_TRIM)
	if runTime > 0 then
		local actualRunTime = runTime - LATENCY_TRIM/1000*2
		runTimer = timer:new(actualRunTime)
		log:info("Latency test to run for %d seconds", actualRunTime)
	else
		log:warn("Latency runTime is 0")
	end
	local timestamper = timestamper1
	local hist = hist1
	local sampleLog = sampleLog1
	local haveHisto = false
	local haveHisto1 = false
	local haveHisto2 = false
	local counter = 0
	local counter1 = 0
	local counter2 = 0
	while (runTime == 0 or runTimer:running()) and moongen.running() do
		for count = 0, transactionsPerDirection - 1 do -- inner loop tests in one direction
			rateLimit:wait()
			counter = counter + 1
			local lat = timestamper:measureLatency(testParams.frameSize, nil, 1000);
			if (lat) then
				haveHisto = true;
                		hist:update(lat)
				sampleLog[counter] = lat
			else
				sampleLog[counter] = -1
			end
			rateLimit:reset()
		end
		if testParams.runBidirec then
			if timestamper == timestamper2 then
				timestamper = timestamper1
				hist = hist1
				sampleLog = sampleLog1
				haveHisto2 = haveHisto
				haveHisto = haveHisto1
				counter2 = counter
				counter = counter1
			else
				timestamper = timestamper2
				hist = hist2
				sampleLog = sampleLog2
				haveHisto1 = haveHisto
				haveHisto = haveHisto2
				counter1 = counter
				counter = counter2
			end
		else
			haveHisto1 = haveHisto
			counter1 = counter
		end
	end
	moongen.sleepMillis(LATENCY_TRIM + 1000) -- the extra 1000 ms ensures the stats are output after the throughput stats
	local histDesc = "Histogram port " .. ("%d"):format(queueIds[1].id) .. " to port " .. ("%d"):format(queueIds[2].id) .. " at rate " .. testParams.rate .. " Mpps"
	local histFile = "dev:" .. ("%d"):format(queueIds[1].id) .. "-" .. ("%d"):format(queueIds[2].id) .. "_rate:" .. testParams.rate .. ".csv"
	local headerLabel = "Dev:" .. ("%d"):format(queueIds[1].id) .. "->" .. ("%d"):format(queueIds[2].id) .. " @ " .. testParams.rate .. " Mpps"
	if haveHisto1 then
		hist1:print(histDesc)
		saveHistogram("latency:histogram_" .. histFile, hist1, headerLabel)
		local hist_size = hist1:totals()
		if hist_size ~= counter1 then
		   log:warn("[%s] Lost %d samples (%.2f%%)!", histDesc, counter1 - hist_size, (counter1 - hist_size)/counter1*100)
		end
		saveSampleLog("latency:samples_" .. histFile, sampleLog1, counter1, headerLabel)
	else
		log:warn("no latency samples found for %s", histDesc)
	end
	if testParams.runBidirec then
		local histDesc = "Histogram port " .. ("%d"):format(queueIds[3].id) .. " to port " .. ("%d"):format(queueIds[4].id) .. " at rate " .. testParams.rate .. " Mpps"
		local histFile = "dev:" .. ("%d"):format(queueIds[3].id) .. "-" .. ("%d"):format(queueIds[4].id) .. "_rate:" .. testParams.rate .. ".csv"
		local headerLabel = "Dev:" .. ("%d"):format(queueIds[3].id) .. "->" .. ("%d"):format(queueIds[4].id) .. " @ " .. testParams.rate .. " Mpps"
		if haveHisto2 then
			hist2:print(histDesc)
			saveHistogram("latency:histogram_" .. histFile, hist2, headerLabel)
			local hist_size = hist2:totals()
			if hist_size ~= counter2 then
			   log:warn("[%s] Lost %d samples (%.2f%%)!", histDesc, counter2 - hist_size, (counter2 - hist_size)/counter2*100) 
			end
			saveSampleLog("latency:samples_" .. histFile, sampleLog2, counter2, headerLabel)
		else
			log:warn("no latency samples found for %s", histDesc)
		end
	end
end
