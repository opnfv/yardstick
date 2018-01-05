##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import logging
import requests
# require pillow package
from PIL import ImageFile

res = requests.get("http://localhost:8000/comparGraph?input=pod_name&output=bandwidth.MBps.&limit=10")

p = ImageFile.Parser()
p.feed(res._content)

im = p.close()
im.save("compareGraph.png")
