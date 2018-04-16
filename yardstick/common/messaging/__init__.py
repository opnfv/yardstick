# Copyright (c) 2018 Intel Corporation
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

# MQ is statically configured:
#   - MQ service: RabbitMQ
#   - user/password: yardstick/yardstick
#   - host:port: localhost:5672
MQ_USER = 'yardstick'
MQ_PASS = 'yardstick'
MQ_SERVICE = 'rabbit'
SERVER = 'localhost'
PORT = 5672
TRANSPORT_URL = (MQ_SERVICE + '://' + MQ_USER + ':' + MQ_PASS + '@' + SERVER +
                 ':' + str(PORT) + '/')

# RPC server.
RPC_SERVER_EXECUTOR = 'threading'

# Topics.
TOPIC_TG = 'topic_traffic_generator'

# Methods.
# Traffic generator consumers methods. Names must match the methods implemented
# in the consumer endpoint class, ``RunnerIterationIPCEndpoint``.
TG_METHOD_STARTED = 'tg_method_started'
TG_METHOD_FINISHED = 'tg_method_finished'
TG_METHOD_ITERATION = 'tg_method_iteration'
