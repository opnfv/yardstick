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

    def __init__(self, line, line_no):
        super(LineParser, self).__init__()
        self.line = line
        self.line_no = line_no
        self.continuation = line != line.lstrip()
        semi_active, _, semi_comment = line.partition(';')
        pound_active, _, pound_comment = line.partition('#')
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

            value.append(line_parser.active.lstrip())
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

        parse_iter = (LineParser(line, line_no) for line_no, line in enumerate(line_iter))
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


class ConfigParser(BaseParser):
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

    def __init__(self, filename, sections=None):
        super(ConfigParser, self).__init__()
        self.filename = filename
        if sections is not None:
            self.sections = sections
        else:
            self.sections = []
        self.section_name = None
        self.section = None

    def parse(self, data=None):
        if not data:
            data = self.filename
        with open(data) as f:
            return self._parse(f)

    def __iter__(self):
        return iter(self.sections)

    def find_section_index(self, section_name):
        return next((i for i, (name, value) in enumerate(self) if name == section_name), -1)

    def find_section(self, section_name):
        return next((value for name, value in self.sections if name == section_name), None)

    def new_section(self, line_parser):
        section_name = line_parser.section_name
        index = self.find_section_index(section_name)
        self.section_name = section_name
        if index == -1:
            self.section = [section_name, []]
            self.sections.append(self.section)
        else:
            self.section = self.sections[index]

    def _assignment(self, key, value, line_parser):
        if not self.section_name:
            raise line_parser.error_no_section_name()

        value = '\n'.join(value)
        entry = [key, value]
        self.section[1].append(entry)

    def comment(self, line_parser):
        """Called when a comment is parsed."""
        pass
