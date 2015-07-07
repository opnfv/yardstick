##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import multiprocessing
import json
import logging

log = logging.getLogger(__name__)


class OutputMgr(object):
    '''
    Class with static methods for managing output to data streams.

    Data for output should be sent through OutputMgr.write(data), where
    data is a dictionary mapping descriptors to values.
    '''
    queue = None
    dump_process = None
    mode = "ONE_FILE"

    output_descriptors = multiprocessing.Manager().dict()
    output_filename = ""

    # NOTE: any changes need to happen before starting sub-process,
    # since it is not synced across multiple threads
    separator = ',\n\t'

    '''maps text strings to functions intended to
    hold the behaviour for a situation
    (like the completion of a loop)
    under the current context and mode
    '''
    _functions = {'_ALL_DONE_': None}

    @staticmethod
    def write(object):
        '''
        Takes a dictionary to print to the decided output destination
        Requires that the class has received a valid init() call
        '''
        if OutputMgr.queue is None:
            log.debug("FATAL: Tried to print to nonexistent output queue")
        OutputMgr.queue.put(object)

    @staticmethod
    def _output_serializer_streamer(target, queue):
        '''entrypoint for the singleton subprocess writing to outfile
        Use of this process enables multiple instances of a scenario without
        messing up the output file.
        '''
        OutputMgr._functions['_INIT_DUMP_']()
        # TODO change to general target statement
        with open(target, 'w') as outfile:
            log.debug('Initialised listener process.')
            log.debug('Write target is '+target)
            separate = False  # avoid printing separator for first element
            while True:
                # blocks until data becomes available
                record = queue.get()
                if record == '_CLOSE_STREAM_':
                    outfile.close()
                    break
                elif record == '_OPEN_LIST_':
                    outfile.write('[\n\t')
                    separate = False
                elif record == '_CLOSE_LIST_':
                    outfile.write('\n]')
                    separate = True
                else:
                    if separate:
                        outfile.write(OutputMgr.separator)
                    json.dump(record, outfile)
                    separate = True

    @staticmethod
    def all_done():
        '''
        Lets the class know all output has been completed,
        allowing it to take any actions necessary for the current mode
        and output destination, as well as shutting down the manager.
        '''
        OutputMgr._functions['_ALL_DONE_']()
        OutputMgr.shut_down()
        pass

    @staticmethod
    def _all_done_one_file():
        OutputMgr.write('_CLOSE_LIST_')
        pass

    @staticmethod
    def shut_down():
        '''
        Shuts down the output manager, freeing resources and necessitating
        another init() call if further service is required.
        Automatically called if the caller specifies all_done().
        Should also be included in the onexit manager of a resource
        that has initialised this class.
        '''
        if (OutputMgr.queue is not None and
                OutputMgr.dump_process.exitcode is None):
            log.debug("Stopping dump process")
            OutputMgr.write('_CLOSE_STREAM_')
            OutputMgr.dump_process.join()

    @staticmethod
    def _register_runner_one_file(pid, message):
        return OutputMgr.target

    @staticmethod
    def register_runner(pid, message):
        '''
        Registers the runner with the output handler. This is generally
        used for making sure context and scenario data is printed exactly
        once per runner.
        '''
        # get output destination from mode-dependent function
        OutputMgr.output_descriptors[pid] = \
            OutputMgr._functions['_REGISTER_RUNNER_'](pid, message)

        message['runnerID'] = pid
        OutputMgr.queue.put(message)

    @staticmethod
    def _init_dump_one_file():
        OutputMgr.write('_OPEN_LIST_')

    @staticmethod
    def init(args):
        '''
        Sets starting values and sets up a thread-safe queue for
        taking output data, directed to the appropriate destination.
        Needs to be called before write() is called, or an
        error will occur.
        '''

        log.debug("Starting dump process file '%s'" %
                  args.output_file)
        OutputMgr.target = args.output_file
        OutputMgr.queue = multiprocessing.Queue()
        OutputMgr.dump_process = multiprocessing.Process(
            target=OutputMgr._output_serializer_streamer,
            name="Dumper",
            args=(args.output_file, OutputMgr.queue))

        # TODO: Read output mode from args
        # and select these values appropriately
        OutputMgr.output_descriptor = OutputMgr.target
        OutputMgr._functions['_ALL_DONE_'] = \
            OutputMgr._all_done_one_file
        OutputMgr._functions['_REGISTER_RUNNER_'] = \
            OutputMgr._register_runner_one_file
        OutputMgr._functions['_INIT_DUMP_'] = \
            OutputMgr._init_dump_one_file
        OutputMgr.dump_process.start()
