# Copyright (c) 2018 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest
from mock import Mock, call

import resource_management_sdk.handle as handle


class TestHandle(unittest.TestCase):

    def test_Handler(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()

        check_handle = handle.Handler(mock_log)
        self.assertEqual(mock_log, check_handle.logger)
        self.assertFalse(check_handle.can_handle(_ctx))
        check_handle.handle(_ctx)
        _ctx.log.assert_not_called()

    def test_NoopHandler(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance.type = None

        check_handle = handle.NoopHandler(mock_log)
        self.assertEqual(mock_log, check_handle.logger)
        self.assertTrue(check_handle.can_handle(_ctx))
        check_handle.handle(_ctx)
        _ctx.log.assert_called_with(
            'info',
            'Node instance has type with is not supported by Resource '
            'Management Plugin. Skipping')

    def test_ProjectHandler(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance.type = handle.NODE_TYPE_PROJECT
        _ctx.resolve_project = Mock()

        check_handle = handle.ProjectHandler(mock_log)
        self.assertEqual(mock_log, check_handle.logger)
        self.assertTrue(check_handle.can_handle(_ctx))
        check_handle.handle(_ctx)
        _ctx.resolve_projectassert_called_with()
        _ctx.log.assert_called_with(
            'info', 'Processing of project started')

    def test_RuntimePropertyHandlerBase_set_value(self):
        _ctx = Mock()
        _ctx.set_value = Mock()

        handle._RuntimePropertyHandlerBase._set_value(_ctx, "a", "b", "c")
        _ctx.set_value.assert_called_with(b='a', resource_name='c')

        handle._RuntimePropertyHandlerBase._set_value(_ctx, "a", "b")
        _ctx.set_value.assert_called_with(b='a')

    def test_RuntimePropertyHandlerBase_process_runtime_properties(self):
        _ctx = Mock()
        _ctx.instance = Mock()
        _ctx.instance.resource_name = "resource_name"
        _ctx.instance.runtime_property_name = "runtime_property_name"

        _ctx.log = Mock()
        _ctx.set_value = Mock()
        instance = handle._RuntimePropertyHandlerBase(Mock())

        # fully empty structure, ignore at all
        instance._process_runtime_properties(_ctx, {}, "unknown")
        _ctx.log.assert_called_with('warn', 'Runtime property "{0}" not found'
                                            ' in runtime properties: {1}',
                                    'runtime_property_name', {})
        # number
        _ctx.log = Mock()
        _ctx.set_value = Mock()
        instance._process_runtime_properties(
            _ctx, {"runtime_property_name": 1}, "unknown")
        _ctx.set_value.assert_called_with(unknown=1)
        _ctx.log.assert_has_calls([
            call(
                'debug',
                'Found {0} numerical value defined in "{1}" runtime property'
                ' (for resource: {2})', 'unknown', 'runtime_property_name',
                'resource_name'),
            call('debug', 'Setting {}', {'unknown': 1})])

        # iterable
        _ctx.log = Mock()
        _ctx.set_value = Mock()
        instance._process_runtime_properties(
            _ctx, {"runtime_property_name": [1, 1]}, "unknown")
        _ctx.set_value.assert_called_with(unknown=2)
        _ctx.log.assert_has_calls([
            call(
                'debug',
                'Found {0} numerical value defined in "{1}" runtime property'
                ' (for resource: {2})', 'unknown', 'runtime_property_name',
                'resource_name'),
            call('debug', 'Setting {}', {'unknown': 2})])

        # dict of string
        # TODO: Recheck with _ctx.set_value
        _ctx.log = Mock()
        _ctx.set_value = Mock()
        instance._process_runtime_properties(
            _ctx, {"runtime_property_name": {'resource_name': None}},
            "unknown")
        _ctx.log.assert_has_calls([
            call(
                'debug',
                'Found {0} dict value defined in "{1}" runtime property - but '
                'resource name has been not specified. Trying to set values '
                'based of dict value keys', 'unknown',
                'runtime_property_name')])

        # dict of int
        _ctx.log = Mock()
        _ctx.set_value = Mock()
        instance._process_runtime_properties(
            _ctx, {"runtime_property_name": {'resource_name': 1}}, "unknown")
        _ctx.set_value.assert_called_with(unknown=1)
        _ctx.log.assert_has_calls([
            call(
                'debug',
                'Found {0} numerical value defined in "{1}" runtime property'
                ' (for resource: {2})', 'unknown',
                'runtime_property_name', 'resource_name'),
            call('debug', 'Setting {}', {'unknown': 1})])

        # fully different type
        _ctx.log = Mock()
        _ctx.set_value = Mock()
        other_type = Mock()
        instance._process_runtime_properties(
            _ctx, {"runtime_property_name": other_type}, "unknown")
        _ctx.log.assert_has_calls([
            call(
                'debug',
                'Not supported {1} type "{0}" of runtime property "{2}"',
                repr(other_type), 'unknown', 'runtime_property_name')])

    def test_SimpleQuotaHandler_can_handle(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance = Mock()
        _ctx.instance.type = None
        _ctx.instance.resource_name = "resource_name"
        _ctx.instance.runtime_property_name = "runtime_property_name"
        _ctx.instance.runtime_properties = {"runtime_property_name": 1}

        # unsupported
        check_handle = handle.SimpleQuotaHandler(mock_log)
        self.assertEqual(mock_log, check_handle.logger)
        self.assertFalse(check_handle.can_handle(_ctx))

        # supported
        _ctx.instance.type = handle.NODE_TYPE_QUOTA
        self.assertTrue(check_handle.can_handle(_ctx))
        check_handle.handle(_ctx)
        _ctx.set_value.assert_called_with(quota=1)
        _ctx.log.assert_has_calls([
            call(
                'debug',
                'Found {0} numerical value defined in "{1}" runtime property'
                ' (for resource: {2})', 'quota', 'runtime_property_name',
                'resource_name'),
            call('debug', 'Setting {}', {'quota': 1})])

    def test_SimpleUsageHandler_can_handle(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance = Mock()
        _ctx.instance.type = None
        _ctx.instance.resource_name = "resource_name"
        _ctx.instance.runtime_property_name = "runtime_property_name"
        _ctx.instance.runtime_properties = {}
        _ctx.run_execution = Mock(return_value={"runtime_property_name": 1})

        # unsupported
        check_handle = handle.SimpleUsageHandler(mock_log)
        self.assertEqual(mock_log, check_handle.logger)
        self.assertFalse(check_handle.can_handle(_ctx))

        # supported
        _ctx.instance.type = handle.NODE_TYPE_USAGE
        self.assertTrue(check_handle.can_handle(_ctx))
        check_handle.handle(_ctx)
        _ctx.set_value.assert_called_with(usage=1)
        _ctx.log.assert_has_calls([
            call('info', 'Executing "list" operation for get usage ...'),
            call('info', 'Got {} runtime_properties after execution',
                 ['runtime_property_name']),
            call(
                'debug',
                'Found {0} numerical value defined in "{1}" runtime property'
                ' (for resource: {2})', 'usage', 'runtime_property_name',
                'resource_name'),
            call('debug', 'Setting {}', {'usage': 1})])
        _ctx.run_execution.assert_called_with()

    def test_ExecutionResultUsageHandler_can_handle(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance = Mock()
        _ctx.instance.type = None
        _ctx.instance.resource_name = "resource_name"
        _ctx.instance.runtime_property_name = "runtime_property_name"
        _ctx.instance.runtime_properties = {}
        _ctx.get_execution_result = Mock(
            return_value={"runtime_property_name": 1})

        # unsupported
        check_handle = handle.ExecutionResultUsageHandler(mock_log)
        self.assertEqual(mock_log, check_handle.logger)
        self.assertFalse(check_handle.can_handle(_ctx))

        # supported
        _ctx.instance.type = handle.NODE_TYPE_USAGE
        self.assertTrue(check_handle.can_handle(_ctx))
        check_handle.handle(_ctx)
        _ctx.set_value.assert_called_with(usage=1)
        _ctx.log.assert_has_calls([
            call('info', 'Got {} runtime_properties after execution',
                 ['runtime_property_name']),
            call(
                'debug',
                'Found {0} numerical value defined in "{1}" runtime property'
                ' (for resource: {2})', 'usage', 'runtime_property_name',
                'resource_name'),
            call('debug', 'Setting {}', {'usage': 1})])
        _ctx.get_execution_result.assert_called_with()

    def test_ExecutionStartUsageHandler_can_handle(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance = Mock()
        _ctx.instance.type = None
        _ctx.instance.resource_name = "resource_name"
        _ctx.instance.runtime_property_name = "runtime_property_name"
        _ctx.instance.runtime_properties = {}
        _ctx.run_execution = Mock(return_value="abcdef")

        # unsupported
        check_handle = handle.ExecutionStartUsageHandler(mock_log)
        self.assertEqual(mock_log, check_handle.logger)
        self.assertFalse(check_handle.can_handle(_ctx))

        # supported
        _ctx.instance.type = handle.NODE_TYPE_USAGE
        self.assertTrue(check_handle.can_handle(_ctx))
        check_handle.handle(_ctx)
        _ctx.set_value.assert_not_called()
        _ctx.log.assert_has_calls([
            call('info',
                 'Starting executing for "list" operation for get usage ...'),
            call('info', 'Execution started with ID: abcdef ...')])
        _ctx.run_execution.assert_called_with(wait=False)

    def test_OpenstackQuotaHandler_suppress(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance.type = None

        instance = handle.OpenstackQuotaHandler(mock_log)
        self.assertTrue(instance._suppress('floating_ips'))
        self.assertFalse(instance._suppress('_not_'))

    def test_OpenstackQuotaHandler_translate(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance.type = None

        instance = handle.OpenstackQuotaHandler(mock_log)
        self.assertEqual(
            instance._translate('key_pairs'),
            'keypair')
        self.assertEqual(
            instance._translate('_pairs'),
            '_pairs')

    def test_OpenstackQuotaHandler_process_dict_value(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance.type = None
        _ctx.set_value = Mock()

        instance = handle.OpenstackQuotaHandler(mock_log)
        instance._process_dict_value(
            _ctx, "value_type", "runtime_property_name",
            {"cinder": {
                'floating_ips': 'ips',
                'security_groups': 'groups',
                'count': 1
            }})
        _ctx.log.assert_has_calls([
            call(
                'debug',
                'Found openstack quota dict value defined in "{1}" runtime '
                'property. Looking for quota for each of openstack '
                'components.', 'value_type', 'runtime_property_name'),
            call('debug', 'Found quota for: {0}', 'cinder')])
        _ctx.set_value.assert_called_with(resource_name='count', value_type=1)

    def test_OpenstackQuotaHandler_can_handle(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance = Mock()
        _ctx.instance.type = None
        _ctx.instance.resource_name = "resource_name"
        _ctx.instance.runtime_property_name = "runtime_property_name"
        _ctx.instance.runtime_properties = {}
        _ctx.run_execution = Mock(return_value={"runtime_property_name": 1})
        _ctx.instance.system_name = handle.SYSTEM_NAME_OPENSTACK

        # unsupported
        check_handle = handle.OpenstackQuotaHandler(mock_log)
        self.assertEqual(mock_log, check_handle.logger)
        self.assertFalse(check_handle.can_handle(_ctx))

        # supported
        _ctx.instance.type = handle.NODE_TYPE_QUOTA
        self.assertTrue(check_handle.can_handle(_ctx))

    def test_ResultHandler_can_handle(self):
        mock_log = Mock()
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.instance = Mock()
        _ctx.instance.id = "abc"
        _ctx.instance.type = None
        _ctx.instance.resource_name = "resource_name"
        _ctx.instance.runtime_property_name = "runtime_property_name"
        _ctx.instance.runtime_properties = {}
        _ctx.add_result_instance_id = Mock()
        _ctx.set_runtime_properties = Mock()
        _ctx.dump = Mock(return_value={"a": "b"})

        # unsupported
        check_handle = handle.ResultHandler(mock_log)
        self.assertEqual(mock_log, check_handle.logger)
        self.assertFalse(check_handle.can_handle(_ctx))

        # supported
        _ctx.instance.type = handle.NODE_TYPE_RESULT
        self.assertTrue(check_handle.can_handle(_ctx))
        check_handle.handle(_ctx)
        _ctx.set_value.assert_not_called()
        _ctx.log.assert_has_calls([
            call('info',
                 'Dumping gathered data to runtime_properties of {} node '
                 'instance', "abc")])
        _ctx.add_result_instance_id.assert_called_with()
        _ctx.dump.assert_called_with()
        _ctx.set_runtime_properties.assert_called_with({'data': {'a': 'b'}})

    def test_RuntimePropertyHandlerBase_process_process_number_value(self):
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.set_value = Mock()
        instance = handle._RuntimePropertyHandlerBase(Mock())

        # set some value
        instance._process_number_value(_ctx, "a", "b", 1, "d")
        _ctx.set_value.assert_called_with(a=1)
        _ctx.log.assert_has_calls([
            call(
                'debug', 'Found {0} numerical value defined in "{1}" runtime '
                'property (for resource: {2})', 'a', 'b', 'd'),
            call('debug', 'Setting {}', {'a': 1})])

    def test_RuntimePropertyHandlerBase_process_dict_value(self):
        _ctx = Mock()
        _ctx.log = Mock()
        _ctx.set_value = Mock()
        instance = handle._RuntimePropertyHandlerBase(Mock())

        # set some value
        instance._process_dict_value(_ctx, "a", "b", {"a": 1})
        _ctx.set_value.assert_called_with(a=1, resource_name='a')
        _ctx.log.assert_has_calls([
            call(
                'debug',
                'Found {0} dict value defined in "{1}" runtime property - but'
                ' resource name has been not specified. Trying to set values '
                'based of dict value keys', 'a', 'b'),
            call('debug', 'Setting {}',
                 {'a': 1, 'resource_name': 'a'})])

        # do nothing
        _ctx.set_value = Mock()
        _ctx.log = Mock()
        instance._process_dict_value(_ctx, "a", "b", {"a": "b"})
        _ctx.set_value.assert_not_called()
        _ctx.log.assert_has_calls([call(
            'debug',
            'Found {0} dict value defined in "{1}" runtime property - but'
            ' resource name has been not specified. Trying to set values '
            'based of dict value keys', 'a', 'b')])

    def test_RuntimePropertyHandlerBase_is_iterable(self):
        # correct iterable
        self.assertTrue(
            handle._RuntimePropertyHandlerBase._is_iterable([1, 2, 3]))
        self.assertTrue(
            handle._RuntimePropertyHandlerBase._is_iterable((1, 2, 3)))
        # not iterable
        self.assertFalse(
            handle._RuntimePropertyHandlerBase._is_iterable("a"))
        self.assertFalse(
            handle._RuntimePropertyHandlerBase._is_iterable(1))

    def test_RuntimePropertyHandlerBase_is_dict(self):
        # correct iterable
        self.assertTrue(
            handle._RuntimePropertyHandlerBase._is_dict({'a': 'b'}))
        self.assertTrue(
            handle._RuntimePropertyHandlerBase._is_dict({}))
        # not iterable
        self.assertFalse(
            handle._RuntimePropertyHandlerBase._is_dict("a"))
        self.assertFalse(
            handle._RuntimePropertyHandlerBase._is_dict(1))
        self.assertFalse(
            handle._RuntimePropertyHandlerBase._is_dict(True))
        self.assertFalse(
            handle._RuntimePropertyHandlerBase._is_dict(False))
        self.assertFalse(
            handle._RuntimePropertyHandlerBase._is_dict((1, 2)))
        self.assertFalse(
            handle._RuntimePropertyHandlerBase._is_dict([1, 2]))

    def test_RuntimePropertyHandlerBase_is_number(self):
        # correct number
        self.assertTrue(
            handle._RuntimePropertyHandlerBase._is_number(0.1))
        self.assertTrue(
            handle._RuntimePropertyHandlerBase._is_number(1))
        self.assertTrue(
            handle._RuntimePropertyHandlerBase._is_number("0.1"))
        self.assertTrue(
            handle._RuntimePropertyHandlerBase._is_number("0.2"))
        # not number
        self.assertFalse(
            handle._RuntimePropertyHandlerBase._is_number("a"))
        self.assertFalse(
            handle._RuntimePropertyHandlerBase._is_number("-"))


if __name__ == '__main__':
    unittest.main()
