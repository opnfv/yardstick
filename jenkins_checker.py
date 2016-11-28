##############################################################################
# Copyright (c) 2015 - 2016, Intel Corporation.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import print_function
from __future__ import absolute_import

import logging
import os
import re
from subprocess import Popen, CalledProcessError, PIPE
import signal
import sys
import errno
import time
from itertools import chain, islice

import cgitb
import argparse
import resource
import operator
from six.moves import filter
from six.moves import range

DEFAULT_GIT_HEAD = "HEAD"

cgitb.enable(format="text")

logging.basicConfig(level=logging.DEBUG)

PYTHON_VERSION = sys.version_info[0]

# min of 4 * num cores or half max open files - 10
PARALLEL_LIMIT = min(os.sysconf('SC_NPROCESSORS_ONLN') * 4,
                     (resource.getrlimit(resource.RLIMIT_NOFILE)[0] / 2) - 10)

def _reset_sigpipe():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def is_file_and_rx(path):
    """
    :param path: path to check
    :return: true if the path is a file and R_OK & X_OK
    :rtype: bool
    """
    return os.path.isfile(path) and os.access(path, os.R_OK & os.X_OK)


def grouper_it(iterable, n):
    it = iter(iterable)
    while True:
        chunk_it = islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield chain((first_el,), chunk_it)


mswindows = (sys.platform == "win32")


class WrappedPopen(Popen):

    @staticmethod
    def auto_string_split(cmd, shell):
        if hasattr(cmd, "encode"):
            saved_cmd_str = cmd
            # only split if we aren't using shell
            if not shell:
                cmd = cmd.split()
        else:
            saved_cmd_str = " ".join(cmd)
        return cmd, saved_cmd_str

    def __init__(
            self, cmd, bufsize=0, executable=None, stdin=None, stdout=None,
            stderr=None, preexec_fn=None,
            close_fds=False, shell=False, cwd=None, env=None,
            universal_newlines=False, startupinfo=None,
            creationflags=0):
        """
        Wrap a Popen with some extra exit checkers.
        Also auto-split a string if non-shell
        Also reset SIGPIPE by default.

        @param cmd: string or list of commands to run
        @type cmd: str, list
        @return: wrapped Popen object
        @rtype: WrappedPopen
        """
        # reset sigpipe as unix processes expect
        if preexec_fn is None:
            preexec_fn = _reset_sigpipe
        if mswindows:
            # windows doesn't support preexec_fn
            preexec_fn = None
        cmd, self._saved_cmd_str = self.auto_string_split(cmd, shell)
        logging.debug("+ " + self._saved_cmd_str)
        self._cwd = cwd
        self._start_time = time.time()
        self._retcode = None
        try:
            super(
                WrappedPopen, self).__init__(cmd, bufsize, executable, stdin,
                                             stdout, stderr,
                                             preexec_fn, close_fds, shell, cwd,
                                             env,
                                             universal_newlines, startupinfo,
                                             creationflags)
        except OSError as e:
            if e.errno == errno.ENOENT:
                if not is_file_and_rx(cmd[0]):
                    raise OSError(e.errno, 'No such file or directory "%s"' %
                                  cmd[0])
                elif not os.path.isdir(self._cwd):
                    raise OSError(e.errno, 'No such file or directory "%s"' %
                                  self._cwd)
                else:
                    raise e
            else:
                raise e

    def communicate(self, *args, **kwargs):
        result = super(WrappedPopen, self).communicate(*args, **kwargs)
        self._log_duration(self._saved_cmd_str, self._start_time)
        # extra wait to make sure?
        self.wait()
        return result

    @staticmethod
    def _log_duration(cmd, start_time):
        if start_time is not None:
            logging.debug(
                "duration: %.2f , cmd: %s", time.time() - start_time, cmd)

    @staticmethod
    def exit_checker(cmd, retcode, start_time=None):
        """

        @param cmd: command line as a string
        @type cmd: str
        @param retcode: integer return code, non-zero indicates error
        @type retcode: int
        @param start_time: start time since epoch
        @type start_time: float, None
        @return: zero for success
        @rtype: int
        """
        WrappedPopen._log_duration(cmd, start_time)
        if retcode != 0:
            raise CalledProcessError(retcode, cmd)
        else:
            return 0

    def check_exit(self):
        """
        Wait for process to complete.  If the exit code was zero then return,
        otherwise raise
        CalledProcessError.  The CalledProcessError object will have the
        return code in the returncode attribute.

        @param self: existing Popen object
        @type self: WrappedPopen
        @return: POSIX exit status
        @rtype: int
        """
        retcode = self.wait()
        self.exit_checker(self._saved_cmd_str, retcode, self._start_time)


def multi_filter(predicates, iters):
    for p in predicates:
        iters = filter(p, iters)
    return iters

DEFAULT_CHECKERS = ('flake8', 'pylint', 'pytest')


get_outputs = operator.itemgetter(0, 1)
get_stdout = operator.itemgetter(0)
get_exit_status = operator.itemgetter(2)


