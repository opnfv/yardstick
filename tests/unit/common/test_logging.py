##############################################################################
# Copyright (c) 2016 Huawei Technologies Co., Ltd. and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.common.yardstick_logging

import unittest

from yardstick.common import yardstick_logging

class Yardstick_LoggingTestCase(unittest.TestCase):

    def test_yardstick_logging_success(self):

        LOG = yardstick_logging.getLogger("hello")
        LOG.info("LOG runs well")
        LOG.debug("THIS is it right!!!")
        self.assertIsNotNone(LOG)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
