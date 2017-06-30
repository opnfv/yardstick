##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import unittest

from api.utils import common


class TranslateToStrTestCase(unittest.TestCase):

    def test_translate_to_str_unicode(self):
        input_str = u'hello'
        output_str = common.translate_to_str(input_str)

        result = 'hello'
        self.assertEqual(result, output_str)

    def test_translate_to_str_dict_list_unicode(self):
        input_str = {
            u'hello': {u'hello': [u'world']}
        }
        output_str = common.translate_to_str(input_str)

        result = {
            'hello': {'hello': ['world']}
        }
        self.assertEqual(result, output_str)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
