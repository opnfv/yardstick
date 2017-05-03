# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
import logging
import os
import subprocess
import time
import posixpath

log = logging.getLogger(__name__)

SAMPLE_VNF_REPO = 'https://gerrit.opnfv.org/gerrit/samplevnf'
REPO_NAME = posixpath.basename(SAMPLE_VNF_REPO)
SAMPLE_REPO_DIR = os.path.join('~/', REPO_NAME)

LOG = logging.getLogger(__name__)


class OPNFVSampleVNF(object):

    def __init__(self, connection, bin_path):
        super(OPNFVSampleVNF, self).__init__()
        self.connection = connection
        self.bin_path = bin_path

    def deploy_vnfs(self, vnf_name):
        vnf_bin = os.path.join(self.bin_path, vnf_name)
        exit_status = self.connection.execute("which %s" % vnf_bin)[0]
        if exit_status:
            subprocess.check_output(["rm", "-rf", REPO_NAME])
            subprocess.check_output(["git", "clone", SAMPLE_VNF_REPO])
            time.sleep(2)
            self.connection.execute("rm -rf %s" % SAMPLE_REPO_DIR)
            self.connection.put(REPO_NAME, SAMPLE_REPO_DIR, True)

            build_script = os.path.join(SAMPLE_REPO_DIR, 'tools/vnf_build.sh')
            time.sleep(2)
            http_proxy = os.environ.get('http_proxy', '')
            https_proxy = os.environ.get('https_proxy', '')
            LOG.debug("sudo -E %s --silient '%s' '%s'" %
                      (build_script, http_proxy, https_proxy))
            self.connection.execute("sudo -E %s --silient '%s' '%s'" %
                                    (build_script, http_proxy,
                                     https_proxy))
            vnf_bin_loc = os.path.join(SAMPLE_REPO_DIR, "VNFs/%s/build/%s" %
                                       (vnf_name, vnf_name))
            self.connection.execute("mkdir -p %s" % (self.bin_path))
            self.connection.execute("cp %s %s" % (vnf_bin_loc, vnf_bin))
