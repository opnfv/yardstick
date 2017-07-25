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

"""JSON utility module"""

import base64
import json
import locale
import logging
import uuid

_LOGGER = logging.getLogger(__name__)
_LOCALE = locale.getlocale()[1]

def create_segment(header_type, encode_64_string):
    """
    Create segment for JSON file
    :param header_type: Type of header as string
    :param encode_64_string: 64 byte encoded string value of the hex bytes
    :return: segment as dictionary
    """
    return {
        "SegmentType": header_type.upper(),
        "SegmentValue": encode_64_string,
        "ItemID": str(uuid.uuid4()),
        "ParentID": "",
        "Label": ""}


def decode_byte_array(enc_str):
    """ Decodes the base64-encoded string to a byte array
    :param enc_str: The base64-encoded string representing a byte array
    :return: The decoded byte array
    """
    dec_string = base64.b64decode(enc_str)
    barray = bytearray()
    barray.extend(dec_string)
    return barray


def encode_byte_array(byte_arr):
    """ Encodes the byte array as a base64-encoded string
    :param byte_arr: A bytearray containing the bytes to convert
    :return: A base64 encoded string
    """
    enc_string = base64.b64encode(bytes(byte_arr))
    return enc_string


def read_json_file(json_file):
    """
    Read the json file path and return a dictionary of the data
    :param json_file: path to json file
    :return: dictionary of json data
    """
    try:
        with open(json_file, 'r', encoding=_LOCALE) as data_file:
            file_data = json.loads(data_file.read())
    except ValueError as exc:
        # general json exception, Python 3.5 adds new exception type
        _LOGGER.exception("Exception with json read: %s", exc)
        raise
    except IOError as exc:
        _LOGGER.exception(
            'Exception during file open: %s file=%s', exc, json_file)
        raise
    return file_data


def write_json_file(json_data, output_path):
    """
    Write out the dictionary of data to a json file
    :param json_data: dictionary of json data
    :param output_path: file path to write output
    :return: Boolean if success
    """
    try:
        with open(output_path, 'w', encoding=_LOCALE) as fileh:
            json.dump(json_data, fileh, indent=2, sort_keys=True,
                      ensure_ascii=True)
        return True
    except ValueError as exc:
        # general json exception, Python 3.5 adds new exception type
        _LOGGER.exception(
            "Exception with json write: %s", exc)
        return False
    except IOError as exc:
        _LOGGER.exception(
            'Exception during file write: %s file=%s', exc, output_path)
        return False