class Tester(object):

    def __init__(self, test_dir, checkers=DEFAULT_CHECKERS, blocking_failure_log='',
                 git_head=None):
        super(Tester, self).__init__()
        self.blocking_failures = []
        self.test_dir = test_dir
        self.checkers = checkers
        self.blocking_failure_log = blocking_failure_log
        self.git_head = git_head
        self.ssh = None
        if self.git_head is None:
            # by default use the current workspace modified files
            self.get_changed_files = self.get_changed_files_from_workspace
        else:
            self.get_changed_files = self.get_changed_files_from_commit

    def chdir(self):
        pass

    def process_errors(self, errors):
        for error in errors:
            logging.debug("%s: %s", error, self.PYTEST_EXIT_CODES.get(error, error))
        # for some reason we can not collect any tests, ignore those values
        errors = [e for e in errors if e != self.PYTEST_EXIT_VALUES['EXIT_NOTESTSCOLLECTED']]
        return errors

    def run_pytest(self):
        return []

    def pre_clean(self):
        WrappedPopen(
            ['find', '.', '-name', '__pycache__', '-o', '-name', '*.pyc',
             '-delete']).wait()
        # don't delete, we overwrite each time
        # try:
        #     os.unlink(self.blocking_failure_log)
        # except OSError:
        #     pass

    FLAKE8_MSG_LINE_RE = re.compile(r'^(?P<path>[^:\n]+):(?P<line>\d+):(?P<column>\d+): '
                                    r'(?P<code>\w+) (?P<message>.+)$',
                                    re.M)

    FLAKE8_OUTPUT_BUT_DONT_FAIL = set(
        chain(
            [
                "E128",  # continuation line under-indented for visual indent
                "E265",  # block comment should start with '# '
            ],
            ("E%s" % n for n in range(121, 713))
        )
    )

