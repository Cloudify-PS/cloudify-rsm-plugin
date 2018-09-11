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

import resource_management_sdk.instance as instance


class TestInstance(unittest.TestCase):

    def _check_instance(self, inst):
        self.assertEqual(inst.id, 'id')
        self.assertEqual(inst.deployment_id, 'deployment_id')
        self.assertEqual(inst.resource_name, 'resource')
        self.assertEqual(inst.runtime_property_name, 'c')
        self.assertEqual(inst.runtime_property_value, 'd')
        self.assertEqual(inst.scope, 'scope')
        self.assertEqual(inst.system_name, 'system')
        self.assertEqual(inst.type, 'a')
        self.assertEqual(inst.execution_id, None)
        self.assertEqual(inst.runtime_properties, {'resource': 'b',
                                                   'c': 'd'})
        self.assertEqual(inst.properties, {'resource_name': 'resource',
                                           'scope': 'scope',
                                           'runtime_property_name': 'c',
                                           'system_name': 'system'})

        inst.set_execution_id('123')
        self.assertEqual(inst.execution_id, '123')

    def test_Instance_empty(self):
        inst = instance.Instance('id', 'deployment_id',
                                 [],
                                 {},
                                 {})
        self.assertEqual(inst.id, 'id')
        self.assertEqual(inst.deployment_id, 'deployment_id')
        self.assertEqual(inst.resource_name, None)
        self.assertEqual(inst.runtime_property_name, None)
        self.assertEqual(inst.runtime_property_value, None)
        self.assertEqual(inst.scope, 'project')
        self.assertEqual(inst.system_name, None)
        self.assertEqual(inst.type, None)
        self.assertEqual(inst.execution_id, None)
        self.assertEqual(inst.runtime_properties, {})
        self.assertEqual(inst.properties, {})

        inst.set_execution_id('123')
        self.assertEqual(inst.execution_id, '123')

    def test_Instance_not_empty(self):
        inst = instance.Instance('id', 'deployment_id',
                                 ['cloudify.nodes.Root', 'a'],
                                 {'system_name': 'system',
                                  'resource_name': 'resource',
                                  'scope': 'scope',
                                  'runtime_property_name': "c"},
                                 {'resource': 'b',
                                  "c": "d"})
        self._check_instance(inst)

    def test_WorkflowCtxInstanceAdapter_not_empty(self):
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
        _ctx.node_instances = [_instances_ctx]

        inst = instance.WorkflowCtxInstanceAdapter.get_instances(_ctx)
        self.assertEqual(len(inst), 1)
        self._check_instance(inst[0])

    def test_RestClientInstanceAdapter_not_empty(self):
        _client = Mock()
        _client.node_instances = Mock()
        _client.nodes = Mock()
        _instance = Mock()
        _node = Mock()

        _client.node_instances.list = Mock(return_value=[_instance])
        _client.nodes.get = Mock(return_value=_node)

        _instance.id = 'id'
        _instance.deployment_id = 'deployment_id'
        _instance.node_id = 'node_id'
        _node.type_hierarchy = ['cloudify.nodes.Root', 'a']
        _node.properties = {'system_name': 'system',
                            'resource_name': 'resource',
                            'scope': 'scope',
                            'runtime_property_name': "c"}
        _instance.runtime_properties = {'resource': 'b',
                                        'c': 'd'}

        inst = instance.RestClientInstanceAdapter.get_instances(
            _client, 'deployment_id')
        # calls
        _client.nodes.get.assert_called_with(deployment_id='deployment_id',
                                             node_id='node_id')
        _client.node_instances.list.assert_called_with(
            deployment_id='deployment_id')

        # results
        self.assertEqual(len(inst), 1)
        self._check_instance(inst[0])

    def test_Instances_not_empty(self):
        _instances_ctx = Mock()
        _instances_ctx.logger = Mock()
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
        _ctx.node_instances = [_instances_ctx]

        inst = instance.Instances(
            _ctx.logger,
            instance.WorkflowCtxInstanceAdapter.get_instances(_ctx)
        )
        self._check_instance(inst.current_instance)
        self.assertEqual(inst.current_project, 'global')
        self.assertEqual(inst.dump(), {
            'to_be_processed': [],
            'current': 1,
            'processed': ['id'],
            'total': 1,
            'left': OrderedDict([('global', 0)])})
        self.assertEqual(
            inst.get_left_instances_info(),
            '\n-- TOTAL: 1 \n-- CURRENT: 1 \n-- LEFT: global=0 | ')

        # check left instances
        self.assertEqual(inst.left_instances, OrderedDict([('global', 0)]))

        # add new instances
        _fake_instance = Mock()
        inst.add_project('global', [_fake_instance])
        self.assertEqual(inst.left_instances, OrderedDict([('global', 1)]))
        self.assertEqual(inst.next_instance(), {
            'project': 'global',
            'instance': _fake_instance,
            'visited': True})
        self.assertEqual(inst.next_instance(), None)
        # go little back
        inst._position = 0
        self.assertEqual(inst.next_instance(), None)

    def test_Instances_empty(self):
        _ctx = Mock()
        _ctx.node_instances = []

        inst = instance.Instances(
            _ctx.logger,
            []
        )
        with self.assertRaises(RuntimeError):
            inst.current_instance


if __name__ == '__main__':
    unittest.main()
