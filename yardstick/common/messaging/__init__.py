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
TOPIC_RUNNER = 'topic_runner'

# Methods.
# Traffic generator consumers methods. Names must match the methods implemented
# in the consumer endpoint class.
TG_METHOD_STARTED = 'tg_method_started'
TG_METHOD_FINISHED = 'tg_method_finished'
TG_METHOD_ITERATION = 'tg_method_iteration'

# Runner consumers methods. Names must match the methods implemented in the
# consumer endpoint class.
RUNNER_METHOD_START_INJECTION = "runner_method_start_injection"
RUNNER_METHOD_STOP_INJECTION = "runner_method_stop_injection"
