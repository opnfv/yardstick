# Copyright 2012 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import os
import six
from collections import Iterable

from six.moves import StringIO

from yardstick.common.utils import validate_non_string_sequence

_LOCAL_DEFAULT = object()


class ParseError(Exception):

    def __init__(self, message, line_no, line):
        self.msg = message
        self.line = line
        self.line_no = line_no

    def __str__(self):
        return 'at line %d, %s: %r' % (self.line_no, self.msg, self.line)


class SectionParseError(ParseError):

    pass


class LineParser(object):

    PARSE_EXC = ParseError

    @staticmethod
    def strip_key_value(key, value):
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value.startswith(('"', "'")):
            value = value[1:-1]
        return key, [value]

    def __init__(self, line, line_no, semi=';', pound='#'):
        super(LineParser, self).__init__()
        self.line = line
        self.line_no = line_no
        self.continuation = line != line.lstrip()

        if semi:
            semi_active, _, semi_comment = line.partition(';')
        else:
            semi_active = semi_comment = ''
        if pound:
            pound_active, _, pound_comment = line.partition('#')
        else:
            pound_active = pound_comment = ''
        if not semi_comment and not pound_comment:
            self.active = line.strip()
            self.comment = ''
        elif len(semi_comment) > len(pound_comment):
            self.active = semi_active.strip()
            self.comment = semi_comment.strip()
        else:
            self.active = pound_active.strip()
            self.comment = pound_comment.strip()
        self._section_name = None

    def __repr__(self):
        template = "line %d: active '%s' comment '%s'\n%s"
        return template % (self.line_no, self.active, self.comment, self.line)

    @property
    def section_name(self):
        if self._section_name is None:
            if not self.active.startswith('['):
                raise self.error_no_section_start_bracket()
            if not self.active.endswith(']'):
                raise self.error_no_section_end_bracket()
            self._section_name = ''
            if self.active:
                self._section_name = self.active[1:-1]
            if not self._section_name:
                raise self.error_no_section_name()
        return self._section_name

    def is_active_line(self):
        return bool(self.active)

    def is_continuation(self):
        return self.continuation

    def split_key_value(self):
        for sep in ['=', ':']:
            words = self.active.split(sep, 1)
            try:
                return self.strip_key_value(*words)
            except TypeError:
                pass

        return self.active.rstrip(), '@'

    def error_invalid_assignment(self):
        return self.PARSE_EXC("No ':' or '=' found in assignment", self.line_no, self.line)

    def error_empty_key(self):
        return self.PARSE_EXC('Key cannot be empty', self.line_no, self.line)

    def error_unexpected_continuation(self):
        return self.PARSE_EXC('Unexpected continuation line', self.line_no, self.line)

    def error_no_section_start_bracket(self):
        return SectionParseError('Invalid section (must start with [)', self.line_no, self.line)

    def error_no_section_end_bracket(self):
        return self.PARSE_EXC('Invalid section (must end with ])', self.line_no, self.line)

    def error_no_section_name(self):
        return self.PARSE_EXC('Empty section name', self.line_no, self.line)


class BaseParser(object):

    def parse(self, data=None):
        if data is not None:
            return self._parse(data.splitlines())

    def _next_key_value(self, line_parser, key, value):
        self.comment(line_parser)

        if not line_parser.is_active_line():
            # Blank line, ends multi-line values
            if key:
                key, value = self.assignment(key, value, line_parser)
            return key, value

        if line_parser.is_continuation():
            # Continuation of previous assignment
            if key is None:
                raise line_parser.error_unexpected_continuation()

            active = line_parser.active.lstrip()
            try:
                value.append(active)
            except AttributeError:
                # multi-line keys!
                key = os.linesep.join([key, active])

            return key, value

        if key:
            # Flush previous assignment, if any
            key, value = self.assignment(key, value, line_parser)

        try:
            # Section start
            self.new_section(line_parser)
        except SectionParseError:
            pass
        else:
            return key, value

        key, value = line_parser.split_key_value()
        if not key:
            raise line_parser.error_empty_key()
        return key, value

    def _parse(self, line_iter):
        key = None
        value = []

        parse_iter = (LineParser(line, line_no, semi=self.semi, pound=self.pound) for line_no, line
                      in enumerate(line_iter))
        for line_parser in parse_iter:
            key, value = self._next_key_value(line_parser, key, value)

        if key:
            # Flush previous assignment, if any
            self.assignment(key, value, LineParser('EOF', -1))

    def _assignment(self, key, value, line_parser):
        """Called when a full assignment is parsed."""
        raise NotImplementedError()

    def assignment(self, key, value, line_parser):
        self._assignment(key, value, line_parser)
        return None, []

    def new_section(self, line_parser):
        """Called when a new section is started."""
        raise NotImplementedError()

    def comment(self, line_parser):
        """Called when a comment is parsed."""
        raise NotImplementedError()