# pep8 codes
# code 	sample message
# E1 	Indentation
# "E101",  # indentation contains mixed spaces and tabs
# "E111",  # indentation is not a multiple of four
# "E112",  # expected an indented block
# "E113",  # unexpected indentation
# "E114",  # indentation is not a multiple of four (comment)
# "E115",  # expected an indented block (comment)
# "E116",  # unexpected indentation (comment)
#
# "E121",  # (^) 	continuation line under-indented for hanging indent
# "E122",  # (^) 	continuation line missing indentation or outdented
# "E123",  # (*) 	closing bracket does not match indentation of opening bracket's line
# "E124",  # (^) 	closing bracket does not match visual indentation
# "E125",  # (^) 	continuation line with same indent as next logical line
# "E126",  # (^) 	continuation line over-indented for hanging indent
# "E127",  # (^) 	continuation line over-indented for visual indent
# "E128",  # (^) 	continuation line under-indented for visual indent
# "E129",  # (^) 	visually indented line with same indent as next logical line
# "E131",  # (^) 	continuation line unaligned for hanging indent
# "E133",  # (*) 	closing bracket is missing indentation
#
# E2 	Whitespace
# "E201",  # whitespace after '('
# "E202",  # whitespace before ')'
# "E203",  # whitespace before ':'
#
# "E211",  # whitespace before '('
#
# "E221",  # multiple spaces before operator
# "E222",  # multiple spaces after operator
# "E223",  # tab before operator
# "E224",  # tab after operator
# "E225",  # missing whitespace around operator
# "E226",  # (*) 	missing whitespace around arithmetic operator
# "E227",  # missing whitespace around bitwise or shift operator
# "E228",  # missing whitespace around modulo operator
#
# "E231",  # missing whitespace after ','
#
# "E241",  # (*) 	multiple spaces after ','
# "E242",  # (*) 	tab after ','
#
# "E251",  # unexpected spaces around keyword / parameter equals
# "E261",  # at least two spaces before inline comment
# "E262",  # inline comment should start with '# '
# "E265",  # block comment should start with '# '
# "E266",  # too many leading '#' for block comment
# "E271",  # multiple spaces after keyword
# "E272",  # multiple spaces before keyword
# "E273",  # tab after keyword
# "E274",  # tab before keyword
#
# E3 	Blank line
# "E301",  # expected 1 blank line, found 0
# "E302",  # expected 2 blank lines, found 0
# "E303",  # too many blank lines (3)
# "E304",  # blank lines found after function decorator
#
# E4 	Import
# "E401",  # multiple imports on one line
#
# E5 	Line length
# "E501",  # (^) 	line too long (82 > 79 characters)
# "E502",  # the backslash is redundant between brackets
#
# E7 	Statement
# "E701",  # multiple statements on one line (colon)
# "E702",  # multiple statements on one line (semicolon)
# "E703",  # statement ends with a semicolon
# "E704",  # multiple statements on one line (def)
# "E711",  # (^) 	comparison to None should be 'if cond is None:'
# "E712",  # (^) 	comparison to True should be 'if cond is True:' or 'if cond:'
# "E713",  # test for membership should be 'not in'
# "E714",  # test for object identity should be 'is not'
# "E721",  # do not compare types, use 'isinstance()'
# "E731",  # do not assign a lambda expression, use a def
#
# E9 	Runtime
# "E901",  # SyntaxError or IndentationError
# "E902",  # IOError
#
# W1 	Indentation warning
# "W191",  # indentation contains tabs
#
# W2 	Whitespace warning
# "W291",  # trailing whitespace
# "W292",  # no newline at end of file
# "W293",  # blank line contains whitespace
#
# W3 	Blank line warning
# "W391",  # blank line at end of file
#
# W6 	Deprecation warning
# "W601",  # .has_key() is deprecated, use 'in'
# "W602",  # deprecated form of raising exception
# "W603",  # '<>' is deprecated, use '!='
# "W604",  # backticks are deprecated, use 'repr()'
#
# pyflakes codes:
# code 	sample message
#
# "F401",  # module imported but unused
# "F402",  # import module from line N shadowed by loop variable
# "F403",  # 'from module import *' used; unable to detect undefined names
# "F404",  # future import(s) name after other statements
# "F811",  # redefinition of unused name from line N
# "F812",  # list comprehension redefines name from line N
# "F821",  # undefined name name
# "F822",  # undefined name name in __all__
# "F823",  # local variable name ... referenced before assignment
# "F831",  # duplicate argument name in function definition
# "F841",  # local variable name is assigned to but never used
#
# pep8-naming codes:
# code 	sample message
# "N801",  # class names should use CapWords convention
# "N802",  # function name should be lowercase
# "N803",  # argument name should be lowercase
# "N804",  # first argument of a classmethod should be named 'cls'
# "N805",  # first argument of a method should be named 'self'
# "N806",  # variable in function should be lowercase
# "N811",  # constant imported as non constant
# "N812",  # lowercase imported as non lowercase
# "N813",  # camelcase imported as lowercase
# "N814",  # camelcase imported as constant

    FLAKE8_FATAL_ERRORS = {
        "E101",  # indentation contains mixed spaces and tabs
        "E111",  # indentation is not a multiple of four
        "E112",  # expected an indented block
        "E113",  # unexpected indentation
        "E114",  # indentation is not a multiple of four (comment)
        "E115",  # expected an indented block (comment)
        "E116",  # unexpected indentation (comment)
        "E711",  # (^) 	comparison to None should be 'if cond is None:'
        "E712",  # (^) 	comparison to True should be 'if cond is True:' or 'if cond:'
        "E713",  # test for membership should be 'not in'
        "E714",  # test for object identity should be 'is not'
        "E721",  # do not compare types, use 'isinstance()'
        "E731",  # do not assign a lambda expression, use a def
        "W191",  # indentation contains tabs
        "W601",  # .has_key() is deprecated, use 'in'
        "W602",  # deprecated form of raising exception
        "W603",  # '<>' is deprecated, use '!='
        "W604",  # backticks are deprecated, use 'repr()'
        "F403",  # 'from module import *' used; unable to detect undefined names
        "F821",  # undefined name name
        "F822",  # undefined name name in __all__
        "F831",  # duplicate argument name in function definition
        "N804",  # first argument of a classmethod should be named 'cls'
        "N805",  # first argument of a method should be named 'self'
        "N811",  # constant imported as non constant
        "N812",  # lowercase imported as non lowercase
        "N813",  # camelcase imported as lowercase
        "N814",  # camelcase imported as constant
    }

    @classmethod
    def _decode_messages(cls, regexp, stdouts):
        matches = chain.from_iterable(
            regexp.finditer(stdout) for stdout in stdouts)
        messages = (m.groupdict() for m in matches if m)
        return messages

    # CODE_RE = re.compile("([A-Z]+)(\d+)")
    #
    # @classmethod
    # def _split_code(cls, code):
    # return code[0], int(code[1:])
    #     cat, val = cls.CODE_RE.search(code).groups()
    #     return cat, int(val)

    @classmethod
    def flake8_find_failures(cls, messages):
        """
        @param messages:  iterator of messages
        @type messages: iter()
        @return: list of failures, must be list so we can check if empty
        @rtype: list
        """
        return [m for m in messages if m['code'] in cls.FLAKE8_FATAL_ERRORS]

    @staticmethod
    def print_failures(failures, output=sys.stderr):
        for f in failures:
            print("[BLOCKING FAILURE] {0[path]}:{0[line]} [{0[code]}] {0[message]}".format(f),
                  file=output)

    FLAKE8_USAGE_ERROR = 2

    def run_flake8(self, changed_files):
        """

        @param changed_files: list of changed files
        @type changed_files: list(str)
        @rtype: list
        """
        results = self.get_flake8_outputs(changed_files)
        for stdout, stderr in (get_outputs(r) for r in results):
            sys.stdout.write(stdout)
            # write stderr so we catch pylint bugs
            sys.stderr.write(stderr)
        # flush so we see if with logging
        sys.stdout.flush()
        # usage error or some other flake8 error, exit with failure
        flake8_exit_failure = any(
            get_exit_status(r) >= self.FLAKE8_USAGE_ERROR for r in results)
        if flake8_exit_failure:
            return flake8_exit_failure
        messages = self._decode_messages(self.FLAKE8_MSG_LINE_RE, (get_stdout(r) for r in results))
        failures = self.flake8_find_failures(messages)
        self.blocking_failures.extend(failures)
        # convert to bool, only fail is failures has messages
        return [bool(failures)]

    # PYTEST_HAS_NO_MEMBER = re.compile("Module 'pytest(?:\..+)?' has no '.+' "
    #                                   "member")

    @classmethod
    def get_flake8_outputs(cls, changed_files):
        file_batches = grouper_it(changed_files, PARALLEL_LIMIT)
        results = []
        for file_batch in file_batches:
            results.extend(
                cls.get_command_outputs(
                    [WrappedPopen(["flake8", f], stdout=PIPE, stderr=PIPE)
                     for f in file_batch])
            )
        logging.debug("flake8 exit statuses=%s", [get_exit_status(r) for r in results])
        return results

    PYLINT_MSG_LINE_RE = re.compile(r'^(?P<path>[^:\n]+):(?P<line>\d+): '
                                    r'\[(?P<code>[^\n\]]+)\] (?P<message>.+)$',
                                    re.M)
    PYLINT_DISABLED_WARNINGS = [
        # "E1101",  # ignore has_no_member due to false positives
        "I0011",  # Locally disabling undefined-variable
        "C0302",  # Too many lines in module
        "C0301",  # Line is longer than max limit (default = 80)
        "C0330",  # Wrong continued indentation.
        "C0103",  # Does not fit naming convention
        "C0111",  # Missing docstring
        "W0105",  # String statement has no effect
        "W0221",  # Arguments list do not fit overloaded method
        "W0403",
        "R0201",  # Method could be a function
        "R0903",
        "R0904",
        "R0912",  # Too many branches
        "R0913",  # Too many arguments
        "R0914",  # Too many local variables
        "R0915",  # Too many statements
    ]
    IGNORED_MODULES = [
        'pytest',
        'py.code',  # pytest magic, py.code.ExceptionInfo
    ]
    GENERATED_MEMBERS = [
    ]
    IGNORED_CLASSES = [
    ]
    DISABLED_STRING = ",".join(PYLINT_DISABLED_WARNINGS)
    IGNORED_MODULES_STRING = ','.join(IGNORED_MODULES)
    IGNORED_CLASSES_STRING = ','.join(IGNORED_CLASSES)

    GENERATED_MEMBERS_STRING = ','.join(GENERATED_MEMBERS)

    #   Output status code:
    # Pylint should leave with following status code:
    # * 0 if everything went fine
    # * 1 if a fatal message was issued
    # * 2 if an error message was issued
    # * 4 if a warning message was issued
    # * 8 if a refactor message was issued
    # * 16 if a convention message was issued
    # * 32 on usage error
    # status 1 to 16 will be bit-ORed so you can know which different
    # categories has been issued by analysing pylint output status code

    PYLINT_USAGE_ERROR = 32

    PYTEST_EXIT_CODES = {
        0: 'EXIT_OK',
        1: 'EXIT_TESTSFAILED',
        2: 'EXIT_INTERRUPTED',
        3: 'EXIT_INTERNALERROR',
        4: 'EXIT_USAGEERROR',
        5: 'EXIT_NOTESTSCOLLECTED',
    }
    PYTEST_EXIT_VALUES = {
        'EXIT_OK': 0,
        'EXIT_TESTSFAILED': 1,
        'EXIT_INTERRUPTED': 2,
        'EXIT_INTERNALERROR': 3,
        'EXIT_USAGEERROR': 4,
        'EXIT_NOTESTSCOLLECTED': 5,
    }

    @staticmethod
    def get_command_outputs(procs):
        outputs = [[out.decode(u'utf-8') for out in p.communicate()] + [p.wait()] for p in procs]
        return outputs

    @classmethod
    def get_pylint_outputs(cls, changed_files):
        logging.debug("PYTHONPATH=%s", os.environ['PYTHONPATH'])
        file_batches = grouper_it(changed_files, PARALLEL_LIMIT)
        results = []
        for file_batch in file_batches:
            results.extend(
                cls.get_command_outputs(
                    [WrappedPopen(
                        ['pylint', '--msg-template={path}:{line}: [{msg_id}] {msg}',
                         "--disable={0}".format(cls.DISABLED_STRING),
                         "--ignored-modules={0}".format(cls.IGNORED_MODULES_STRING),
                         "--generated-members={0}".format(
                             cls.GENERATED_MEMBERS_STRING),
                         "--ignored-classes={0}".format(cls.IGNORED_CLASSES_STRING),
                         "-r", "no", f], stdout=PIPE, stderr=PIPE, env=os.environ)
                     for f in file_batch]))

        logging.debug("pylint exit statuses=%s", [get_exit_status(r) for r in results])
        return results

