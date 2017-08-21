##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# yardstick: this file is copied from rally and slightly modified
##############################################################################
from __future__ import absolute_import
import re
import jinja2
import jinja2.meta
import yaml


def finalize_for_yaml(elem):
    """Render Jinja2 output specifically for YAML files"""
    # Jinaj2 by default converts None to 'None', we can't allow this
    # we could convert to empty string '', or we can convert to null, aka ~
    if elem is None:
        return '~'
    # convert data structures to inline YAML
    # match builtin types because we shouldn't be trying to render complex types
    if isinstance(elem, (dict, list)):
        # remove newlines because we are injecting back into YAML
        # use block style for single line
        return yaml.safe_dump(elem, default_flow_style=True).replace('\n', '')
    return elem


class TaskTemplate(object):

    @classmethod
    def render(cls, task_template, **kwargs):
        """Render jinja2 task template to Yardstick input task.

        :param task_template: string that contains template
        :param kwargs: Dict with template arguments
        :returns:rendered template str
        """

        from six.moves import builtins

        ast = jinja2.Environment().parse(task_template)
        required_kwargs = jinja2.meta.find_undeclared_variables(ast)

        missing = set(required_kwargs) - set(kwargs) - set(dir(builtins))
        real_missing = [mis for mis in missing
                        if is_really_missing(mis, task_template)]

        if real_missing:
            multi_msg = ("Please specify next template task arguments:%s")
            single_msg = ("Please specify template task argument:%s")
            raise TypeError((len(real_missing) > 1 and multi_msg or single_msg)
                            % ", ".join(real_missing))
        return jinja2.Template(task_template, finalize=finalize_for_yaml).render(**kwargs)


def is_really_missing(mis, task_template):
    # Removing variables that have default values from
    # missing. Construction that won't be properly
    # check is {% set x = x or 1}
    if re.search(mis.join([r"{%\s*set\s+", "\s*=\s*", r"[^\w]+"]),
                 task_template):
        return False
    # Also check for a default filter which can show up as
    # a missing variable
    if re.search(mis + r"\s*\|\s*default\(", task_template):
        return False
    return True
