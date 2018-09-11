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
from mock import Mock
from collections import OrderedDict

import resource_management_sdk.context as context
import resource_management_sdk.data as data


class TestContext(unittest.TestCase):

    def test_ResourceManagementContext_get_execution_result(self):
        inst, _client, _ctx, _instances_ctx = self._gen_resource_instance()
        _client.executions.get = Mock(return_value={'status': 'terminated'})
        _client.node_instances.get = Mock(
            return_value=_instances_ctx._node_instance)
        self.assertEqual(inst.get_execution_result(),
                         {'c': 'd', 'resource': 'b'})

    def test_ResourceManagementContext_run_execution(self):
        inst, _client, _ctx, _instances_ctx = self._gen_resource_instance()
        _execution_start_mock = Mock()
        _execution_start_mock.id = "1234"
        _client.executions.start = Mock(return_value=_execution_start_mock)
        _client.executions.get = Mock(return_value={'status': 'terminated'})
        _client.node_instances.get = Mock(
            return_value=_instances_ctx._node_instance)

        # check with wait for result
        self.assertEqual(inst.run_execution(), {'c': 'd', 'resource': 'b'})

        _client.executions.get.assert_called_with(execution_id='1234')
        _client.executions.start.assert_called_with(
            'deployment_id', 'execute_operation',
            allow_custom_parameters=True, force=True,
            parameters={
                'node_instance_ids': ['id'],
                'operation_kwargs': {},
                'allow_kwargs_override': True,
                'operation': 'list'})

        # check without waiting
        self.assertEqual(inst.run_execution(wait=False), "1234")

    def test_ResourceManagementContext_set_value(self):
        inst, _client, _ctx, _instances_ctx = self._gen_resource_instance()

        inst._collected_data = {data.ResourceKey(
            data.SCOPE_PROJECT, "system", "resource", "a"
        ): data.ResourceAvailability(10, 1)}

        # add new
        inst.set_value(quota=100, usage=50)
        new_value = inst._collected_data.get(data.ResourceKey(
            data.SCOPE_PROJECT, "system", "resource", "global"
        ))
        self.assertEqual(new_value.as_dict(), {
            'usage': 50.0, 'quota': 100.0, 'availability': 50.0})

        # update
        inst.set_value(quota=100, usage=80)
        new_value = inst._collected_data.get(data.ResourceKey(
            data.SCOPE_PROJECT, "system", "resource", "global"
        ))
        self.assertEqual(new_value.as_dict(), {
            'usage': 80.0, 'quota': 100.0, 'availability': 20.0})

    def test_ResourceManagementContext_collected_data(self):
        _ctx = Mock()
        _client = Mock()
        _ctx.node_instances = []
        inst = context.ResourceManagementContext(_ctx, _client)

        _ava = Mock()
        _ava.availability = None
        inst._collected_data = {data.ResourceKey(
            data.SCOPE_PROJECT, "system", "resource", "a"
        ): _ava}
        self.assertEqual(inst.collected_data, {})

        _ava.availability = 1.1
        self.assertEqual(inst.collected_data, {data.ResourceKey(
            data.SCOPE_PROJECT, "system", "resource", "a"
        ): _ava})

    def test_ResourceManagementContext_collected_data_dict(self):
        _ctx = Mock()
        _client = Mock()
        _ctx.node_instances = []
        inst = context.ResourceManagementContext(_ctx, _client)
        _ava = Mock()
        _ava.availability = 1.1
        _ava.as_dict = Mock(return_value={"a": "!"})
        inst._collected_data = {data.ResourceKey(
            data.SCOPE_PROJECT, "system", "resource", "a"
        ): _ava, data.ResourceKey(
            data.SCOPE_PROJECT, "system", "resource", "b"
        ): _ava, data.ResourceKey(
            data.SCOPE_PROJECT, "system", "other", "b"
        ): _ava, data.ResourceKey(
            data.SCOPE_GLOBAL, "system", "other"
        ): _ava}
        self.assertEqual(
            inst.collected_data_dict, {
                'a': {'system': {'resource': {'a': '!'}}},
                'global': {'system': {'other': {'a': '!'}}},
                'b': {'system': {
                    'other': {'a': '!'},
                    'resource': {'a': '!'}}}})

    def _gen_resource_instance(self):
        _instances_ctx = Mock()
        _instances_ctx.id = 'id'
        _instances_ctx._node_instance.deployment_id = 'deployment_id'
        _instances_ctx.node.type_hierarchy = ['cloudify.nodes.Root', 'a']
        _instances_ctx.node.properties = {'system_name': 'system',
                                          'resource_name': 'resource',
                                          'scope': 'scope',
                                          'runtime_property_name': "c"}
        _instances_ctx._node_instance.runtime_properties = {'resource': 'b',
                                                            'c': 'd'}
        _ctx = Mock()
        _client = Mock()
        _client.node_instances = Mock()
        _ctx.node_instances = [_instances_ctx]

        inst = context.ResourceManagementContext(_ctx, _client)
        return inst, _client, _ctx, _instances_ctx

    def test_ResourceManagementContext_init(self):
        inst, _client, _ctx, _instances_ctx = self._gen_resource_instance()

        self.assertEqual(inst.instance.id, 'id')
        self.assertEqual(inst.project, 'global')
        self.assertEqual(inst.result_instances, [])
        inst.add_result_instance_id()
        inst.add_result_instance_id('abc')
        self.assertEqual(inst.result_instances, ['id', 'abc'])
        self.assertEqual(inst.collected_data_raw, {})
        self.assertEqual(inst.dump(), {
            'availability': {},
            'instances': {
                'current': 1,
                'left': OrderedDict([('global', 0)]),
                'processed': ['id'],
                'to_be_processed': [],
                'total': 1}})
        inst.logger.info = Mock()
        inst.log('info', "message {}/{}", 'arg1', 'arg2')
        inst.logger.info.assert_called_with('[id] message arg1/arg2')
        inst.logger.info = Mock()
        inst.log_state()
        inst.logger.info.assert_called_with(
            '\n\nCurrent ResourceManagementContext state: \ncurrent_project: '
            'global \ninstances: \n-- TOTAL: 1 \n-- CURRENT: 1 \n-- LEFT: '
            'global=0 |  \ninstance: id\n')
        self.assertEqual(inst.next_instance(), None)
        self.assertEqual(inst.reset(), {
            'visited': True,
            'instance': inst.instance,
            'project': 'global'
        })

        # check get_resource_key
        self.assertEqual(
            inst.get_resource_key("abc"),
            data.ResourceKey(
                data.SCOPE_PROJECT, "system", "abc", "global"
            ))

        # check set_runtime_properties
        _client.node_instances.update = Mock()
        _client.node_instances.get = Mock(return_value={
            'version': 11,
            'runtime_properties': {'a': 'b'}
        })
        current_properties = {}
        inst.set_runtime_properties(current_properties, update=True)
        self.assertEqual(current_properties, {'a': 'b'})
        _client.node_instances.get.assert_called_with('id')
        _client.node_instances.update.assert_called_with(
            'id', runtime_properties={'a': 'b'}, version=11)

    def test_ResourceManagementContext_resolve_project(self):
        inst, _client, _ctx, _instances_ctx = self._gen_resource_instance()

        # no deployment
        self.assertFalse(inst.resolve_project())

        # have some deployment but without project
        inst.instance.properties[
            context.PROPERTY_DEPLOYMENT_ID
        ] = 'depl'
        self.assertFalse(inst.resolve_project())

        # we have some project
        inst.instance.properties[
            context.PROPERTY_PROJECT_NAME
        ] = 'proj'
        _cfy_instance = Mock()
        _cfy_node = Mock()
        _cfy_instance.id = 'id'
        _cfy_instance.deployment_id = 'deployment_id'
        _cfy_instance.node_id = 'node_id'
        _cfy_node.type_hierarchy = ['cloudify.nodes.Root', 'a']
        _cfy_node.properties = {'system_name': 'system',
                                'resource_name': 'resource',
                                'scope': 'scope',
                                'runtime_property_name': "c"}
        _cfy_instance.runtime_properties = {'resource': 'b',
                                            'c': 'd'}

        _client.node_instances.list = Mock(return_value=[_cfy_instance])
        _client.nodes.get = Mock(return_value=_cfy_node)
        self.assertTrue(inst.resolve_project())
        next_instance = inst.next_instance()
        self.assertEqual(next_instance['project'], 'proj')
        self.assertTrue(next_instance['visited'])


if __name__ == '__main__':
    unittest.main()
