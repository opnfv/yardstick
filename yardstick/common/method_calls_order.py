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

import itertools
import functools
import logging
import weakref


LOG = logging.getLogger(__name__)



class MethodCallsOrderException(Exception):
    pass


class MethodCallsOrderExhaustedException(MethodCallsOrderException):

    def __init__(self, instance):
        message = "Exhausted instance {}.".format(instance)
        super(MethodCallsOrderExhaustedException, self).__init__(message)
        self.instance = instance


class MethodCallsOrderUnknownInstanceException(MethodCallsOrderException):

    def __init__(self, instance):
        message = "Unknown instance {}.".format(instance)
        super(MethodCallsOrderUnknownInstanceException, self).__init__(message)
        self.instance = instance


class MethodCallsOutOfOrderException(MethodCallsOrderException):

    def __init__(self, found, expected):
        message = 'Method {} called instead of {}!'.format(found, expected)
        super(MethodCallsOutOfOrderException, self).__init__(message)
        self.is_error = found != expected


class MethodCallsOrderManager(object):

    def __init__(self, *args, **kwargs):
        super(MethodCallsOrderManager, self).__init__()
        LOG.debug('setting call order')
        self._tracker_map = {}
        self._args = args
        self._kwargs = kwargs

    def __call__(self, *args, **kwargs):
        args_iter = iter(args)
        try:
            target_class = kwargs['target_class']
        except KeyError:
            target_class = next(args_iter, None)

        assert isinstance(target_class, type), 'Need target class'
        LOG.debug('decorating %s', target_class)
        target_class._METHOD_CALLS_ORDER_MANAGER = self
        call_order_list = getattr(target_class, 'METHOD_CALLS_ORDER_LIST', ())
        if not call_order_list:
            LOG.warning('METHOD_CALLS_ORDER_LIST not provided or empty for the %s class.',
                        target_class)
        for call_order, order_kwargs in call_order_list:
            LOG.debug('decorating %s', call_order)
            tracker = MethodCallsOrderTracker(target_class, *call_order, **order_kwargs)
            self._tracker_map[call_order] = tracker

        if '__init__' not in target_class.__dict__:
            def helper_init(self, *args, **kwargs):
                super(target_class, self).__init__(*args, **kwargs) # pylint: disable=bad-super-call
            target_class.__init__ = helper_init

        dunder_init = target_class.__init__

        @functools.wraps(dunder_init)
        def init_add_on(instance, *init_args, **init_kwargs):
            dunder_init(instance, *init_args, **init_kwargs)
            for init_tracker in self._tracker_map.values():
                init_tracker.add(instance)

        def enable(instance, order):
            self._tracker_map[order].enable(instance)

        def disable(instance, order=None):
            if order:
                self._tracker_map[order].disable(instance)
                return
            for tracker in self._tracker_map.values():
                try:
                    tracker.disable(instance)
                except KeyError:
                    pass

        target_class.__init__ = init_add_on
        target_class.enable_call_tracking = enable
        target_class.disable_call_tracking = disable
        return target_class


class MethodCallsOrderTracker(object):

    def __init__(self, target_class, *order, **kwargs):
        super(MethodCallsOrderTracker, self).__init__()
        self._enabled_instances = {}
        self._disabled_instances = {}
        self._failed_calls = {}
        self._repeatable = kwargs.get('repeatable')
        self._order = order
        for func in order:
            LOG.debug('setting %s of %s', func, target_class)
            setattr(target_class, func, self.wrap(getattr(target_class, func)))

    def enable(self, instance):
        weak_ref = weakref.ref(instance)
        self._enabled_instances[weak_ref] = self._disabled_instances.pop(weak_ref)

    def disable(self, instance):
        weak_ref = weakref.ref(instance)
        self._disabled_instances[weak_ref] = self._enabled_instances.pop(weak_ref)

    def add(self, instance):
        LOG.debug('registering %s %s', instance, self._order)
        order_iter = iter(self._order)

        if self.is_repeatable:
            # As a repeatable sequence, we need to cycle through the order
            order_iter = itertools.cycle(order_iter)

        self._enabled_instances[weakref.ref(instance)] = order_iter

    def clean(self, instance=None):
        if instance is None:
            self._enabled_instances.clear()
            self._disabled_instances.clear()
        else:
            weak_ref = weakref.ref(instance)
            self._enabled_instances.pop(weak_ref, None)
            self._disabled_instances.pop(weak_ref, None)

    @property
    def is_repeatable(self):
        return self._repeatable

    def wrap(self, target_func):
        @functools.wraps(target_func)
        def f(instance, *args, **kwargs):
            weak_ref = weakref.ref(instance)
            if weak_ref in self._disabled_instances:
                return target_func(instance, *args, **kwargs)

            expected_method_name = self._failed_calls.pop(weak_ref, None)

            if not expected_method_name:
                try:
                    order_iter = self._enabled_instances[weak_ref]
                    expected_method_name = next(order_iter)
                except KeyError:
                    raise MethodCallsOrderUnknownInstanceException(instance)
                except StopIteration:
                    raise MethodCallsOrderExhaustedException(instance)

            exception = MethodCallsOutOfOrderException(target_func.__name__, expected_method_name)
            if exception.is_error:
                # need to keep track of the method that was not called, in case
                # the exception is caught and additional calls are made
                self._failed_calls[weak_ref] = expected_method_name
                raise exception

            return target_func(instance, *args, **kwargs)

        return f