#
# "C0102",  # Black listed name "%s"
# "C0103",  # Invalid %s name "%s"
# "C0111",  # Missing %s docstring
# "C0112",  # Empty %s docstring
# "C0121",  # Missing required attribute "%s"
# "C0202",  # Class method %s should have cls as first argument
# "C0203",  # Metaclass method %s should have mcs as first argument
# "C0204",  # Metaclass class method %s should have %s as first argument
# "C0301",  # Line too long (%s/%s)
# "C0302",  # Too many lines in module (%s)
# "C0303",  # Trailing whitespace
# "C0304",  # Final newline missing
# "C0321",  # More than one statement on a single line
# "C0322",  # Old: Operator not preceded by a space
# "C0323",  # Old: Operator not followed by a space
# "C0324",  # Old: Comma not followed by a space
# "C0325",  # Unnecessary parens after %r keyword
# "C0326",  # %s space %s %s %s\n%s
# "C1001",  # Old-style class defined.
# "E0001",  # (syntax error raised for a module; message varies)
# "E0011",  # Unrecognized file option %r
# "E0012",  # Bad option value %r
# "E0100",  # __init__ method is a generator
# "E0101",  # Explicit return in __init__
# "E0102",  # %s already defined line %s
# "E0103",  # %r not properly in loop
# "E0104",  # Return outside function
# "E0105",  # Yield outside function
# "E0106",  # Return with argument inside generator
# "E0107",  # Use of the non-existent %s operator
# "E0108",  # Duplicate argument name %s in function definition
# "E0202",  # An attribute affected in %s line %s hide this method
# "E0203",  # Access to member %r before its definition line %s
# "E0211",  # Method has no argument
# "E0213",  # Method should have "self" as first argument
# "E0221",  # Interface resolved to %s is not a class
# "E0222",  # Missing method %r from %s interface
# "E0235",  # __exit__ must accept 3 arguments: type, value, traceback
# "E0501",  # Old: Non ascii characters found but no encoding specified (PEP 263)
# "E0502",  # Old: Wrong encoding specified (%s)
# "E0503",  # Old: Unknown encoding specified (%s)
# "E0601",  # Using variable %r before assignment
# "E0602",  # Undefined variable %r
# "E0603",  # Undefined variable name %r in __all__
# "E0604",  # Invalid object %r in __all__, must contain only strings
# "E0611",  # No name %r in module %r
# "E0701",  # Bad except clauses order (%s)
# "E0702",  # Raising %s while only classes, instances or string are allowed
# "E0710",  # Raising a new style class which doesn't inherit from BaseException
# "E0711",  # NotImplemented raised - should raise NotImplementedError
# "E0712",  # Catching an exception which doesn\'t inherit from BaseException: %s
# "E1001",  # Use of __slots__ on an old style class
# "E1002",  # Use of super on an old style class
# "E1003",  # Bad first argument %r given to super()
# "E1004",  # Missing argument to super()
# "E1101",  # %s %r has no %r member
# "E1102",  # %s is not callable
# "E1103",  # %s %r has no %r member (but some types could not be inferred)
# "E1111",  # Assigning to function call which doesn't return
# "E1120",  # No value passed for parameter %s in function call
# "E1121",  # Too many positional arguments for function call
# "E1122",  # Old: Duplicate keyword argument %r in function call
# "E1123",  # Passing unexpected keyword argument %r in function call
# "E1124",  # Parameter %r passed as both positional and keyword argument
# "E1125",  # Old: Missing mandatory keyword argument %r
# "E1200",  # Unsupported logging format character %r (%#02x) at index %d
# "E1201",  # Logging format string ends in middle of conversion specifier
# "E1205",  # Too many arguments for logging format string
# "E1206",  # Not enough arguments for logging format string
# "E1300",  # Unsupported format character %r (%#02x) at index %d
# "E1301",  # Format string ends in middle of conversion specifier
# "E1302",  # Mixing named and unnamed conversion specifiers in format string
# "E1303",  # Expected mapping for format string, not %s
# "E1304",  # Missing key %r in format string dictionary
# "E1305",  # Too many arguments for format string
# "E1306",  # Not enough arguments for format string
# "E1310",  # Suspicious argument in %s.%s call
# "F0001",  # (error prevented analysis; message varies)
# "F0002",  # %s: %s (message varies)
# "F0003",  # ignored builtin module %s
# "F0004",  # unexpected inferred value %s
# "F0010",  # error while code parsing: %s
# "F0202",  # Unable to check methods signature (%s / %s)
# "F0220",  # failed to resolve interfaces implemented by %s (%s)
# "F0321",  # Old: Format detection error in %r
# "F0401",  # Unable to import %s
# "I0001",  # Unable to run raw checkers on built-in module %s
# "I0010",  # Unable to consider inline option %r
# "I0011",  # Locally disabling %s
# "I0012",  # Locally enabling %s
# "I0013",  # Ignoring entire file
# "I0014",  # Used deprecated directive "py lint:disable-all" or "py lint:disable=all"
# "I0020",  # Suppressed %s (from line %d)
# "I0021",  # Useless suppression of %s
# "I0022",  # Deprecated pragma "py lint:disable-msg" or "py lint:enable-msg"
# "R0201",  # Method could be a function
# "R0401",  # Cyclic import (%s)
# "R0801",  # Similar lines in %s files
# "R0901",  # Too many ancestors (%s/%s)
# "R0902",  # Too many instance attributes (%s/%s)
# "R0903",  # Too few public methods (%s/%s)
# "R0904",  # Too many public methods (%s/%s)
# "R0911",  # Too many return statements (%s/%s)
# "R0912",  # Too many branches (%s/%s)
# "R0913",  # Too many arguments (%s/%s)
# "R0914",  # Too many local variables (%s/%s)
# "R0915",  # Too many statements (%s/%s)
# "R0921",  # Abstract class not referenced
# "R0922",  # Abstract class is only referenced %s times
# "R0923",  # Interface not implemented
# "W0101",  # Unreachable code
# "W0102",  # Dangerous default value %s as argument
# "W0104",  # Statement seems to have no effect
# "W0105",  # String statement has no effect
# "W0106",  # Expression "%s" is assigned to nothing
# "W0107",  # Unnecessary pass statement
# "W0108",  # Lambda may not be necessary
# "W0109",  # Duplicate key %r in dictionary
# "W0110",  # map/filter on lambda could be replaced by comprehension
# "W0120",  # Else clause on loop without a break statement
# "W0121",  # Use raise ErrorClass(args) instead of raise ErrorClass, args.
# "W0122",  # Use of exec
# "W0141",  # Used builtin function %r
# "W0142",  # Used * or ** magic
# "W0150",  # %s statement in finally block may swallow exception
# "W0199",  # Assert called on a 2-uple. Did you mean \'assert x,y\'?
# "W0201",  # Attribute %r defined outside __init__
# "W0211",  # Static method with %r as first argument
# "W0212",  # Access to a protected member %s of a client class
# "W0221",  # Arguments number differs from %s method
# "W0222",  # Signature differs from %s method
# "W0223",  # Method %r is abstract in class %r but is not overridden
# "W0231",  # __init__ method from base class %r is not called
# "W0232",  # Class has no __init__ method
# "W0233",  # __init__ method from a non direct base class %r is called
# "W0234",  # iter returns non-iterator
# "W0301",  # Unnecessary semicolon
# "W0311",  # Bad indentation. Found %s %s, expected %s
# "W0312",  # Found indentation with %ss instead of %ss
# "W0331",  # Use of the <> operator
# "W0332",  # Use of "l" as long integer identifier
# "W0333",  # Use of the `` operator
# "W0401",  # Wildcard import %s
# "W0402",  # Uses of a deprecated module %r
# "W0403",  # Relative import %r, should be %r
# "W0404",  # Reimport %r (imported line %s)
# "W0406",  # Module import itself
# "W0410",  # __future__ import is not the first non docstring statement
# "W0511",  # (warning notes in code comments; message varies)
# "W0512",  # Cannot decode using encoding "%s", unexpected byte at position %d
# "W0601",  # Global variable %r undefined at the module level
# "W0602",  # Using global for %r but no assigment is done
# "W0603",  # Using the global statement
# "W0604",  # Using the global statement at the module level
# "W0611",  # Unused import %s
# "W0612",  # Unused variable %r
# "W0613",  # Unused argument %r
# "W0614",  # Unused import %s from wildcard import
# "W0621",  # Redefining name %r from outer scope (line %s)
# "W0622",  # Redefining built-in %r
# "W0623",  # Redefining name %r from %s in exception handler
# "W0631",  # Using possibly undefined loop variable %r
# "W0632",  # Possible unbalanced tuple unpacking with sequence%s:
# "W0633",  # Attempting to unpack a non-sequence%s
# "W0701",  # Raising a string exception
# "W0702",  # No exception type(s) specified
# "W0703",  # Catching too general exception %s
# "W0704",  # Except doesn't do anything
# "W0710",  # Exception doesn't inherit from standard "Exception" class
# "W0711",  # Exception to catch is the result of a binary "%s" operation
# "W0712",  # Implicit unpacking of exceptions is not supported in Python 3
# "W1001",  # Use of "property" on an old style class
# "W1111",  # Assigning to function call which only returns None
# "W1201",  # Specify string format arguments as logging function parameters
# "W1300",  # Format string dictionary key should be a string, not %s
# "W1301",  # Unused key %r in format string dictionary
# "W1401",  # Anomalous backslash in string: \'%s\'. String constant might be missing an r prefix.
# "W1402",  # Anomalous Unicode escape in byte string: \'%s\'. String constant might be missing
# "W1501",  # "%s" is not a valid mode for open.
#
# "RP0001",  # Messages by category
# "RP0002",  # % errors / warnings by module
# "RP0003",  # Messages
# "RP0004",  # Global evaluation
# "RP0101",  # Statistics by type
# "RP0401",  # External dependencies
# "RP0402",  # Modules dependencies graph
# "RP0701",  # Raw metrics
# "RP0801",  # Duplication

    PYLINT_FATAL_ERRORS = {

        "C0121",  # Missing required attribute "%s"
        "C0202",  # Class method %s should have cls as first argument
        "C0203",  # Metaclass method %s should have mcs as first argument
        "C0204",  # Metaclass class method %s should have %s as first argument
        "C1001",  # Old-style class defined.

        "E0001",  # (syntax error raised for a module; message varies)
        "E0011",  # Unrecognized file option %r
        "E0012",  # Bad option value %r
        "E0100",  # __init__ method is a generator
        "E0101",  # Explicit return in __init__
        "E0102",  # %s already defined line %s
        "E0103",  # %r not properly in loop
        "E0104",  # Return outside function
        "E0105",  # Yield outside function
        "E0106",  # Return with argument inside generator
        "E0107",  # Use of the non-existent %s operator
        "E0108",  # Duplicate argument name %s in function definition
        "E0202",  # An attribute affected in %s line %s hide this method
        "E0203",  # Access to member %r before its definition line %s
        "E0211",  # Method has no argument
        "E0213",  # Method should have "self" as first argument
        "E0221",  # Interface resolved to %s is not a class
        "E0222",  # Missing method %r from %s interface
        "E0235",  # __exit__ must accept 3 arguments: type, value, traceback
        "E0501",  # Old: Non ascii characters found but no encoding specified (PEP 263)
        "E0502",  # Old: Wrong encoding specified (%s)
        "E0503",  # Old: Unknown encoding specified (%s)
        "E0601",  # Using variable %r before assignment
        "E0602",  # Undefined variable %r
        "E0603",  # Undefined variable name %r in __all__
        "E0604",  # Invalid object %r in __all__, must contain only strings
        "E0611",  # No name %r in module %r
        "E0701",  # Bad except clauses order (%s)
        "E0702",  # Raising %s while only classes, instances or string are allowed
        "E0710",  # Raising a new style class which doesn't inherit from BaseException
        "E0711",  # NotImplemented raised - should raise NotImplementedError
        "E0712",  # Catching an exception which doesn\'t inherit from BaseException: %s
        "E1001",  # Use of __slots__ on an old style class
        "E1002",  # Use of super on an old style class
        "E1003",  # Bad first argument %r given to super()
        "E1004",  # Missing argument to super()
        "E1101",  # %s %r has no %r member
        "E1102",  # %s is not callable
        "E1103",  # %s %r has no %r member (but some types could not be inferred)
        "E1111",  # Assigning to function call which doesn't return
        "E1120",  # No value passed for parameter %s in function call
        "E1121",  # Too many positional arguments for function call
        "E1122",  # Old: Duplicate keyword argument %r in function call
        "E1123",  # Passing unexpected keyword argument %r in function call
        "E1124",  # Parameter %r passed as both positional and keyword argument
        "E1125",  # Old: Missing mandatory keyword argument %r
        "E1200",  # Unsupported logging format character %r (%#02x) at index %d
        "E1201",  # Logging format string ends in middle of conversion specifier
        "E1205",  # Too many arguments for logging format string
        "E1206",  # Not enough arguments for logging format string
        "E1300",  # Unsupported format character %r (%#02x) at index %d
        "E1301",  # Format string ends in middle of conversion specifier
        "E1302",  # Mixing named and unnamed conversion specifiers in format string
        "E1303",  # Expected mapping for format string, not %s
        "E1304",  # Missing key %r in format string dictionary
        "E1305",  # Too many arguments for format string
        "E1306",  # Not enough arguments for format string
        "E1310",  # Suspicious argument in %s.%s call

        "F0001",  # (error prevented analysis; message varies)
        "F0002",  # %s: %s (message varies)
        "F0010",  # error while code parsing: %s

        "R0401",  # Cyclic import (%s)
        "W0102",  # Dangerous default value %s as argument
        "W0109",  # Duplicate key %r in dictionary
        "W0121",  # Use raise ErrorClass(args) instead of raise ErrorClass, args.
        "W0122",  # Use of exec
        "W0150",  # %s statement in finally block may swallow exception
        "W0199",  # Assert called on a 2-uple. Did you mean \'assert x,y\'?
        "W0211",  # Static method with %r as first argument
        "W0221",  # Arguments number differs from %s method
        "W0233",  # __init__ method from a non direct base class %r is called
        "W0234",  # iter returns non-iterator
        "W0311",  # Bad indentation. Found %s %s, expected %s
        "W0331",  # Use of the <> operator
        "W0332",  # Use of "l" as long integer identifier
        "W0333",  # Use of the `` operator
        "W0401",  # Wildcard import %s
        "W0402",  # Uses of a deprecated module %r
        "W0404",  # Reimport %r (imported line %s)
        "W0410",  # __future__ import is not the first non docstring statement
        "W0406",  # Module import itself
        "W0512",  # Cannot decode using encoding "%s", unexpected byte at position %d
        "W0601",  # Global variable %r undefined at the module level
        "W0602",  # Using global for %r but no assigment is done
        "W0604",  # Using the global statement at the module level
        "W0614",  # Unused import %s from wildcard import
        "W0622",  # Redefining built-in %r
        "W0623",  # Redefining name %r from %s in exception handler
        "W0631",  # Using possibly undefined loop variable %r
        "W0632",  # Possible unbalanced tuple unpacking with sequence%s:
        "W0633",  # Attempting to unpack a non-sequence%s
        "W0701",  # Raising a string exception
        "W0702",  # No exception type(s) specified
        "W0711",  # Exception to catch is the result of a binary "%s" operation
        "W0712",  # Implicit unpacking of exceptions is not supported in Python 3
        "W1001",  # Use of "property" on an old style class
        "W1111",  # Assigning to function call which only returns None
        "W1201",  # Specify string format arguments as logging function parameters
        "W1300",  # Format string dictionary key should be a string, not %s
        "W1301",  # Unused key %r in format string dictionary
        "W1501",  # "%s" is not a valid mode for open.

    }

    @classmethod
    def pylint_find_failures(cls, messages):
        """
        @param messages:  iterator of messages
        @type messages: iter()
        @return: list failures, must be list so we can check empty
        @rtype: list
        """
        return [m for m in messages if m['code'] in
                cls.PYLINT_FATAL_ERRORS]

    def run_pylint(self, changed_python_files):
        """

        @param changed_python_files: list of changed files
        @type changed_python_files: list(str)
        @rtype: list
        """
        results = self.get_pylint_outputs(
            changed_python_files)
        for stdout, stderr in (get_outputs(p) for p in results):
            sys.stdout.write(stdout)
            sys.stderr.write(stderr)
        # flush so we see if with logging
        sys.stdout.flush()
        # usage error or some other pylint error, exit with failure
        pylint_exit_failure = any(
            get_exit_status(r) >= self.PYLINT_USAGE_ERROR for r in results)
        if pylint_exit_failure:
            return [pylint_exit_failure]
        messages = self._decode_messages(self.PYLINT_MSG_LINE_RE, (get_stdout(r) for r in results))
        failures = self.pylint_find_failures(messages)
        self.blocking_failures.extend(failures)
        # convert to bool, only fail if failures has messages
        return [bool(failures)]

    # don't examine deleted files
    GIT_STATUS_RE = re.compile(u'^[^D]\\s+(\\S+)$', re.M)

    def get_changed_files_from_commit(self):
        git_diff_tree_cmd = ["git", "diff-tree", "--no-commit-id",
                             "--name-status", "-r", self.git_head]
        proc = WrappedPopen(git_diff_tree_cmd, stdout=PIPE)
        git_changed_files = proc.communicate()[0].decode(u'utf-8')
        proc.check_exit()
        changed_files = self.GIT_STATUS_RE.findall(git_changed_files)
        logging.debug("Changed Files = %s", ", ".join(changed_files))
        return changed_files

    def get_changed_files_from_workspace(self):
        # null separator
        git_diff_tree_cmd = ["git", "ls-files", "-z", "-m"]
        proc = WrappedPopen(git_diff_tree_cmd, stdout=PIPE)
        git_changed_files = proc.communicate()[0].decode(u'utf-8')
        proc.check_exit()
        changed_files = git_changed_files.split(u"\0")
        logging.debug("Changed Files = %s", ", ".join(changed_files))
        return changed_files


    def do_test(self):
        self.chdir()
        self.pre_clean()
        # pip_update runs as root disable it
        # self.pip_update()
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        git_changed_files = self.get_changed_files()
        # filter out non-python files
        changed_python_files = [f for f in git_changed_files if f.endswith(".py")]
        errors = []
        if 'flake8' in self.checkers:
            flake8_errors = self.run_flake8(changed_python_files)
            errors.extend(flake8_errors)
        if 'pylint' in self.checkers:
            pylint_errors = self.run_pylint(changed_python_files)
            errors.extend(pylint_errors)
        if self.blocking_failures:
            self.print_failures(self.blocking_failures)
        # If Jenkins then write always, even with empty list
        if self.blocking_failure_log:
            # normalize
            self.blocking_failure_log = os.path.realpath(self.blocking_failure_log)
            with open(self.blocking_failure_log, "w") as blocking_file:
                self.print_failures(self.blocking_failures, output=blocking_file)
        if 'pytest' in self.checkers:
            py_test_errors = self.run_pytest()
            errors.extend(py_test_errors)
        if any(errors):
            raise SystemExit(max(errors))

    @staticmethod
    def _path_filter(prefix, files):
        matches = [f for f in files if f.startswith(prefix)]
        if matches:
            return prefix, matches

    def pip_update(self):
        # using local devpi caching mirror
        PIP_MIRROR = ""
        PIP_MIRROR_HOST = ""
        WrappedPopen([
            'sudo', '-H', 'pip',
            'install',
            '-i',
            PIP_MIRROR,
            '--trusted-host',
            PIP_MIRROR_HOST,
            'yamllint',
        ]).wait()
        WrappedPopen([
            'sudo', '-H', 'pip',
            'install',
            '-i',
            PIP_MIRROR,
            '--trusted-host',
            PIP_MIRROR_HOST,
            '-r',
            os.path.join(self.test_dir, "requirements.txt"),
        ]).wait()



