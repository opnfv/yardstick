# Copyright 2017 Red Hat Inc & Xena Networks.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Contributors:
#   Dan Amzulescu, Xena Networks
#   Christian Trautman, Red Hat Inc.
#
# Usage can be seen below in unit test. This implementation is designed for one
# module two port Xena chassis runs only.

"""
Xena JSON module for mesh topology.
"""

from yardstick.traffic_generator.tools.pkt_gen.xena.json.xena_json import XenaJSON


class XenaJSONMesh(XenaJSON):
    """
    Class to modify and read Xena JSON configuration files. Topology will be set
    as Mesh.
    """
    def __init__(self):
        super(XenaJSONMesh, self).__init__()
        self.set_topology_mesh()

    def set_topology_mesh(self):
        """
        Set the test topology to Mesh for bi directional full duplex flow
        :return: None
        """
        self.json_data['TestOptions']['TopologyConfig']['Topology'] = 'MESH'
        self.json_data['TestOptions']['TopologyConfig']['Direction'] = 'BIDIR'
        self.json_data['PortHandler']['EntityList'][0]['PortGroup'] = "UNDEFINED"
        self.json_data['PortHandler']['EntityList'][1]['PortGroup'] = "UNDEFINED"