class YardstickConfigParser(BaseParser):
    """Parses a single config file, populating 'sections' to look like:

        [
            [
                'section1',
                [
                    ['key1', 'value1\nvalue2'],
                    ['key2', 'value3\nvalue4'],
                ],
            ],
            [
                'section2',
                [
                    ['key3', 'value5\nvalue6'],
                ],
            ],
        ]
    """

    @staticmethod
    def dump_key_value(buffer, key, value, quote=None, linesep=None, equal_sep=''):
        if key == "__name__":
            return

        if quote is None:
            quote = ''
        else:
            quote = str(quote)

        if linesep:
            buffer.write(linesep)

        if value is None or value == '@':
            buffer.write(str(key).replace('\n', '\n\t'))
        else:
            buffer.write(str(key))
            buffer.write('{0}={0}'.format(equal_sep))
            buffer.write(quote)
            buffer.write(str(value).replace('\n', '\n\t'))
            buffer.write(quote)

    @staticmethod
    def _section_iter(section_data, key):
        if not isinstance(section_data, Iterable):
            section_data = []
        return (item for item in section_data if item[0] == key)

    @classmethod
    def section_del(cls, section, key):
        # make sure we are passed section not section_data
        assert isinstance(section[0], six.string_types)
        section_data = section[1]
        # mutate with slice assignment
        section_data[:] = [item for item in section_data if item[0] != key]

    @classmethod
    def section_get(cls, section, key, default=_LOCAL_DEFAULT):
        # make sure we are passed section not section_data
        assert isinstance(section[0], six.string_types)
        section_data = section[1]
        try:
            result = next(cls._section_iter(section_data, key), (None, default))[1]
        except IndexError:
            raise
        if result is _LOCAL_DEFAULT:
            raise KeyError(key)
        return result

    @classmethod
    def section_set_value(cls, section, key, val, indexes=None, set_all=False):
        # make sure we are passed section not section_data
        assert isinstance(section[0], six.string_types)
        section_data = section[1]
        if indexes is None:
            indexes = [0]
        else:
            indexes = validate_non_string_sequence(indexes, [indexes])
        for item_index, item in enumerate(cls._section_iter(section_data, key)):
            if set_all or item_index in indexes:
                item[1] = val

    @classmethod
    def update_section_data(cls, target_section, new_section_data):
        assert isinstance(target_section[0], six.string_types)
        target_section_data = target_section[1]

        target_indexes = {}
        for i, (key, _) in enumerate(target_section_data):
            target_indexes.setdefault(key, []).append(i)

        new_indexes = {}
        for i, (key, _) in enumerate(new_section_data):
            new_indexes.setdefault(key, []).append(i)

        for target_key, target_key_index_list in target_indexes.items():
            target_index_iter = iter(target_key_index_list)
            for new_key, new_value in new_section_data:
                if target_key == new_key:
                    try:
                        target_index = next(target_index_iter)
                    except StopIteration:
                        target_section_data.append([new_key, new_value])
                    else:
                        target_section_data[target_index][1] = new_value
        # append new keys
        for new_key, new_value in new_section_data:
            if new_key not in target_indexes:
                target_section_data.append([new_key, new_value])


    def __init__(self, filename=None, sections=None, linesep=os.linesep, section_sep=os.linesep,
                 equal_sep='', semi=';', pound='#'):
        super(YardstickConfigParser, self).__init__()
        self.filename = filename
        if sections is not None:
            self.sections = sections
        else:
            self.sections = []
        self.section_name = None
        self.section = None
        self.linesep = linesep
        self.section_sep = section_sep
        self.equal_sep = equal_sep
        self.semi = semi
        self.pound = pound

    def read(self, file_path):
        with open(file_path) as fh:
            return self.readfp(fh)

    def readfp(self, file_handle):
        return self._parse(file_handle)

    def write(self, file_handle):
        self.dump(file_handle)

    def parse(self, data=None):
        if not data:
            data = self.filename
        with open(data) as file_handle:
            return self._parse(file_handle)

    def load(self, file_path):
        self.read(file_path)

    def loads(self, data_string):
        self.readfp(StringIO(data_string))

    def dump(self, file_handle):
        """
        Write an .ini-format config string into the file handle

        PROX does not allow a space before/after the =, so we need
        a custom method
        """
        self._dump(file_handle)

    def dumps(self):
        """
        Generate an .ini-format config string

        PROX does not allow a space before/after the =, so we need
        a custom method
        """
        return self._dump(StringIO()).getvalue()

    def _dump(self, buffer):
        for section_name, section_data in self:
            buffer.write("[")
            buffer.write(str(section_name))
            buffer.write("]")
            for key, value in section_data:
                self.dump_key_value(buffer, key, value, linesep=self.linesep,
                                    equal_sep=self.equal_sep)
            buffer.write(self.linesep)
            buffer.write(self.section_sep)
        return buffer

    def __iter__(self):
        return iter(self.sections)

    def find_section_index(self, section_name):
        return next((i for i, (name, _) in enumerate(self) if name == section_name), -1)

    def find_section(self, section_name):
        return next((section for section in self if section[0] == section_name), None)

    def find_section_data(self, section_name):
        return next((value for name, value in self if name == section_name), None)

    def add_section(self, section_name):
        self.section = self.find_section(section_name)
        self.section_name = section_name
        if not self.section:
            self.section = [section_name, []]
            self.sections.append(self.section)

    def new_section(self, line_parser):
        self.add_section(line_parser.section_name)

    def get(self, section_name, key, default=_LOCAL_DEFAULT):
        value = default
        section = self.find_section(section_name)
        if section:
            value = next((v for k, v in section[1] if k == key), default)
        if value == _LOCAL_DEFAULT:
            raise KeyError('{}: {}'.format(section_name, key))
        return value

    def set(self, section_name, key, value):
        self.add_section(section_name)
        for key_value_pair in self.section[1]:
            if key_value_pair[0] == key:
                key_value_pair[1] = str(value)
                break
        else:
            self.section[1].append([key, str(value)])

    def append(self, section_name, key, value):
        self.add_section(section_name)
        for key_value_pair in self.section[1]:
            if key_value_pair[0] == key:
                key_value_pair[1] = '\n'.join([key_value_pair[1], str(value)])
                break
        else:
            self.section[1].append([key, str(value)])

    def _assignment(self, key, value, line_parser):
        if not self.section_name:
            raise line_parser.error_no_section_name()

        value = '\n'.join(value)
        entry = [key, value]
        self.section[1].append(entry)

    def comment(self, line_parser):
        """Called when a comment is parsed."""
        pass
