# Copyright 2016-2017 Spirent Communications.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=invalid-name
'''
@author Spirent Communications

This test automates the RFC2889 tests using the Spirent
TestCenter REST APIs. This test supports Python 3.4

'''
import argparse
import logging
import os

# Logger Configuration
logger = logging.getLogger(__name__)


def create_dir(path):
    """Create the directory as specified in path """
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as e:
            logger.error("Failed to create directory %s: %s", path, str(e))
            raise


def write_query_results_to_csv(results_path, csv_results_file_prefix,
                               query_results):
    """ Write the results of the query to the CSV """
    create_dir(results_path)
    filec = os.path.join(results_path, csv_results_file_prefix + ".csv")
    with open(filec, "wb") as f:
        f.write(query_results["Columns"].replace(" ", ",") + "\n")
        for row in (query_results["Output"].replace("} {", ",").
                    replace("{", "").replace("}", "").split(",")):
            f.write(row.replace(" ", ",") + "\n")


def positive_int(value):
    """ Positive Integer type for Arguments """
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            "%s is an invalid positive int value" % value)
    return ivalue


def percent_float(value):
    """ Floating type for Arguments """
    pvalue = float(value)
    if pvalue < 0.0 or pvalue > 100.0:
        raise argparse.ArgumentTypeError(
            "%s not in range [0.0, 100.0]" % pvalue)
    return pvalue

