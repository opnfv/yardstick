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


class BaseParser(object):

    PARSE_EXC = ParseError

    def __init__(self):
        super(BaseParser, self).__init__()
        self.line_no = 0

    def _assignment(self, key, value):
        self.assignment(key, value)
        return None, []

    def _get_section(self, line):
        if not line.endswith(']'):
            return self.error_no_section_end_bracket(line)
        if len(line) <= 2:
            return self.error_no_section_name(line)

        return line[1:-1]

    def _split_key_value(self, line):
        colon = line.find(':')
        equal = line.find('=')
        if colon < 0 and equal < 0:
            return self.error_invalid_assignment(line)

        if colon < 0 or (0 <= equal < colon):
            key, value = line[:equal], line[equal + 1:]
        else:
            key, value = line[:colon], line[colon + 1:]

        value = value.strip()
        if value and value[0] == value[-1] and value.startswith(("\"", "'")):
            value = value[1:-1]
        return key.strip(), [value]

    def parse(self, line_iter=None):
        if line_iter is None:
            return

        key = None
        value = []

        for line in line_iter:
            self.line_no += 1

            line = line.rstrip()
            lines = line.split(';')
            line = lines[0]
            if not line:
                # Blank line, ends multi-line values
                if key:
                    key, value = self._assignment(key, value)
                continue
            elif line.startswith((' ', '\t')):
                # Continuation of previous assignment
                if key is None:
                    self.error_unexpected_continuation(line)
                else:
                    value.append(line.lstrip())
                continue

            if key:
                # Flush previous assignment, if any
                key, value = self._assignment(key, value)

            if line.startswith('['):
                # Section start
                section = self._get_section(line)
                if section:
                    self.new_section(section)
            elif line.startswith(('#', ';')):
                self.comment(line[1:].lstrip())
            else:
                key, value = self._split_key_value(line)
                if not key:
                    return self.error_empty_key(line)

        if key:
            # Flush previous assignment, if any
            self._assignment(key, value)

    def assignment(self, key, value):
        """Called when a full assignment is parsed."""
        raise NotImplementedError()

    def new_section(self, section):
        """Called when a new section is started."""
        raise NotImplementedError()

    def comment(self, comment):
        """Called when a comment is parsed."""
        pass

    def error_invalid_assignment(self, line):
        raise self.PARSE_EXC("No ':' or '=' found in assignment",
                             self.line_no, line)

    def error_empty_key(self, line):
        raise self.PARSE_EXC('Key cannot be empty', self.line_no, line)

    def error_unexpected_continuation(self, line):
        raise self.PARSE_EXC('Unexpected continuation line',
                             self.line_no, line)

    def error_no_section_end_bracket(self, line):
        raise self.PARSE_EXC('Invalid section (must end with ])',
                             self.line_no, line)

    def error_no_section_name(self, line):
        raise self.PARSE_EXC('Empty section name', self.line_no, line)


class ConfigParser(BaseParser):
    """Parses a single config file, populating 'sections' to look like:

        {'DEFAULT': {'key': [value, ...], ...},
         ...}
    """

    def __init__(self, filename, sections):
        super(ConfigParser, self).__init__()
        self.filename = filename
        self.sections = sections
        self.section = None

    def parse(self, line_iter=None):
        with open(self.filename) as f:
            return super(ConfigParser, self).parse(f)

    def new_section(self, section):
        self.section = section
        self.sections.setdefault(self.section, [])

    def assignment(self, key, value):
        if not self.section:
            raise self.error_no_section()

        value = '\n'.join(value)

        def append(sections, section):
            entry = [key, value]
            sections[section].append(entry)

        append(self.sections, self.section)

    def error_no_section(self):
        return self.PARSE_EXC('Section must be started before assignment',
                              self.line_no, "")