# NUM_CPUS = multiprocessing.cpu_count()
# override and set to just 2, because we are getting weird errors from pytest
NUM_CPUS = 1


class TestYardstick(Tester):
    UNITTEST_PREFIX = "unittests"

    def __init__(self, test_dir, checkers=DEFAULT_CHECKERS, blocking_failure_log='', git_head=None):
        super(TestYardstick, self).__init__(test_dir, checkers,
                                            blocking_failure_log=blocking_failure_log,
                                            git_head=git_head)

    def chdir(self):
        os.chdir(self.test_dir)


TESTERS = {
    'yardstick': TestYardstick,
}


def try_jenkins_config():
    args = argparse.Namespace()
    try:
        # only should be true if called from Jenkins
        args.workspace = os.environ['WORKSPACE']
        args.project = os.environ['GERRIT_PROJECT']
    except KeyError:
        return None
    else:
        # defaults
        args.test_dir = "."
        args.blocking_failure_log = os.path.join(args.workspace, "blocking.txt")
        # only use FETCH_HEAD for gerrit
        args.git_head = "FETCH_HEAD"
        args.checkers = DEFAULT_CHECKERS
        logging.debug(args)
        return args

DESCRIPTION = """\
This program checks code for various warnings and errors

By default the script scans all the locally modified files
in the current git workspace using git ls-files -m.
You can also specify a single commit to check using
--git-head, e.g. --git_head HEAD

"""

EPILOG = """\
Examples:


"""


def main():

    args = try_jenkins_config()
    if args is None:
        parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument("project", choices=list(TESTERS.keys()),
                            help="which project to test, taf core or testcases")
        parser.add_argument("test_dir", help="path to testcases")
        parser.add_argument("--checkers",
                            help="Comma separated list of checkers to run default: %(default)s",
                            default=",".join(DEFAULT_CHECKERS))
        parser.add_argument("--blocking_failure_log", help="Output path for blocking failures")
        parser.add_argument("--git_head",
                            help="commit to scan for changed files, e.g. --git_head=HEAD")
        args = parser.parse_args()
        args.checkers = args.checkers.split(",")

    # add local python paths
    # we really want the parent of testlib, which is $WORKSPACE/taf
    os.environ['PYTHONPATH'] = os.pathsep.join([args.test_dir])

    # WrappedPopen(['sudo', 'git', 'clean', '-fdx']).wait()
    tester = TESTERS[args.project](args.test_dir, args.checkers,
                                   args.blocking_failure_log,
                                   args.git_head)
    tester.do_test()


if __name__ == "__main__":
    main()
