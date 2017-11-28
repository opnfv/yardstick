# Copyright (c) 2016-2017 Intel Corporation
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

import mock
import unittest
import weakref

from yardstick.common import method_calls_order as mco


@mco.MethodCallsOrderManager()
class MyClass(object):

    METHOD_CALLS_ORDER_1 = 'func1', 'func2', 'func3'
    METHOD_CALLS_ORDER_2 = 'func4', 'func5', 'func6'

    METHOD_CALLS_ORDER_LIST = [
        (METHOD_CALLS_ORDER_1, {'repeatable': True}),
        (METHOD_CALLS_ORDER_2, {}),
    ]

    def func1(self):
        pass

    def func2(self):
        pass

    def func3(self):
        pass

    def func4(self):
        pass

    def func5(self):
        pass

    def func6(self):
        pass


class TestMethodCallsOrder(unittest.TestCase):


    def test_method_calls_order_sequences(self):
        instance = MyClass()
        # start sequence 1
        instance.func1()
        # start a sequence 2
        instance.func4()
        # continue sequence 2
        instance.func5()
        # continue sequence 1
        instance.func2()
        # retry middle of sequence 1
        with self.assertRaises(mco.MethodCallsOutOfOrderException):
            instance.func2()
        # retry start of sequence 1 again
        with self.assertRaises(mco.MethodCallsOutOfOrderException):
            instance.func1()
        # retry middle of sequence 1 again
        with self.assertRaises(mco.MethodCallsOutOfOrderException):
            instance.func2()
        # finish sequence 1
        instance.func3()
        # start a new cycle of sequence 1
        instance.func1()
        # finish sequence 2
        instance.func6()

        # try to restart sequence2, must fail since it's not repeatable
        with self.assertRaises(mco.MethodCallsOrderExhaustedException):
            instance.func4()

    def test_method_calls_order_disabled(self):
        instance = MyClass()
        instance.disable_call_tracking(instance.METHOD_CALLS_ORDER_2)
        # call out of order method while tracking disabled
        instance.func5()

    def test_method_calls_order_unknown_exception(self):
        instance = MyClass()
        tracker = instance._METHOD_CALLS_ORDER_MANAGER._tracker_map[MyClass.METHOD_CALLS_ORDER_1]
        tracker._enabled_instances = {}
        with self.assertRaises(mco.MethodCallsOrderUnknownInstanceException):
            instance.func1()

    @mock.patch('yardstick.common.method_calls_order.LOG.warning')
    def test_method_calls_order_missing_calls_order_list(self, mock_warning):

        # pylint: disable=unused-variable
        @mco.MethodCallsOrderManager()
        class IncorrectClass(object):
            # METHOD_CALLS_ORDER_LIST is missing
            def func1(self):
                pass

            def func2(self):
                pass

        mock_warning.assert_called()
        # pylint: enable=unused-variable

    def test_tracker_enable_disable_clean(self):

        class Dummy(object):
            def f1(self):
                pass
            def f2(self):
                pass

        dummy = Dummy()
        dummy2 = Dummy()
        weak_ref = weakref.ref(dummy)
        weak_ref2 = weakref.ref(dummy2)

        tracker = mco.MethodCallsOrderTracker(Dummy, 'f1', 'f2')
        tracker.add(dummy)
        tracker.add(dummy2)

        tracker.disable(dummy)
        self.assertNotIn(weak_ref, tracker._enabled_instances)
        self.assertIn(weak_ref, tracker._disabled_instances)

        tracker.enable(dummy)
        self.assertIn(weak_ref, tracker._enabled_instances)
        self.assertNotIn(weak_ref, tracker._disabled_instances)

        tracker.clean(dummy)
        self.assertNotIn(weak_ref, tracker._enabled_instances)
        self.assertNotIn(weak_ref, tracker._disabled_instances)
        self.assertIn(weak_ref2, tracker._enabled_instances)
        self.assertNotIn(weak_ref2, tracker._disabled_instances)

        tracker.clean()
        self.assertNotIn(weak_ref2, tracker._enabled_instances)
        self.assertNotIn(weak_ref2, tracker._disabled_instances)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
