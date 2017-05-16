# Copyright (c) 2017 Intel Corporation
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
import mock


STL_MOCKS = {
    'trex_stl_lib': mock.MagicMock(),
    'trex_stl_lib.base64': mock.MagicMock(),
    'trex_stl_lib.binascii': mock.MagicMock(),
    'trex_stl_lib.collections': mock.MagicMock(),
    'trex_stl_lib.copy': mock.MagicMock(),
    'trex_stl_lib.datetime': mock.MagicMock(),
    'trex_stl_lib.functools': mock.MagicMock(),
    'trex_stl_lib.imp': mock.MagicMock(),
    'trex_stl_lib.inspect': mock.MagicMock(),
    'trex_stl_lib.json': mock.MagicMock(),
    'trex_stl_lib.linecache': mock.MagicMock(),
    'trex_stl_lib.math': mock.MagicMock(),
    'trex_stl_lib.os': mock.MagicMock(),
    'trex_stl_lib.platform': mock.MagicMock(),
    'trex_stl_lib.pprint': mock.MagicMock(),
    'trex_stl_lib.random': mock.MagicMock(),
    'trex_stl_lib.re': mock.MagicMock(),
    'trex_stl_lib.scapy': mock.MagicMock(),
    'trex_stl_lib.socket': mock.MagicMock(),
    'trex_stl_lib.string': mock.MagicMock(),
    'trex_stl_lib.struct': mock.MagicMock(),
    'trex_stl_lib.sys': mock.MagicMock(),
    'trex_stl_lib.threading': mock.MagicMock(),
    'trex_stl_lib.time': mock.MagicMock(),
    'trex_stl_lib.traceback': mock.MagicMock(),
    'trex_stl_lib.trex_stl_async_client': mock.MagicMock(),
    'trex_stl_lib.trex_stl_client': mock.MagicMock(),
    'trex_stl_lib.trex_stl_exceptions': mock.MagicMock(),
    'trex_stl_lib.trex_stl_ext': mock.MagicMock(),
    'trex_stl_lib.trex_stl_jsonrpc_client': mock.MagicMock(),
    'trex_stl_lib.trex_stl_packet_builder_interface': mock.MagicMock(),
    'trex_stl_lib.trex_stl_packet_builder_scapy': mock.MagicMock(),
    'trex_stl_lib.trex_stl_port': mock.MagicMock(),
    'trex_stl_lib.trex_stl_stats': mock.MagicMock(),
    'trex_stl_lib.trex_stl_streams': mock.MagicMock(),
    'trex_stl_lib.trex_stl_types': mock.MagicMock(),
    'trex_stl_lib.types': mock.MagicMock(),
    'trex_stl_lib.utils': mock.MagicMock(),
    'trex_stl_lib.utils.argparse': mock.MagicMock(),
    'trex_stl_lib.utils.collections': mock.MagicMock(),
    'trex_stl_lib.utils.common': mock.MagicMock(),
    'trex_stl_lib.utils.json': mock.MagicMock(),
    'trex_stl_lib.utils.os': mock.MagicMock(),
    'trex_stl_lib.utils.parsing_opts': mock.MagicMock(),
    'trex_stl_lib.utils.pwd': mock.MagicMock(),
    'trex_stl_lib.utils.random': mock.MagicMock(),
    'trex_stl_lib.utils.re': mock.MagicMock(),
    'trex_stl_lib.utils.string': mock.MagicMock(),
    'trex_stl_lib.utils.sys': mock.MagicMock(),
    'trex_stl_lib.utils.text_opts': mock.MagicMock(),
    'trex_stl_lib.utils.text_tables': mock.MagicMock(),
    'trex_stl_lib.utils.texttable': mock.MagicMock(),
    'trex_stl_lib.warnings': mock.MagicMock(),
    'trex_stl_lib.yaml': mock.MagicMock(),
    'trex_stl_lib.zlib': mock.MagicMock(),
    'trex_stl_lib.zmq': mock.MagicMock(),
}