# pylint: disable=too-many-statements
def main():
    """ Read the arguments, Invoke Test and Return the results"""
    parser = argparse.ArgumentParser()
    # Required parameters
    required_named = parser.add_argument_group("required named arguments")
    required_named.add_argument("--lab_server_addr",
                                required=True,
                                help=("The IP address of the "
                                      "Spirent Lab Server"),
                                dest="lab_server_addr")
    required_named.add_argument("--license_server_addr",
                                required=True,
                                help=("The IP address of the Spirent "
                                      "License Server"),
                                dest="license_server_addr")
    required_named.add_argument("--location_list",
                                required=True,
                                help=("A comma-delimited list of test port "
                                      "locations"),
                                dest="location_list")
    # Optional parameters
    optional_named = parser.add_argument_group("optional named arguments")
    optional_named.add_argument("--metric",
                                required=False,
                                help=("One among - Forwarding,\
                                      Address Caching and Learning"),
                                choices=["forwarding", "caching",
                                         "learning"],
                                default="forwarding",
                                dest="metric")
    optional_named.add_argument("--test_session_name",
                                required=False,
                                default="Rfc2889Ses",
                                help=("The friendly name to identify "
                                      "the Spirent Lab Server test session"),
                                dest="test_session_name")
    optional_named.add_argument("--test_user_name",
                                required=False,
                                default="Rfc2889Usr",
                                help=("The friendly name to identify the "
                                      "Spirent Lab Server test user"),
                                dest="test_user_name")
    optional_named.add_argument("--results_dir",
                                required=False,
                                default="./Results",
                                help="The directory to copy results to",
                                dest="results_dir")
    optional_named.add_argument("--csv_results_file_prefix",
                                required=False,
                                default="Rfc2889MaxFor",
                                help="The prefix for the CSV results files",
                                dest="csv_results_file_prefix")
    optional_named.add_argument("--num_trials",
                                type=positive_int,
                                required=False,
                                default=1,
                                help=("The number of trials to execute during "
                                      "the test"),
                                dest="num_trials")
    optional_named.add_argument("--trial_duration_sec",
                                type=positive_int,
                                required=False,
                                default=60,
                                help=("The duration of each trial executed "
                                      "during the test"),
                                dest="trial_duration_sec")
    optional_named.add_argument("--traffic_pattern",
                                required=False,
                                choices=["BACKBONE", "MESH", "PAIR"],
                                default="MESH",
                                help="The traffic pattern between endpoints",
                                dest="traffic_pattern")
    optional_named.add_argument("--frame_size_list",
                                type=lambda s: [int(item)
                                                for item in s.split(',')],
                                required=False,
                                default=[256],
                                help="A comma-delimited list of frame sizes",
                                dest="frame_size_list")
    optional_named.add_argument("--min_learning_rate",
                                type=positive_int,
                                required=False,
                                default=1488,
                                help="Lowest learning rate for test",
                                dest="min_learning_rate")
    optional_named.add_argument("--max_learning_rate",
                                type=positive_int,
                                required=False,
                                default=14880,
                                help="Highest learning rate for test",
                                dest="max_learning_rate")
    optional_named.add_argument("--min_num_addrs",
                                type=positive_int,
                                required=False,
                                default=1,
                                help="lowest number of addrs sent to DUT",
                                dest="min_num_addrs")
    optional_named.add_argument("--max_num_addrs",
                                type=positive_int,
                                required=False,
                                default=1000,
                                help="Highest number of addrs sent to DUT",
                                dest="max_num_addrs")
    optional_named.add_argument("--ac_learning_rate",
                                type=positive_int,
                                required=False,
                                default=1000,
                                help="Number of learning frames per sec",
                                dest="ac_learning_rate")
    optional_named.add_argument("--frame_size",
                                type=positive_int,
                                required=False,
                                default=64,
                                help="Frame size for address test",
                                dest="frame_size")
    parser.add_argument("-v",
                        "--verbose",
                        required=False,
                        default=True,
                        help="More output during operation when present",
                        action="store_true",
                        dest="verbose")
    args = parser.parse_args()

    if args.verbose:
        logger.debug("Creating results directory")
    create_dir(args.results_dir)
    locationList = [str(item) for item in args.location_list.split(',')]

    session_name = args.test_session_name
    user_name = args.test_user_name

    # pylint: disable=import-error
    try:
        # Load Spirent REST Library
        from stcrestclient import stchttp

        stc = stchttp.StcHttp(args.lab_server_addr)
        session_id = stc.new_session(user_name, session_name)
        stc.join_session(session_id)
    except RuntimeError as e:
        logger.error(e)
        raise

    # Retrieve and display the server information
    if args.verbose:
        logger.debug("SpirentTestCenter system version: %s",
                     stc.get("system1", "version"))

    try:
        if args.verbose:
            logger.debug("Bring up license server")
        license_mgr = stc.get("system1", "children-licenseservermanager")
        if args.verbose:
            logger.debug("license_mgr = %s", license_mgr)
        stc.create("LicenseServer", under=license_mgr, attributes={
            "server": args.license_server_addr})

        # Create the root project object
        if args.verbose:
            logger.debug("Creating project ...")
        project = stc.get("System1", "children-Project")

        # Create ports
        if args.verbose:
            logger.debug("Creating ports ...")

        for location in locationList:
            stc.perform("CreateAndReservePorts", params={"locationList":
                                                         location,
                                                         "RevokeOwner":
                                                         "FALSE"})

        port_list_get = stc.get("System1.project", "children-port")

        if args.verbose:
            logger.debug("Adding Host Gen PArams")
        gen_params = stc.create("EmulatedDeviceGenParams",
                                under=project,
                                attributes={"Port": port_list_get})

        # Create the DeviceGenEthIIIfParams object
        stc.create("DeviceGenEthIIIfParams",
                   under=gen_params)
        # Configuring Ipv4 interfaces
        stc.create("DeviceGenIpv4IfParams",
                   under=gen_params)

        stc.perform("DeviceGenConfigExpand",
                    params={"DeleteExisting": "No",
                            "GenParams": gen_params})

        if args.verbose:
            logger.debug("Set up the RFC2889 test...")

        if args.metric == "learning":
            stc.perform("Rfc2889SetupAddressLearningRateTestCommand",
                        params={"FrameSize": args.frame_size,
                                "MinLearningRate": args.min_learning_rate,
                                "MaxLearningRate": args.max_learning_rate,
                                "NumOfTrials": args.num_trials})
        elif args.metric == "caching":
            stc.perform("Rfc2889SetupAddressCachingCapacityTestCommand",
                        params={"FrameSize": args.frame_size,
                                "MinNumAddrs": args.min_num_addrs,
                                "MaxNumAddrs": args.max_num_addrs,
                                "LearningRate": args.ac_learning_rate,
                                "NumOfTrials": args.num_trials})
        else:
            stc.perform("Rfc2889SetupMaxForwardingRateTestCommand",
                        params={"Duration": args.trial_duration_sec,
                                "FrameSizeList": args.frame_size_list,
                                "NumOfTrials": args.num_trials,
                                "TrafficPattern": args.traffic_pattern})

        # Save the configuration
        stc.perform("SaveToTcc", params={"Filename": "2889.tcc"})
        # Connect to the hardware...
        stc.perform("AttachPorts", params={"portList": stc.get(
            "system1.project", "children-port"), "autoConnect": "TRUE"})
        # Apply configuration.
        if args.verbose:
            logger.debug("Apply configuration...")
        stc.apply()

        if args.verbose:
            logger.debug("Starting the sequencer...")
        stc.perform("SequencerStart")

        # Wait for sequencer to finish
        logger.info(
            "Starting test... Please wait for the test to complete...")
        stc.wait_until_complete()
        logger.info("The test has completed... Saving results...")

        # Determine what the results database filename is...
        lab_server_resultsdb = stc.get(
            "system1.project.TestResultSetting", "CurrentResultFileName")

        if args.verbose:
            logger.debug("The lab server results database is %s",
                         lab_server_resultsdb)

        if args.metric == "learning":
            resultsdict = (
                stc.perform("QueryResult",
                            params={
                                "DatabaseConnectionString":
                                lab_server_resultsdb,
                                "ResultPath":
                                ("RFC2889AddressLearningRateTestResultDetailed"
                                 "SummaryView")}))
        elif args.metric == "caching":
            resultsdict = (
                stc.perform("QueryResult",
                            params={
                                "DatabaseConnectionString":
                                lab_server_resultsdb,
                                "ResultPath":
                                ("RFC2889AddressCachingCapacityTestResult"
                                 "DetailedSummaryView")}))
        else:
            resultsdict = (
                stc.perform("QueryResult",
                            params={
                                "DatabaseConnectionString":
                                lab_server_resultsdb,
                                "ResultPath":
                                ("RFC2889MaxForwardingRateTestResultDetailed"
                                 "SummaryView")}))

        if args.verbose:
            logger.debug("resultsdict[\"Columns\"]: %s",
                         resultsdict["Columns"])
            logger.debug("resultsdict[\"Output\"]: %s", resultsdict["Output"])
            logger.debug("Result paths: %s",
                         stc.perform("GetTestResultSettingPaths"))

        # Write results to csv
        if args.verbose:
            logger.debug("Writing CSV file to results directory %s",
                         args.results_dir)
        write_query_results_to_csv(
            args.results_dir, args.csv_results_file_prefix, resultsdict)

    except RuntimeError as err:
        logger.error(err)

    if args.verbose:
        logger.debug("Destroy session on lab server")

    stc.end_session()

    logger.info("Test complete!")

if __name__ == "__main__":
    main()
